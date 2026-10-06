import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import psycopg
from openai import APITimeoutError, OpenAI, RateLimitError
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field, TypeAdapter, ValidationError, field_validator

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000"))
DAILY_GENERATION_LIMIT = max(1, int(os.getenv("DAILY_GENERATION_LIMIT", "3")))
DUPLICATE_EMAIL_MESSAGE = "Email linked to existing account. Please try a different email."

# scrypt cost parameters (OWASP-recommended range). Stored inside each hash so they can be tuned later.
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SESSION_DURATION = timedelta(days=15)
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)
LOGIN_RATE_LIMIT = 10
LOGIN_RATE_LIMIT_WINDOW = timedelta(minutes=15)
INVALID_CREDENTIALS_MESSAGE = "Incorrect Email or Password. Please try again"

# The process-local limit is a useful baseline for the deployed serverless app.
# Use a shared store such as Redis if the app is scaled to multiple instances.
generation_counts: dict[str, tuple[str, int]] = {}
generation_counts_lock = Lock()

app = FastAPI(title="Learning Path LLM API", version="0.2.0")

# Defaults cover Vite's local dev server; add the deployed frontend's origin(s)
# via the ALLOWED_ORIGINS env var (comma-separated) instead of editing this list.
DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173,http://localhost:5174"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

Provider = Literal["openai", "gemini"]


class UserInputRequest(BaseModel):
    career_goal: str = Field(min_length=1)
    current_skill_level: Literal["beginner", "intermediate", "advanced"]
    working_industry: str = Field(min_length=1)
    past_experience: str = Field(min_length=1)
    available_time: int = Field(ge=1, le=168)
    provider: Provider = Field(
        default="openai",
        description="The LLM provider to use to generate the learning path.",
    )

    @field_validator("career_goal", "past_experience")
    @classmethod
    def require_description(cls, value: str) -> str:
        value = value.strip()
        if not any(character.isalpha() for character in value):
            raise ValueError("Please enter a description containing letters.")
        return value


class LearningPathStep(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    estimated_time: str = Field(min_length=1)


LearningPathSteps = TypeAdapter(list[LearningPathStep])


class UserInputResponse(BaseModel):
    message: str
    data: UserInputRequest
    learning_path: list[LearningPathStep]
    provider: Provider
    model: str


class PromptRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        max_length=10_000,
        description="The user's prompt for the language model.",
    )
    provider: Provider = Field(
        default="openai",
        description="The LLM provider to use: openai or gemini.",
    )


class GenerateResponse(BaseModel):
    response: str
    response_id: str
    model: str
    provider: Provider


class LLMResponse(BaseModel):
    """Provider-neutral response used by both output endpoints."""

    text: str
    response_id: str
    model: str
    provider: Provider


@app.get("/health")
def health_check():
    return {"status": "ok", "providers": ["openai", "gemini"]}


def _client_identifier(request: Request) -> str:
    """Return Vercel's trusted client IP, with a safe local-development fallback."""
    vercel_forwarded_for = request.headers.get("x-vercel-forwarded-for")
    if vercel_forwarded_for:
        return vercel_forwarded_for
    return request.client.host if request.client else "unknown"


def enforce_daily_generation_limit(request: Request) -> None:
    """Allow a client to generate at most DAILY_GENERATION_LIMIT plans per UTC day."""
    client_id = _client_identifier(request)
    today = datetime.now(timezone.utc).date().isoformat()

    with generation_counts_lock:
        recorded_day, count = generation_counts.get(client_id, (today, 0))
        if recorded_day != today:
            count = 0

        if count >= DAILY_GENERATION_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Daily generation limit reached ({DAILY_GENERATION_LIMIT}). "
                    "Please try again tomorrow."
                ),
            )

        generation_counts[client_id] = (today, count + 1)


def build_learning_path_prompt(request: UserInputRequest) -> str:
    """Turn a user's assessment answers into a prompt for the LLM."""
    return (
        "Create a personalized 6-month learning path for someone with the "
        "following profile:\n"
        f"- Career goal: {request.career_goal}\n"
        f"- Current skill level: {request.current_skill_level}\n"
        f"- Working industry: {request.working_industry}\n"
        f"- Past experience: {request.past_experience}\n"
        f"- Available time per week: {request.available_time} hours\n\n"
        "The plan must cover a total duration of approximately 6 months, "
        "broken into sequential learning steps whose estimated_time values "
        "add up to roughly 6 months. Respond with ONLY a JSON array (no "
        "markdown, no surrounding text) of learning path steps. Each element "
        "must be an object with exactly these string fields: \"title\", "
        "\"description\" (1-2 sentences), and \"estimated_time\" (e.g. "
        "\"3 weeks\"). Example:\n"
        '[{"title": "...", "description": "...", "estimated_time": "3 weeks"}]'
    )


def parse_learning_path(text: str) -> list[LearningPathStep]:
    """Validate and parse the AI's raw text into structured learning path steps."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    if not text:
        raise HTTPException(status_code=502, detail="The AI returned an empty response.")

    try:
        raw_steps = json.loads(text)
    except json.JSONDecodeError as error:
        logger.exception("AI response was not valid JSON")
        raise HTTPException(
            status_code=502, detail="The AI returned a malformed response."
        ) from error

    try:
        steps = LearningPathSteps.validate_python(raw_steps)
    except ValidationError as error:
        logger.exception("AI response did not match the expected learning path shape")
        raise HTTPException(
            status_code=502, detail="The AI returned a malformed response."
        ) from error

    if not steps:
        raise HTTPException(status_code=502, detail="The AI returned an empty response.")

    return steps


@app.post("/user-input", response_model=UserInputResponse)
def user_input(request: UserInputRequest, http_request: Request):
    enforce_daily_generation_limit(http_request)
    prompt = build_learning_path_prompt(request)
    response = create_llm_response(prompt, request.provider)
    learning_path = parse_learning_path(response.text)

    return UserInputResponse(
        message="User input received successfully",
        data=request,
        learning_path=learning_path,
        provider=response.provider,
        model=response.model,
    )


def _openai_response(prompt: str) -> LLMResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    start = time.perf_counter()
    try:
        response = OpenAI(api_key=api_key, timeout=60).responses.create(
            model=model,
            input=prompt,
            store=False,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            reasoning={"effort": "low"},
        )
    except RateLimitError as error:
        logger.exception("OpenAI request was rate limited")
        raise HTTPException(
            status_code=429, detail="The OpenAI service is rate-limited. Please try again shortly."
        ) from error
    except APITimeoutError as error:
        logger.exception("OpenAI request timed out")
        raise HTTPException(
            status_code=504, detail="The OpenAI service timed out."
        ) from error
    except Exception as error:
        logger.exception("OpenAI request failed")
        raise HTTPException(
            status_code=502, detail="The OpenAI service is temporarily unavailable."
        ) from error

    logger.info(
        "OpenAI response in %.2fs, usage=%s",
        time.perf_counter() - start,
        response.usage,
    )

    if response.status == "incomplete":
        raise HTTPException(
            status_code=502,
            detail=f"The OpenAI response was incomplete: {response.incomplete_details.reason}",
        )

    return LLMResponse(
        text=response.output_text,
        response_id=response.id,
        model=model,
        provider="openai",
    )


def _gemini_response(prompt: str) -> LLMResponse:
    """Call Gemini's generateContent REST API without adding an SDK dependency."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    body = json.dumps(
        {
            "model": model,
            "input": prompt,
            "store": False,
            "generation_config": {
                "thinking_level": "minimal",
                "max_output_tokens": MAX_OUTPUT_TOKENS,
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url="https://generativelanguage.googleapis.com/v1beta/interactions",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    start = time.perf_counter()
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as api_response:
                payload = json.loads(api_response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as error:
            if error.code in (429, 503) and attempt < max_attempts:
                logger.warning("Gemini request got HTTP %s, retrying once", error.code)
                time.sleep(1)
                continue
            logger.exception("Gemini request failed")
            if error.code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="The Gemini service is rate-limited. Please try again shortly.",
                ) from error
            raise HTTPException(
                status_code=502, detail="The Gemini service is temporarily unavailable."
            ) from error
        except TimeoutError as error:
            logger.exception("Gemini request timed out")
            raise HTTPException(
                status_code=504, detail="The Gemini service timed out."
            ) from error
        except urllib.error.URLError as error:
            logger.exception("Gemini request failed")
            if isinstance(error.reason, TimeoutError):
                raise HTTPException(
                    status_code=504, detail="The Gemini service timed out."
                ) from error
            raise HTTPException(
                status_code=502, detail="The Gemini service is temporarily unavailable."
            ) from error
        except json.JSONDecodeError as error:
            logger.exception("Gemini request failed")
            raise HTTPException(
                status_code=502, detail="The Gemini service is temporarily unavailable."
            ) from error

    logger.info(
        "Gemini response in %.2fs, usage=%s",
        time.perf_counter() - start,
        payload.get("usage"),
    )

    if payload.get("status") == "incomplete":
        raise HTTPException(
            status_code=502,
            detail="The Gemini response was incomplete; try a shorter profile or increase LLM_MAX_OUTPUT_TOKENS.",
        )

    try:
        text = payload["steps"][-1]["content"][0]["text"]
    except (KeyError, IndexError) as error:
        logger.exception("Unexpected Gemini response shape")
        raise HTTPException(
            status_code=502, detail="The Gemini service is temporarily unavailable."
        ) from error

    return LLMResponse(
        text=text,
        response_id=f"gemini-{uuid4()}",
        model=model,
        provider="gemini",
    )


def create_llm_response(prompt: str, provider: Provider = "openai") -> LLMResponse:
    """Create one response from the selected provider."""
    if provider == "gemini":
        return _gemini_response(prompt)
    return _openai_response(prompt)


@app.post("/generate", response_model=GenerateResponse)
def generate(request: PromptRequest, http_request: Request):
    """Send one user prompt to the LLM and return structured JSON."""
    enforce_daily_generation_limit(http_request)
    response = create_llm_response(request.prompt, request.provider)

    return GenerateResponse(
        response=response.text,
        response_id=response.response_id,
        model=response.model,
        provider=response.provider,
    )


@app.post("/generate/text", response_class=PlainTextResponse)
def generate_text(request: PromptRequest, http_request: Request):
    """Send one user prompt to the LLM and return readable plain text."""
    enforce_daily_generation_limit(http_request)
    return create_llm_response(request.prompt, request.provider).text


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def require_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name cannot be blank.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    """Public user data. Never include password or password_hash here."""

    id: int
    full_name: str
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class SessionResponse(BaseModel):
    user: UserResponse
    session_token: str
    expires_at: datetime


def get_db_connection() -> psycopg.Connection:
    """Open a connection to PostgreSQL (Supabase Transaction Pooler) for one request.

    prepare_threshold=None disables server-side prepared statements, which the
    transaction pooler does not support. The schema lives in migrations/, not here.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    return psycopg.connect(database_url, connect_timeout=5, prepare_threshold=None)


def hash_password(password: str) -> str:
    """Hash a password with scrypt and a random per-password salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=64,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a scrypt hash without leaking comparison timing."""
    try:
        algorithm, n, r, p, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != "scrypt":
            return False
        computed_digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(digest_hex)),
        )
        return hmac.compare_digest(computed_digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


# Verify absent users against a valid hash to reduce account-enumeration timing differences.
DUMMY_PASSWORD_HASH = hash_password("not-a-real-password")


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def enforce_auth_rate_limit(
    connection: psycopg.Connection, request: Request, scope: str
) -> None:
    """Limit authentication attempts per client and action across serverless instances."""
    client_hash = hashlib.sha256(f"{scope}:{_client_identifier(request)}".encode("utf-8")).hexdigest()
    row = connection.execute(
        "INSERT INTO login_rate_limits (client_hash, window_started_at, attempt_count) "
        "VALUES (%s, now(), 1) "
        "ON CONFLICT (client_hash) DO UPDATE SET "
        "window_started_at = CASE WHEN login_rate_limits.window_started_at <= now() - %s "
        "THEN now() ELSE login_rate_limits.window_started_at END, "
        "attempt_count = CASE WHEN login_rate_limits.window_started_at <= now() - %s "
        "THEN 1 ELSE login_rate_limits.attempt_count + 1 END "
        "RETURNING attempt_count",
        (client_hash, LOGIN_RATE_LIMIT_WINDOW, LOGIN_RATE_LIMIT_WINDOW),
    ).fetchone()
    if row[0] > LOGIN_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")


def clear_successful_auth_attempt(
    connection: psycopg.Connection, request: Request, scope: str
) -> None:
    """Do not penalize a client for a successful authentication."""
    client_hash = hashlib.sha256(f"{scope}:{_client_identifier(request)}".encode("utf-8")).hexdigest()
    connection.execute(
        "UPDATE login_rate_limits SET attempt_count = GREATEST(attempt_count - 1, 0) "
        "WHERE client_hash = %s",
        (client_hash,),
    )


def require_session(authorization: str | None = Header(default=None)) -> UserResponse:
    """Resolve an active bearer token to its user, rejecting expired or revoked sessions."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")

    token_hash = hash_session_token(authorization.removeprefix("Bearer ").strip())
    try:
        connection = get_db_connection()
        try:
            row = connection.execute(
                "SELECT u.id, u.full_name, u.email FROM user_sessions s "
                "JOIN users u ON u.id = s.user_id "
                "WHERE s.token_hash = %s AND s.revoked_at IS NULL AND s.expires_at > now()",
                (token_hash,),
            ).fetchone()
        finally:
            connection.close()
    except (psycopg.Error, RuntimeError) as error:
        logger.exception("Database error while validating session")
        raise HTTPException(status_code=500, detail="Could not validate the session.") from error

    if not row:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return UserResponse(id=row[0], full_name=row[1], email=row[2])


def create_user(request: RegisterRequest) -> UserResponse:
    """Insert a new user. The UNIQUE constraint on email makes duplicates race-safe."""
    password_hash = hash_password(request.password)

    try:
        connection = get_db_connection()
        try:
            with connection:
                row = connection.execute(
                    "INSERT INTO users (full_name, email, password_hash) "
                    "VALUES (%s, %s, %s) RETURNING id",
                    (request.full_name, request.email, password_hash),
                ).fetchone()
        finally:
            connection.close()
    except psycopg.errors.UniqueViolation as error:
        raise HTTPException(status_code=409, detail=DUPLICATE_EMAIL_MESSAGE) from error
    except (psycopg.Error, RuntimeError) as error:
        logger.exception("Database error while creating user")
        raise HTTPException(
            status_code=500, detail="Could not create the account. Please try again later."
        ) from error

    return UserResponse(
        id=row[0],
        full_name=request.full_name,
        email=request.email,
    )


@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, http_request: Request):
    try:
        connection = get_db_connection()
        try:
            with connection:
                enforce_auth_rate_limit(connection, http_request, "register")
        finally:
            connection.close()
    except HTTPException:
        raise
    except (psycopg.Error, RuntimeError) as error:
        logger.exception("Database error while rate limiting registration")
        raise HTTPException(status_code=500, detail="Could not create the account. Please try again later.") from error
    return create_user(request)


@app.post("/auth/login", response_model=SessionResponse)
def login(request: LoginRequest, http_request: Request):
    """Authenticate a user and issue a revocable 15-day bearer session."""
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    expires_at = now + SESSION_DURATION
    login_error: HTTPException | None = None
    authenticated_user: UserResponse | None = None

    try:
        connection = get_db_connection()
        try:
            with connection:
                enforce_auth_rate_limit(connection, http_request, "login")
                row = connection.execute(
                    "SELECT id, full_name, email, password_hash, failed_login_attempts, locked_until "
                    "FROM users WHERE email = %s FOR UPDATE",
                    (request.email,),
                ).fetchone()

                if not row:
                    verify_password(request.password, DUMMY_PASSWORD_HASH)
                    login_error = HTTPException(status_code=401, detail=INVALID_CREDENTIALS_MESSAGE)
                else:
                    user_id, full_name, email, password_hash, failed_attempts, locked_until = row
                    if locked_until and locked_until > now:
                        verify_password(request.password, DUMMY_PASSWORD_HASH)
                        login_error = HTTPException(status_code=401, detail=INVALID_CREDENTIALS_MESSAGE)
                    else:
                        if locked_until:
                            failed_attempts = 0
                            connection.execute(
                                "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = %s",
                                (user_id,),
                            )
                        if not verify_password(request.password, password_hash):
                            failed_attempts += 1
                            if failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                                connection.execute(
                                    "UPDATE users SET failed_login_attempts = %s, locked_until = %s WHERE id = %s",
                                    (failed_attempts, now + LOCKOUT_DURATION, user_id),
                                )
                            else:
                                connection.execute(
                                    "UPDATE users SET failed_login_attempts = %s WHERE id = %s",
                                    (failed_attempts, user_id),
                                )
                            login_error = HTTPException(status_code=401, detail=INVALID_CREDENTIALS_MESSAGE)
                        else:
                            connection.execute(
                                "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = %s",
                                (user_id,),
                            )
                        connection.execute(
                            "INSERT INTO user_sessions (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                            (user_id, hash_session_token(token), expires_at),
                        )
                        clear_successful_auth_attempt(connection, http_request, "login")
                        authenticated_user = UserResponse(id=user_id, full_name=full_name, email=email)
                connection.execute(
                    "DELETE FROM user_sessions WHERE expires_at <= now() OR "
                    "(revoked_at IS NOT NULL AND revoked_at < now() - %s)",
                    (SESSION_DURATION,),
                )
                connection.execute(
                    "DELETE FROM login_rate_limits WHERE window_started_at < now() - %s",
                    (timedelta(days=1),),
                )
        finally:
            connection.close()
    except (psycopg.Error, RuntimeError) as error:
        logger.exception("Database error while logging in")
        raise HTTPException(status_code=500, detail="Could not log in. Please try again later.") from error

    if login_error:
        raise login_error
    if not authenticated_user:
        raise HTTPException(status_code=500, detail="Could not log in. Please try again later.")
    return SessionResponse(user=authenticated_user, session_token=token, expires_at=expires_at)


@app.get("/auth/me", response_model=UserResponse)
def current_user(user: UserResponse = Depends(require_session)):
    return user


@app.post("/auth/logout", status_code=204)
def logout(authorization: str | None = Header(default=None)):
    """Revoke the current bearer session. Logging out twice is safe."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        connection = get_db_connection()
        try:
            with connection:
                connection.execute(
                    "UPDATE user_sessions SET revoked_at = now() "
                    "WHERE token_hash = %s AND revoked_at IS NULL",
                    (hash_session_token(authorization.removeprefix("Bearer ").strip()),),
                )
        finally:
            connection.close()
    except (psycopg.Error, RuntimeError) as error:
        logger.exception("Database error while logging out")
        raise HTTPException(status_code=500, detail="Could not log out. Please try again later.") from error


@app.post("/auth/logout-all", status_code=204)
def logout_all(user: UserResponse = Depends(require_session)):
    """Revoke every active session for the authenticated user."""
    try:
        connection = get_db_connection()
        try:
            with connection:
                connection.execute(
                    "UPDATE user_sessions SET revoked_at = now() WHERE user_id = %s AND revoked_at IS NULL",
                    (user.id,),
                )
        finally:
            connection.close()
    except (psycopg.Error, RuntimeError) as error:
        logger.exception("Database error while revoking all sessions")
        raise HTTPException(status_code=500, detail="Could not log out. Please try again later.") from error


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Keep FastAPI's 422 format, but drop the echoed "input" for /auth/register.

    Validation errors echo the submitted value, which would return the password.
    Every other route keeps FastAPI's default handler, so /user-input is unchanged.
    """
    if request.url.path not in {"/auth/register", "/auth/login"}:
        return await request_validation_exception_handler(request, exc)

    errors = [
        {key: value for key, value in error.items() if key != "input"}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))

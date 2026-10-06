import hashlib
import json
import logging
import os
import secrets
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
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
    allow_headers=["Content-Type"],
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
    """Return the originating client IP provided by the hosting proxy."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
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
def register(request: RegisterRequest):
    return create_user(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Keep FastAPI's 422 format, but drop the echoed "input" for /auth/register.

    Validation errors echo the submitted value, which would return the password.
    Every other route keeps FastAPI's default handler, so /user-input is unchanged.
    """
    if request.url.path != "/auth/register":
        return await request_validation_exception_handler(request, exc)

    errors = [
        {key: value for key, value in error.items() if key != "input"}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))

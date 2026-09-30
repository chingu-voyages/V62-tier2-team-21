import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from openai import APITimeoutError, OpenAI, RateLimitError
from dotenv import load_dotenv
from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000"))

app = FastAPI(title="Learning Path LLM API", version="0.2.0")

# Vite's local development server. Change or remove this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
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
def user_input(request: UserInputRequest):
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
def generate(request: PromptRequest):
    """Send one user prompt to the LLM and return structured JSON."""
    response = create_llm_response(request.prompt, request.provider)

    return GenerateResponse(
        response=response.text,
        response_id=response.response_id,
        model=response.model,
        provider=response.provider,
    )


@app.post("/generate/text", response_class=PlainTextResponse)
def generate_text(request: PromptRequest):
    """Send one user prompt to the LLM and return readable plain text."""
    return create_llm_response(request.prompt, request.provider).text

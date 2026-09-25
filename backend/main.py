import json
import os
import urllib.error
import urllib.request
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

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


@app.post("/user-input")
def user_input(request: UserInputRequest):
    return {"message": "User input received successfully", "data": request}


def _openai_response(prompt: str) -> LLMResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    try:
        response = OpenAI(api_key=api_key).responses.create(
            model=model,
            input=prompt,
            store=False,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502, detail="The OpenAI service is temporarily unavailable."
        ) from error

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

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    body = json.dumps({"model": model, "input": prompt}).encode("utf-8")
    request = urllib.request.Request(
        url="https://generativelanguage.googleapis.com/v1beta/interactions",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as api_response:
            payload = json.loads(api_response.read().decode("utf-8"))
        text = payload["steps"][-1]["content"][0]["text"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError) as error:
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

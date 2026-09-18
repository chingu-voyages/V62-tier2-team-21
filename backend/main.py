"""API endpoints for generating learning-path content with an LLM provider."""

import json
import os
import urllib.error
import urllib.request
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Learning Path LLM API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

Provider = Literal["openai", "gemini"]


class PromptRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        max_length=10000,
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

    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    request = urllib.request.Request(
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as api_response:
            payload = json.loads(api_response.read().decode("utf-8"))
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=502, detail="The Gemini service is temporarily unavailable."
        ) from error

    return LLMResponse(
        text=text,
        # generateContent does not return a response ID; create a request-safe ID.
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
    """Send one prompt to the selected provider and return structured JSON."""
    response = create_llm_response(request.prompt, request.provider)
    return GenerateResponse(
        response=response.text,
        response_id=response.response_id,
        model=response.model,
        provider=response.provider,
    )


@app.post("/generate/text", response_class=PlainTextResponse)
def generate_text(request: PromptRequest):
    """Send one prompt to the selected provider and return readable plain text."""
    return create_llm_response(request.prompt, request.provider).text

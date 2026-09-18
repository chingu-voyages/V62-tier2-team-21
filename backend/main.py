import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Learning Path LLM API", version="0.1.0")

# Vite's local development server. Change or remove this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class PromptRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        max_length=10_000,
        description="The user's prompt for the language model.",
    )


class GenerateResponse(BaseModel):
    response: str
    response_id: str
    model: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


def create_llm_response(prompt: str):
    """Create one LLM response while keeping provider errors private."""
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
        # Do not expose provider or configuration details to the client.
        raise HTTPException(status_code=502, detail="The language model is temporarily unavailable.") from error

    return response, model


@app.post("/generate", response_model=GenerateResponse)
def generate(request: PromptRequest):
    """Send one user prompt to the LLM and return structured JSON."""
    response, model = create_llm_response(request.prompt)

    return {
        "response": response.output_text,
        "response_id": response.id,
        "model": model,
    }


@app.post("/generate/text", response_class=PlainTextResponse)
def generate_text(request: PromptRequest):
    """Send one user prompt to the LLM and return readable plain text."""
    response, _ = create_llm_response(request.prompt)
    return response.output_text

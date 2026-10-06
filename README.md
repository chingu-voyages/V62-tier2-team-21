# Learning Path to Career

## Overview

Learning Path to Career is an AI-powered web application that turns career goals into personalized, step-by-step learning plans.

Based on the user's career goal, current skill level, professional background, and weekly study time, the application generates a learning path covering approximately six months. Users can follow the steps and track their progress as they learn.

## Screenshots

Screenshots will be added soon.

## Features

- **Career and skill assessment:** Enter a career goal, current skill level, working industry, past experience, and weekly study time to personalize the learning path.
- **AI-powered learning plans:** Generate a learning path tailored to the user's goals and background.
- **Step-by-step guidance:** View an ordered list of learning steps, each with a title, description, and estimated completion time.
- **Progress tracking:** Mark steps as complete using checkboxes and view an updating completed-steps counter.
- **Generate a new path:** Return to the assessment form and submit different information to generate a new learning path.
- **Input validation and feedback:** Required fields, text input limits, and study-time limits help users provide valid information. Loading and error messages provide feedback during path generation.

## Tech Stack

| Area                  | Technologies                         |
| --------------------- | ------------------------------------ |
| Frontend              | React, JavaScript, React Router, CSS |
| Frontend tooling      | Vite, npm, ESLint                    |
| Icons                 | Bootstrap Icons                      |
| Backend               | Python, FastAPI, Pydantic, Uvicorn   |
| AI integration        | OpenAI API, Gemini API               |
| Backend configuration | python-dotenv                        |

## How It Works

1. Open the home page and proceed to the career and skill assessment form.
2. Enter your career goal, current skill level, working industry, past experience, and available study hours per week.
3. Submit the form. The frontend validates the input and sends it to the backend through `POST /user-input`.
4. The backend builds a prompt from your answers, requests an AI-generated learning plan, and returns structured learning steps.
5. Review the generated path on the results page and use the checkboxes to mark completed steps. The completed-steps counter updates as you change the checkboxes.

To create another learning path, return to the form and submit a new assessment.

## Project Structure

| Directory   | Contents                                                               |
| ----------- | ---------------------------------------------------------------------- |
| `frontend/` | React application, page components, styles, and frontend configuration |
| `backend/`  | FastAPI application, AI integration, and backend configuration         |
| `docs/`     | Team planning documents, meeting materials, and screenshots            |

## Frontend Development

### Prerequisites

- Node.js 22.x, version 22.13.0 or later, or Node.js 24 or later
- npm
- A running backend with a valid AI API key for learning-path generation

### Run locally

Clone the repository if you do not already have a local copy:

```bash
git clone https://github.com/chingu-voyages/V62-tier2-team-21.git
cd V62-tier2-team-21
```

Start the backend using the instructions in [MVP API](#mvp-api).

In a separate terminal, run:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

## MVP API

The first version accepts a single user `prompt`, sends it to the OpenAI Responses API, and returns the model's text response. User accounts, conversation history, a database, and streaming are out of scope for this phase.

### Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Replace OPENAI_API_KEY in .env with your own API key
uvicorn main:app --reload --port 8000
```

API documentation: `http://localhost:8000/docs`

### Endpoints

`GET /health` checks that the API is running.

`POST /generate` generates a response for one prompt:

```json
{
  "prompt": "Create a beginner learning plan for becoming a software developer."
}
```

`POST /generate/text` accepts the same request body but returns only the LLM text as `text/plain`. It is useful for quick manual tests in Postman, where line breaks appear directly in the response body.

Successful response:

```json
{
  "response": "...",
  "response_id": "resp_...",
  "model": "gpt-5.6-luna"
}
```

You can change the model with the `OPENAI_MODEL` environment variable. The API key must remain only in the backend `.env` file and must never be added to the frontend or Git.

## Our Team

- Terence Lui: [GitHub](https://github.com/lwhterence) / [LinkedIn](https://www.linkedin.com/in/terence-lui-7ab78a4/)
- Han [GitHub](https://github.com/hnkcodes)
- Eman: [GitHub](https://github.com/emannaji597) / [LinkedIn](https://www.linkedin.com/in/eman-naji-485203311/)
- Ahmet: [GitHub](https://www.linkedin.com/in/ahmet-sagdasli) / [LinkedIn](https://github.com/ahmetsagdasli)
- Zaina Alahmar: [GitHub](https://github.com/ZainaAlahmar) / [LinkedIn](https://www.linkedin.com/in/zaina-alahmar)
- Chimdindu Nwobodo: [GitHub](https://github.com/chimdisandra) /[LinkedIn](https://www.linkedin.com/in/chimdindu-nwobodo-ba0a75316)

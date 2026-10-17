# Learning Path to Career

## Overview

Learning Path to Career is an AI-powered web application that turns career goals into personalized, step-by-step learning plans.

Based on the user's career goal, current skill level, professional background, and weekly study time, the application generates a learning path covering approximately six months. Users can follow the steps and track their progress as they learn.

## Screenshots

### Home Page

![Home Page](docs/screenshots/HomePage.png)

### Login Page

![Login Page](docs/screenshots/LoginPage.png)

### Career & Skill Assessment Form

![Assessment Form](docs/screenshots/FormPage.png)

### Loading Screen

![Loading Screen](docs/screenshots/LoadingPage.png)

### Generated Learning Path

![Generated Learning Path](docs/screenshots/ResultPage.png)

### Saved Learning Paths & Progress Tracking

![Saved Learning Paths](docs/screenshots/SavedLearningPath.png)

## Features

- **Career and skill assessment:** Enter a career goal, current skill level, working industry, past experience, and weekly study time to personalize the learning path.
- **Loading state and animations:** Display a time-based progress bar and rotating cog animations while the AI generates a learning path, providing visual feedback during the loading process.
- **AI-powered learning plans:** Generate personalized learning paths using OpenAI or Gemini.
- **Step-by-step guidance:** View an ordered list of learning steps, each with a title, description, and estimated completion time.
- **User authentication:** Create an account, log in, and securely access saved learning paths.
- **Save learning paths:** Save an entire generated learning path to your account.
- **Manage saved paths:** View, rename, and delete saved learning paths.
- **Progress tracking:** Mark individual steps as completed using checkboxes on the Saved Learning Paths page and view an updated completion counter.
- **Generate a new path:** Return to the assessment form and submit different information to generate another learning path.
- **Input validation and feedback:** Required fields, text input limits, and study-time limits help users provide valid information. Loading and error messages provide feedback during path generation and saving.

## Tech Stack

| Area                  | Technologies                       |
| --------------------- | ---------------------------------- |
| Frontend              | React, JavaScript                  |
| Routing               | React Router                       |
| Styling & Icons       | CSS, Bootstrap Icons               |
| Frontend Tooling      | Vite, npm, ESLint                  |
| Backend               | Python, FastAPI, Pydantic, Uvicorn |
| AI integration        | OpenAI API, Gemini API             |
| Backend configuration | python-dotenv                      |

## How It Works

1. Open the home page and proceed to the career and skill assessment form.
2. Enter your career goal, current skill level, working industry, past experience, and available study hours per week.
3. Submit the form. The frontend validates the input and sends it to the backend through `POST /user-input`.
4. The backend generates a personalized learning path using the selected AI provider and returns structured learning steps.
5. Review the generated learning path on the Results page.
6. Create an account or log in to save the entire learning path.
7. Open the Saved Learning Paths page to view and manage saved paths.
8. Expand a saved path to view its steps and use checkboxes to mark completed steps. The completion counter updates after each successful progress update.

Users can also rename or delete an entire saved learning path.

To create another learning path, return to the assessment form and submit a new assessment.

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

Start the backend using the instructions in [Backend API](#backend-api).

In a separate terminal, run:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

## Backend API

The FastAPI backend generates structured learning paths with OpenAI or Gemini. It also provides PostgreSQL-backed user accounts, bearer-token sessions, and saved learning-path management. Interactive API documentation, including every request and response schema, is available at `http://localhost:8000/docs` while the server is running.

### Architecture

```mermaid
flowchart LR
    user[User] --> frontend[React frontend]
    frontend -->|Generate a path\nPOST /user-input| api[FastAPI backend]
    api -->|Prompt and structured response| llm[OpenAI or Gemini]
    llm --> api
    frontend -->|Register, log in, save or update a path\nBearer token where required| api
    api -->|Users, sessions, saved paths, and steps| database[(PostgreSQL / Supabase)]
```

The frontend never connects to the database or AI providers directly. The backend validates requests, enforces generation and authentication limits, calls the selected provider, and stores account-related data.

### Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set the required values described below.
uvicorn main:app --reload --port 8000
```

Keep API keys and database credentials in `backend/.env`; never commit them or expose them in the frontend. The default development URL is `http://localhost:8000`.

### Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | When using OpenAI | API key for the OpenAI provider. |
| `OPENAI_MODEL` | No | OpenAI model name; defaults to `gpt-5.6-luna`. |
| `GEMINI_API_KEY` | When using Gemini | API key for the Gemini provider. |
| `GEMINI_MODEL` | No | Gemini model name; the code default is `gemini-3.6-flash`. The provided `.env.example` explicitly selects `gemini-3.8-flash`. |
| `DATABASE_URL` | For accounts and saved paths | PostgreSQL connection URL. Use the Supabase Transaction Pooler URL with `sslmode=require` in production. |
| `ALLOWED_ORIGINS` | No | Comma-separated frontend origins allowed by CORS. Local Vite origins are the default. |
| `DAILY_GENERATION_LIMIT` | No | Maximum learning-path generations per client IP per UTC day; defaults to `3`. |
| `LLM_MAX_OUTPUT_TOKENS` | No | Maximum tokens requested from the selected provider; defaults to `2000`. |
| `TEST_DATABASE_URL` | For integration tests | Disposable local PostgreSQL database used only by the test suite. It must never be the production `DATABASE_URL`. |

### Database setup

Create a PostgreSQL database (or Supabase project), set `DATABASE_URL` in `backend/.env`, then apply the migrations in order from the `backend/` directory. The commands require PostgreSQL's `psql` CLI:

```bash
set -a
source .env
set +a

for migration in migrations/*.sql; do
  psql "$DATABASE_URL" -f "$migration"
done
```

The migrations create the `users`, `user_sessions`, `login_rate_limits`, `saved_learning_paths`, and `saved_learning_path_items` tables. Apply each migration once to a new or appropriately versioned database. The backend connects directly to PostgreSQL; it does not use Supabase's public REST API.

### Main endpoints

| Endpoint | Description |
| --- | --- |
| `GET /health` | Checks API health and lists the supported AI providers. |
| `POST /user-input` | Generates a structured learning path from career goal, skill level, industry, experience, weekly study time, and selected provider (`openai` or `gemini`). |
| `POST /auth/register` | Creates a user account. |
| `POST /auth/login` | Authenticates a user and returns a bearer session token. |
| `GET /auth/me` | Returns the current user. |
| `POST /auth/logout` / `POST /auth/logout-all` | Revokes the current session or all sessions. |
| `POST /learning-path/save` | Saves a generated learning path for the authenticated user. |
| `GET /learning-path/saved` | Lists the authenticated user's saved learning paths. |
| `PATCH` / `DELETE /learning-path/saved/{saved_path_id}` | Renames or deletes a saved learning path. |
| `PATCH` / `DELETE /learning-path/saved/{saved_path_id}/items/{item_id}` | Updates a step's completion state or deletes that step. |
| `DELETE /auth/account` | Permanently deletes the authenticated user's account and its data. |

`POST /user-input` accepts the following shape and returns structured steps in `learning_path`:

```json
{
  "career_goal": "Frontend developer",
  "current_skill_level": "beginner",
  "working_industry": "Retail",
  "past_experience": "I have built a few small HTML and CSS projects.",
  "available_time": 8,
  "provider": "openai"
}
```

Authentication and saved-path routes require the token returned by `POST /auth/login`:

```http
Authorization: Bearer <session_token>
```

The older `POST /generate` and `POST /generate/text` endpoints remain available for simple prompt-based generation and manual testing. Use `/docs` for their full schemas and example responses.

### Tests

Install the development dependencies and point `TEST_DATABASE_URL` to a disposable local PostgreSQL database:

```bash
cd backend
pip install -r requirements-dev.txt
export TEST_DATABASE_URL="postgresql://USER:PASSWORD@localhost:5432/learning_path_test"
pytest
```

The test suite runs every migration against the test database and truncates its tables between tests. Never set `TEST_DATABASE_URL` to the production database.

## Our Team

- Terence Lui: [GitHub](https://github.com/lwhterence) / [LinkedIn](https://www.linkedin.com/in/terence-lui-7ab78a4/)
- Han [GitHub](https://github.com/hnkcodes)
- Ahmet: [GitHub](https://github.com/ahmetsagdasli) / [LinkedIn](https://www.linkedin.com/in/ahmet-sagdasli)
- Chimdindu Nwobodo: [GitHub](https://github.com/chimdisandra) /[LinkedIn](https://www.linkedin.com/in/chimdindu-nwobodo-ba0a75316)
- Tee Femiola: [GitHub](https://github.com/teefemiola-pixel) / [LinkedIn](https://www.linkedin.com/in/tusa-femiola/)

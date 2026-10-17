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

The FastAPI backend generates structured learning paths with OpenAI or Gemini. It also provides database-backed user accounts, bearer-token sessions, and saved learning-path management. Interactive API documentation is available at `http://localhost:8000/docs` while the server is running.

### Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set OPENAI_API_KEY and/or GEMINI_API_KEY, then configure DATABASE_URL for PostgreSQL.
uvicorn main:app --reload --port 8000
```

Keep API keys and database credentials in `backend/.env`; never commit them or expose them in the frontend.

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

The older `POST /generate` and `POST /generate/text` endpoints remain available for simple prompt-based generation and manual testing. Routes that access account or saved-path data require `Authorization: Bearer <token>`.

## Our Team

- Terence Lui: [GitHub](https://github.com/lwhterence) / [LinkedIn](https://www.linkedin.com/in/terence-lui-7ab78a4/)
- Han [GitHub](https://github.com/hnkcodes)
- Ahmet: [GitHub](https://github.com/ahmetsagdasli) / [LinkedIn](https://www.linkedin.com/in/ahmet-sagdasli)
- Chimdindu Nwobodo: [GitHub](https://github.com/chimdisandra) /[LinkedIn](https://www.linkedin.com/in/chimdindu-nwobodo-ba0a75316)
- Tee Femiola: [GitHub](https://github.com/teefemiola-pixel) / [LinkedIn](https://www.linkedin.com/in/tusa-femiola/)

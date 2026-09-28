# Learning Path to Career

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

---

Your project's `readme` is as important to success as your code. For 
this reason you should put as much care into its creation and maintenance
as you would any other component of the application.

If you are unsure of what should go into the `readme` let this article,
written by an experienced Chingu, be your starting point - 
[Keys to a well written README](https://tinyurl.com/yk3wubft).

And before we go there's "one more thing"! Once you decide what to include
in your `readme` feel free to replace the text we've provided here.

> Own it & Make it your Own!

## Team Documents

You may find these helpful as you work together to organize your project.

- [Team Project Ideas](./docs/team_project_ideas.md)
- [Team Decision Log](./docs/team_decision_log.md)

Meeting Agenda templates (located in the `/docs` directory in this repo):

- Meeting - Voyage Kickoff --> ./docs/meeting-voyage_kickoff.docx
- Meeting - App Vision & Feature Planning --> ./docs/meeting-vision_and_feature_planning.docx
- Meeting - Sprint Retrospective, Review, and Planning --> ./docs/meeting-sprint_retrospective_review_and_planning.docx
- Meeting - Sprint Open Topic Session --> ./docs/meeting-sprint_open_topic_session.docx

## Our Team

Everyone on your team should add their name along with a link to their GitHub
& optionally their LinkedIn profiles below. Do this in Sprint #1 to validate
your repo access and to practice PR'ing with your team *before* you start
coding!

- Terence Lui: (https://github.com/lwhterence) / (https://www.linkedin.com/in/terence-lui-7ab78a4/)
- Han (https://github.com/hnkcodes) 
- Teammate name #3: [GitHub](https://github.com/emannaji597) / [LinkedIn](https://www.linkedin.com/in/eman-naji-485203311/)
- Teammate name #2: (https://www.linkedin.com/in/ahmet-sagdasli) ---(https://github.com/ahmetsagdasli)
   ...
- Teammate name #n: [GitHub](https://github.com/ghaccountname) / [LinkedIn](https://linkedin.com/in/liaccountname)
- Zaina Alahmar: [GitHub](https://github.com/ZainaAlahmar) / [LinkedIn](https://www.linkedin.com/in/zaina-alahmar)
- Sakshi: [GitHub](https://github.com/sakship2204) / [LinkedIn](https://www.linkedin.com/in/sakshi-pandita-88b4741b0/)
- Chimdindu Nwobodo: <a href="https://github.com/chimdisandra"> Github</a> / <a href="https://www.linkedin.com/in/chimdindu-nwobodo-ba0a75316">Linkedin</a>
  

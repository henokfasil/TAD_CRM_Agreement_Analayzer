# Deployment

`docker compose up --build` starts PostgreSQL, Redis, the FastAPI API, and the Streamlit app.

The public prototype is deployed on Streamlit Community Cloud from `main`. Production secrets are
stored only in Streamlit Secrets. Required hosted settings include Neon PostgreSQL, Neon Object
Storage and, when enabled, the external model provider.

For Gemini agreement analysis:

```toml
ALLOW_EXTERNAL_LLM = "true"
GEMINI_API_KEY = "..."
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-3.8-flash"
```

The key must be valid and the Google AI Studio project must have available credits. If Gemini is
unavailable, the deployed app saves a labelled local evidence scan instead of losing the workflow.

After deployment, smoke-test these routes in order: Upload agreements, Analyse agreements, Review
findings, Compare agreements and Presentation. Never paste or commit secret values into source.


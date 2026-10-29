# CRM Agreement Studio — Agent Guide

## Product objective

Build a persistent, evidence-centred research engine for comparative mapping of critical raw
materials agreements. The target is not merely PDF search: uploaded agreements become a validated,
reusable corpus capable of producing comparisons, figures, methods and research reports.

## User-facing workflow

Keep the primary Streamlit journey simple and connected:

1. **Upload agreements** — persist the original PDF, extract native text and run OCR when needed.
2. **Analyse agreements** — answer the nine registered research questions with page-level evidence.
3. **Review findings** — a researcher checks evidence, edits the answer and records a rationale.
4. **Compare and report** — use human-approved profiles for comparative outputs.

Detailed page review, codebook variables, provision coding and verification remain advanced audit
controls. They must not obstruct the primary journey.

## Research safeguards

- AI and local evidence scans are provisional; humans approve final findings.
- Never publish a positive claim without a quotation verified against extracted page text.
- Preserve document checksum, extraction/OCR provenance, provider, model and prompt version.
- Official comparisons and reports should use approved profiles by default.
- Show corpus cutoff, denominator, missing-data treatment and codebook/specification versions.
- The original paper is a quality benchmark. Generate new results from the live corpus; do not copy
  its fixed figures.

## Current architecture

- **UI:** Streamlit Community Cloud.
- **Records:** Neon PostgreSQL.
- **Original PDFs:** private Neon Object Storage.
- **Extraction:** PyMuPDF with Tesseract OCR fallback.
- **Analysis:** Gemini through a provider adapter, with a conservative local evidence scan when the
  external provider is unavailable.
- **Validation/services:** Pydantic, YAML, Psycopg, Boto3, SQLAlchemy and Alembic.

The supported Gemini model is `gemini-3.8-flash`. Retired model aliases are resolved to this model.
External Gemini generation also requires valid project credits; otherwise the app must explain the
provider error safely and retain the local fallback.

## Security and repository discipline

- Never commit API keys, database credentials or storage credentials.
- Use `.env.local` locally and Streamlit Secrets in deployment.
- Preserve unrelated working-tree changes and stage only files belonging to the current task.
- Sanitize provider errors so credentials cannot appear in UI or logs.

## Verification

Run `python -m pytest -q` before deployment. The current baseline is 44 passing tests. For a release,
also smoke-test Upload, Analyse, Review, Compare and the embedded Presentation on the live URL.

## Near-term roadmap

1. Validate the nine-question answer sheet on a benchmark set with double coding.
2. Register deterministic indicators and reusable charts over approved profiles.
3. Generate complete reports with methods, limitations and evidence manifests.
4. Later, add a governed agent that monitors official sources for new CRM agreements, prepares
   candidate records and sends email notifications; researchers must approve corpus inclusion.

# Architecture

The Studio separates Streamlit pages, research services, provider adapters, schemas and durable
persistence. Streamlit pages should remain thin orchestration and presentation layers.

## Runtime layers

1. **Interface** — Streamlit provides Upload, Analyse, Review, Compare, dashboards and presentation.
2. **Document services** — originals are fingerprinted and retained in Neon Object Storage;
   PyMuPDF and Tesseract produce page-level text and extraction provenance.
3. **Research services** — the nine-question analysis service generates structured provisional
   answers and validates every returned quotation against extracted pages.
4. **Model adapters** — Gemini (`gemini-3.8-flash`) and OpenAI-compatible providers share typed
   request/response contracts. A conservative local evidence scan preserves functionality when an
   external provider is unavailable.
5. **Persistence** — Neon PostgreSQL stores documents, pages, analyses, decisions and provenance;
   SQLite remains available for isolated local tests.
6. **Publication** — approved profiles feed comparisons today and registered indicators, figures
   and complete reports in the next stage.

Human review is the publication boundary: provisional model or local-scan output cannot silently
become a final research conclusion.


# CRM Agreement Research Engine Blueprint

## Purpose

The Studio is being organised as a research-production engine. Agreement PDFs are processed
once, converted into evidence-linked structured records, and then reused to generate updated
comparative analysis and complete research reports as the corpus grows.

The reference paper defines the expected quality and breadth of the final output. Its published
figures are benchmarks, not static templates to copy. Future tables, figures, prose and methods
must be calculated from the live corpus under a versioned analytical contract.

## Production layers

1. **Source layer** — original PDF, source URL, checksum, extraction method and OCR provenance.
2. **Evidence layer** — page text and candidate passages with stable page-level citations.
3. **Research layer** — agreement metadata, participants, legal form and coded provisions.
4. **Validation layer** — reviewer decisions, adjudication rationale and validation status.
5. **Analysis layer** — deterministic indicators defined in the analysis registry.
6. **Publication layer** — figures, tables, narrative, methods, limitations and evidence manifest.

## Publication contract

- Exploratory views may include clearly labelled provisional records.
- Official outputs use validated records by default.
- Every coded claim must retain page-level evidence.
- Every output records the corpus cutoff, codebook version and research-specification version.
- The denominator and missing-data treatment must be visible for every indicator.
- Language models may explain validated results, but cannot invent values or silently alter the
  population used by deterministic calculations.

## Report modes

- **Baseline report** — a reproducible report for a fixed corpus cutoff and specification version.
- **Live-corpus report** — the same registered analyses recalculated as validated agreements grow.
- **Custom report** — a user-selected subset or theme, with the same provenance and validation
  rules.

## Delivery sequence

1. Complete structured agreement metadata and validation gates.
2. Implement registered analytical datasets and indicator functions.
3. Add automated quality tests against known benchmark cases.
4. Build reusable figure and table components from analytical datasets.
5. Assemble narrative, methods and evidence manifests into exportable reports.
6. Add scheduled corpus refresh and reproducible publication snapshots.

## Current implementation status — 29 October 2026

The operational prototype now persists original PDFs, extracts/OCRs page text, prepares a complete
nine-question provisional agreement profile, verifies returned quotations against the source,
supports human validation with rationale, and exposes agreement comparison. Gemini 3.8 Flash is
configured as the hosted semantic-analysis provider; a conservative local evidence scan keeps the
workflow usable if provider access or credits are unavailable.

The next research-engine milestone is not to recreate fixed figures manually. It is to register
deterministic indicators over approved profiles, render reusable charts, and assemble reproducible
reports with methods, limitations and evidence manifests.

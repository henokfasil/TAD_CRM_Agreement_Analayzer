# One-Page Proposal: CRM Agreement Intelligence System

## Purpose

This proposal outlines a human-in-the-loop approach for improving how critical raw materials agreements are collected, reviewed, coded, and compared. The goal is to support faster and more transparent analysis while preserving expert judgement as the final authority.

## Problem

Critical raw materials agreements are often dispersed across PDFs, public announcements, government pages, and institutional repositories. Manual review is time-consuming, and coding decisions can be difficult to trace back to specific agreement text. As the number of agreements grows, it becomes harder to maintain consistency, provenance, and review quality.

## Proposed Approach

The proposed system creates a structured workflow for agreement intelligence:

1. Ingest agreement documents in PDF format.
2. Extract text while preserving page-level provenance.
3. Segment candidate provisions for review.
4. Apply a CRM-specific codebook.
5. Generate provisional AI coding proposals.
6. Run a verification step to flag missing evidence or rule conflicts.
7. Preserve human adjudication as the final decision layer.
8. Export results for analysis, reporting, and comparison.

The system is designed so that AI outputs are never treated as validated results. They are only provisional suggestions that require review, verification, and adjudication.

## Potential Value

- Faster initial review of long agreement documents.
- Better traceability from each coding decision back to page-level evidence.
- More consistent use of the codebook across agreements.
- Clear separation between raw AI output, verification, reviewer judgement, and final adjudicated decisions.
- A foundation for future monitoring of newly published CRM agreements.

## Future Extension

A later phase could add a discovery layer that searches trusted public sources on a weekly schedule, identifies potential new agreements, stores them in a discovery queue, and allows a human reviewer to approve documents before they enter the main ingestion and coding workflow.

## Current Status

A working prototype has been developed for demonstration purposes. It includes document ingestion, page extraction, candidate provision segmentation, codebook management, manual coding, AI-assisted coding proposals, verification outputs, adjudication, dashboard views, and exports. It is suitable for discussion and feedback, but should be treated as a prototype rather than a production system.

## Suggested Next Step

Present the concept and prototype workflow to the team leader, gather feedback on usefulness and governance, and decide whether to develop it further as a formal internal tool or research-support workflow.

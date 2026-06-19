from __future__ import annotations


class CRMError(Exception):
    """Base exception for project-specific errors."""


class DuplicateDocumentError(CRMError):
    """Raised when an uploaded document hash already exists."""


class ExtractionError(CRMError):
    """Raised when a document cannot be extracted by the configured parser."""


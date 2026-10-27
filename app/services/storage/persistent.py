from __future__ import annotations

import os
import mimetypes
from pathlib import Path
from typing import Any

import psycopg
import boto3
from botocore.config import Config
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

LOCAL_DEFAULT_DATABASE_URL = "postgresql+psycopg://crm:crm@localhost:5432/crm_agreements"
DEFAULT_WORKSPACE_PATH = Path("data/processed/document_workspace.sqlite")


def persistent_database_url() -> str | None:
    value = os.environ.get("DATABASE_URL", "").strip()
    if not value or value == LOCAL_DEFAULT_DATABASE_URL or "localhost" in value:
        return None
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def uses_persistent_store(db_path: Path = DEFAULT_WORKSPACE_PATH) -> bool:
    return Path(db_path) == DEFAULT_WORKSPACE_PATH and persistent_database_url() is not None


def _connect() -> psycopg.Connection:
    url = persistent_database_url()
    if not url:
        raise RuntimeError("A persistent DATABASE_URL is not configured.")
    return psycopg.connect(url, row_factory=dict_row)


def _object_storage_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL_S3"),
        region_name=os.environ.get("AWS_REGION"),
        config=Config(s3={"addressing_style": "path"}),
    )


def initialize_persistent_store() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS crm_record_store (
                collection TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (collection, record_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS crm_document_files (
                document_id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                object_key TEXT NOT NULL,
                size_bytes BIGINT NOT NULL,
                sha256_hash TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_crm_record_store_collection ON crm_record_store (collection)"
        )


def upsert_record(collection: str, record_id: str, payload: dict[str, Any]) -> None:
    initialize_persistent_store()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO crm_record_store (collection, record_id, payload)
            VALUES (%s, %s, %s)
            ON CONFLICT (collection, record_id) DO UPDATE
            SET payload = EXCLUDED.payload, updated_at = NOW()
            """,
            (collection, record_id, Jsonb(payload)),
        )


def load_records(collection: str) -> list[dict[str, Any]]:
    initialize_persistent_store()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM crm_record_store WHERE collection = %s ORDER BY updated_at DESC",
            (collection,),
        ).fetchall()
    return [dict(row["payload"]) for row in rows]


def get_record(collection: str, record_id: str) -> dict[str, Any] | None:
    initialize_persistent_store()
    with _connect() as connection:
        row = connection.execute(
            "SELECT payload FROM crm_record_store WHERE collection = %s AND record_id = %s",
            (collection, record_id),
        ).fetchone()
    return dict(row["payload"]) if row else None


def delete_collection(collection: str) -> None:
    initialize_persistent_store()
    with _connect() as connection:
        connection.execute("DELETE FROM crm_record_store WHERE collection = %s", (collection,))


def save_document_file(record: dict[str, Any]) -> None:
    path = Path(record["stored_path"])
    if not path.exists():
        return
    initialize_persistent_store()
    bucket = os.environ.get("NEON_STORAGE_BUCKET", "crm-agreements")
    object_key = f"agreements/{record['sha256_hash']}{path.suffix.lower()}"
    mime_type = mimetypes.guess_type(record["original_filename"])[0] or "application/octet-stream"
    client = _object_storage_client()
    client.upload_file(
        str(path),
        bucket,
        object_key,
        ExtraArgs={"ContentType": mime_type},
    )
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO crm_document_files (
                document_id, original_filename, mime_type, object_key, size_bytes, sha256_hash
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_id) DO UPDATE SET
                original_filename = EXCLUDED.original_filename,
                mime_type = EXCLUDED.mime_type,
                object_key = EXCLUDED.object_key,
                size_bytes = EXCLUDED.size_bytes,
                sha256_hash = EXCLUDED.sha256_hash,
                updated_at = NOW()
            """,
            (
                record["document_id"],
                record["original_filename"],
                mime_type,
                object_key,
                record["size_bytes"],
                record["sha256_hash"],
            ),
        )


def load_document_file(document_id: str) -> dict[str, Any] | None:
    initialize_persistent_store()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT original_filename, mime_type, object_key, size_bytes
            FROM crm_document_files
            WHERE document_id = %s
            """,
            (document_id,),
        ).fetchone()
    if not row:
        return None
    response = _object_storage_client().get_object(
        Bucket=os.environ.get("NEON_STORAGE_BUCKET", "crm-agreements"),
        Key=row["object_key"],
    )
    return {
        "original_filename": row["original_filename"],
        "mime_type": row["mime_type"],
        "size_bytes": row["size_bytes"],
        "data": response["Body"].read(),
    }


def delete_document_files() -> None:
    initialize_persistent_store()
    bucket = os.environ.get("NEON_STORAGE_BUCKET", "crm-agreements")
    with _connect() as connection:
        rows = connection.execute("SELECT object_key FROM crm_document_files").fetchall()
        if rows:
            client = _object_storage_client()
            client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": row["object_key"]} for row in rows]},
            )
        connection.execute("DELETE FROM crm_document_files")


def persistent_store_status() -> dict[str, Any]:
    initialize_persistent_store()
    with _connect() as connection:
        collections = connection.execute(
            "SELECT collection, COUNT(*) AS records FROM crm_record_store GROUP BY collection ORDER BY collection"
        ).fetchall()
        file_count = connection.execute("SELECT COUNT(*) AS count FROM crm_document_files").fetchone()
    return {
        "backend": "Neon PostgreSQL",
        "durable": True,
        "collections": collections,
        "stored_pdf_files": file_count["count"],
    }

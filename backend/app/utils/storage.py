"""
Supabase Storage helpers for resume files.

Container disk is ephemeral on Cloud Run — resume PDFs live in the private
`resumes` bucket instead. `resume_key` (stored on the `resumes` row) is the
object path within that bucket.
"""
import logging

from app.dependencies.database import db_client

RESUME_BUCKET = "CareerAtlas"

logger = logging.getLogger(__name__)


def upload_resume_file(object_path: str, data: bytes, content_type: str = "application/pdf") -> str:
    """Upload a resume file to the private bucket; return its object path."""
    db_client.storage.from_(RESUME_BUCKET).upload(
        path=object_path,
        file=data,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return object_path


def download_resume_file(object_path: str) -> bytes:
    """Download a resume file by its storage object path."""
    return db_client.storage.from_(RESUME_BUCKET).download(object_path)

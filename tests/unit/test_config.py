from app.core.config import Settings


def test_max_upload_bytes() -> None:
    settings = Settings(max_upload_mb=2)
    assert settings.max_upload_bytes == 2 * 1024 * 1024


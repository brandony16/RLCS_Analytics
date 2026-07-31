from pathlib import Path

from src.api.routes.replays import resolve_upload_dir


def test_resolve_upload_dir_defaults_to_backend_data_raw(monkeypatch):
    monkeypatch.delenv("REPLAY_UPLOAD_DIR", raising=False)

    expected = (Path(__file__).resolve().parents[2] / "data" / "raw").resolve()

    assert resolve_upload_dir() == expected


def test_resolve_upload_dir_uses_env_override(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("REPLAY_UPLOAD_DIR", str(upload_dir))

    assert resolve_upload_dir() == upload_dir.resolve()

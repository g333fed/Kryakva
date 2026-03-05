from pathlib import Path

import pytest

from app import source_guard


def test_source_guard_bypass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KRYAKVA_ALLOW_UNVERIFIED_SOURCE", "1")
    monkeypatch.setattr(source_guard, "ROOT_DIR", tmp_path)
    source_guard.ensure_github_source()


def test_source_guard_rejects_non_github(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(source_guard, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(source_guard, "_git_remote_url", lambda _repo: "https://example.com/repo.git")

    with pytest.raises(source_guard.SourceGuardError):
        source_guard.ensure_github_source()

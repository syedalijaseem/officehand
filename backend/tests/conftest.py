from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

VALID_SECRET = "s" * 48
VALID_KEK = "k" * 44
VALID_PEPPER = "p" * 40


def make_settings(tmp_path: Path, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "env": "test",
        "demo_mode": True,
        "data_dir": tmp_path / "data",
        "frontend_dist": tmp_path / "dist",
        "session_secret": VALID_SECRET,
        "kek_keys": VALID_KEK,
        "log_hash_pepper": VALID_PEPPER,
        "llm_provider": "fake",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


@pytest.fixture
def settings_factory(tmp_path: Path) -> Callable[..., Settings]:
    def factory(**overrides: Any) -> Settings:
        return make_settings(tmp_path, **overrides)

    return factory


@pytest.fixture
def dist_dir(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        '<!doctype html><html><head><script type="importmap">{"integrity":{}}</script>'
        '<link rel="stylesheet" href="styles-ABC.css"></head>'
        '<body><app-root></app-root><script src="main-XYZ.js" type="module"></script></body></html>',
        encoding="utf-8",
    )
    (dist / "main-XYZ.js").write_text("console.log('app')", encoding="utf-8")
    return dist


@pytest.fixture
def client(settings_factory: Callable[..., Settings], dist_dir: Path) -> Iterator[TestClient]:
    app = create_app(settings_factory())
    with TestClient(app) as test_client:
        yield test_client

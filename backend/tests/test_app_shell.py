import re
from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

EXPECTED_HEADERS = {
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "cross-origin-opener-policy": "same-origin",
    "cross-origin-resource-policy": "same-origin",
}


def _nonce_from_csp(csp: str) -> str:
    match = re.search(r"'nonce-([A-Za-z0-9_-]+)'", csp)
    assert match, csp
    return match.group(1)


def test_healthz_returns_only_status(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_security_headers_on_every_response(client: TestClient) -> None:
    for path in ("/healthz", "/", "/api/does-not-exist"):
        response = client.get(path)
        for name, value in EXPECTED_HEADERS.items():
            assert response.headers[name] == value, (path, name)
        csp = response.headers["content-security-policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "object-src 'none'" in csp
        assert "unsafe-inline" not in csp
        assert "max-age=" in response.headers["strict-transport-security"]


def test_index_injects_per_request_csp_nonce(client: TestClient) -> None:
    first = client.get("/")
    second = client.get("/inbox/123")  # SPA deep link falls back to index

    assert first.status_code == 200
    assert second.status_code == 200
    nonce_one = _nonce_from_csp(first.headers["content-security-policy"])
    nonce_two = _nonce_from_csp(second.headers["content-security-policy"])
    assert nonce_one != nonce_two
    assert f'<app-root ngCspNonce="{nonce_one}">' in first.text
    assert first.headers["cache-control"] == "no-store"


def test_static_asset_is_served(client: TestClient) -> None:
    response = client.get("/main-XYZ.js")

    assert response.status_code == 200
    assert "console.log" in response.text


def test_path_traversal_never_serves_files_outside_dist(client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "secret.txt").write_text("TOP-SECRET", encoding="utf-8")

    for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt"):
        response = client.get(path)
        assert "TOP-SECRET" not in response.text, path


def test_unknown_api_route_is_json_404_and_not_cached(client: TestClient) -> None:
    response = client.get("/api/nope")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}
    assert response.headers["cache-control"] == "no-store"


def test_missing_frontend_build_returns_friendly_503(
    settings_factory: Callable[..., Settings], tmp_path: Path
) -> None:
    app = create_app(settings_factory(frontend_dist=tmp_path / "missing"))
    with TestClient(app) as test_client:
        response = test_client.get("/")

    assert response.status_code == 503
    assert "not built" in response.text.lower()


def test_openapi_docs_hidden_in_prod(settings_factory: Callable[..., Settings], dist_dir: Path) -> None:
    app = create_app(settings_factory(env="prod"))
    with TestClient(app) as test_client:
        assert test_client.get("/api/openapi.json").status_code == 404
        assert test_client.get("/api/docs").status_code == 404


def test_openapi_docs_available_in_dev(settings_factory: Callable[..., Settings], dist_dir: Path) -> None:
    app = create_app(settings_factory(env="dev"))
    with TestClient(app) as test_client:
        assert test_client.get("/api/openapi.json").status_code == 200
        assert "swagger" in test_client.get("/api/docs").text.lower()


def test_build_script_tags_carry_the_nonce_and_csp_allows_it(client: TestClient) -> None:
    response = client.get("/")
    nonce = _nonce_from_csp(response.headers["content-security-policy"])

    script_src = next(
        d for d in response.headers["content-security-policy"].split("; ") if d.startswith("script-src")
    )
    assert script_src == f"script-src 'self' 'nonce-{nonce}'"
    assert f'<script nonce="{nonce}" type="importmap">' in response.text
    assert f'<script nonce="{nonce}" src="main-XYZ.js"' in response.text

"""Serves the built Angular app: static files from the dist folder, index.html for everything else.

index.html gets the request's CSP nonce injected as `ngCspNonce`, so Angular can apply it to the
styles it adds at runtime.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

APP_ROOT_TAG = "<app-root"
NOT_BUILT_MESSAGE = "<!doctype html><title>OfficeHand</title><p>The frontend is not built yet.</p>"


def _safe_static_file(dist: Path, request_path: str) -> Path | None:
    """Return the file for request_path if it exists *inside* dist, else None."""
    if not request_path:
        return None
    candidate = (dist / request_path).resolve()
    if not candidate.is_relative_to(dist) or not candidate.is_file():
        return None
    return candidate


def _render_index(index_html: str, nonce: str) -> str:
    """Stamp the request nonce on the app root (for Angular's runtime styles) and on the build's own
    script tags. index.html comes only from our build output, never from user content."""
    html = index_html.replace(APP_ROOT_TAG, f'{APP_ROOT_TAG} ngCspNonce="{nonce}"', 1)
    return html.replace("<script ", f'<script nonce="{nonce}" ')


def build_spa_router(frontend_dist: Path) -> APIRouter:
    dist = frontend_dist.resolve()
    index_file = dist / "index.html"
    router = APIRouter(include_in_schema=False)

    @router.get("/{full_path:path}")
    async def spa(full_path: str, request: Request) -> Response:
        if full_path == "api" or full_path.startswith("api/"):
            return Response('{"detail":"Not found"}', status_code=404, media_type="application/json")

        static_file = _safe_static_file(dist, full_path)
        if static_file is not None and static_file != index_file:
            return FileResponse(static_file)

        if not index_file.is_file():
            return HTMLResponse(NOT_BUILT_MESSAGE, status_code=503)

        html = _render_index(index_file.read_text(encoding="utf-8"), request.state.csp_nonce)
        return HTMLResponse(html, headers={"Cache-Control": "no-store"})

    return router

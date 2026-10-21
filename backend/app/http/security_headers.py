"""Security headers and a per-request CSP nonce for every response."""

import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

NONCE_BYTES = 16

STATIC_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def build_csp(nonce: str) -> str:
    directives = [
        "default-src 'self'",
        # The nonce covers the build's inline import map (SRI hashes for lazy chunks).
        f"script-src 'self' 'nonce-{nonce}'",
        f"style-src 'self' 'nonce-{nonce}'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self' https://accounts.google.com",
        "object-src 'none'",
        "upgrade-insecure-requests",
    ]
    return "; ".join(directives)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        nonce = secrets.token_urlsafe(NONCE_BYTES)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        for name, value in STATIC_HEADERS.items():
            response.headers[name] = value
        response.headers["Content-Security-Policy"] = build_csp(nonce)
        if request.url.path.startswith("/api/") or request.url.path == "/api":
            response.headers["Cache-Control"] = "no-store"
        return response

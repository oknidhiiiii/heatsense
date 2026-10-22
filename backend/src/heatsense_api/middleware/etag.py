"""HTTP ETag and 304 Conditional Caching Middleware.

Computes a deterministic SHA-256 ETag for successful GET/HEAD responses.
Returns HTTP 304 Not Modified when client provides matching If-None-Match header.
"""

import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ETagMiddleware(BaseHTTPMiddleware):
    """Middleware for generating ETags and serving HTTP 304 Not Modified."""

    async def dispatch(self, request: Request, call_next):
        # Only cache GET and HEAD requests
        if request.method not in ("GET", "HEAD"):
            return await call_next(request)

        response = await call_next(request)

        # Only process 200 OK responses
        if response.status_code != 200:
            return response

        # Read response body chunks into memory
        body_chunks = [chunk async for chunk in response.body_iterator]
        body_bytes = b"".join(body_chunks)

        # Generate standard weak ETag based on body content SHA-256 hash
        digest = hashlib.sha256(body_bytes).hexdigest()[:16]
        etag = f'W/"{digest}"'

        # Check client conditional request header
        if_none_match = request.headers.get("if-none-match")
        if if_none_match:
            # Match either weak ETag or raw hash
            client_etags = [t.strip() for t in if_none_match.split(",")]
            if etag in client_etags or f'"{digest}"' in client_etags or "*" in client_etags:
                return Response(
                    status_code=304,
                    headers={
                        "etag": etag,
                        "cache-control": response.headers.get(
                            "cache-control",
                            "public, max-age=60, stale-while-revalidate=300",
                        ),
                    },
                )

        # Reconstruct response with computed ETag header
        headers = dict(response.headers)
        headers["etag"] = etag
        if "cache-control" not in headers:
            headers["cache-control"] = "public, max-age=60, stale-while-revalidate=300"

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

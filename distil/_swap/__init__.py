"""Web (HTML) layer: server-rendered pages and HTMX endpoints.

Kept separate from ``app.api`` (JSON) so the two surfaces can evolve
independently — the API is for programmatic clients, the web layer is for
humans in a browser.
"""

from app.web.routes import router as web_router

__all__ = ["web_router"]
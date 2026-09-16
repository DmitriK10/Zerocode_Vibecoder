"""Jinja2 environment and rendering helpers.

Two helpers are exposed:

* :func:`render_page` — renders a full HTML page (uses ``base.html``).
* :func:`render_partial` — renders an HTML fragment for HTMX swaps,
  returning a plain :class:`HTMLResponse` with status 200.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import PROJECT_ROOT

TEMPLATES_DIR: Path = PROJECT_ROOT / "app" / "templates"
STATIC_DIR: Path = PROJECT_ROOT / "app" / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render_page(
    request: Request,
    template_name: str,
    **context: Any,
) -> HTMLResponse:
    """Render a full page (extends ``base.html``)."""
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


def render_partial(template_name: str, **context: Any) -> HTMLResponse:
    """Render an HTML fragment for an HTMX swap."""
    template = templates.get_template(template_name)
    return HTMLResponse(content=template.render(**context))
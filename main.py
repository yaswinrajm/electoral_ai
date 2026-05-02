"""
main.py — Electoral AI Application Entry Point
===============================================
Bootstraps the FastAPI application for the Multilingual Electoral AI Dashboard.

Responsibilities:
    - Creates the FastAPI ``app`` instance with metadata from ``settings``
    - Mounts the ``/static`` directory for CSS, JS, and image assets
    - Registers the Jinja2 template engine for server-side HTML rendering
    - Includes the API router with the ``/api`` prefix
    - Serves the single-page dashboard on ``GET /``
    - Starts the Uvicorn ASGI development server when run directly

Architecture Overview:
    User Browser
        → GET /              → templates/index.html  (Jinja2)
        → GET /static/*      → static/               (files)
        → POST /api/ask      → api/routes.py          (controller)
            → services/ai_service.py                  (Gemini logic)
        → POST /api/tts      → api/routes.py
            → services/tts_service.py                 (TTS logic)
        → POST /api/translate → api/routes.py
            → services/translation_service.py         (Translation logic)
        → GET /api/dictionary → api/routes.py
            → data/electoral_data.py                  (static cache)

Usage:
    Development::

        python main.py
        # or
        uvicorn main:app --reload

    Production (Docker / Cloud Run)::

        uvicorn main:app --host 0.0.0.0 --port 8080

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.routes import router as api_router
from config import settings


# ─── Application Instance ─────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_title,
    description=(
        "A voice-first, multilingual AI dashboard that guides Indian voters through "
        "the electoral process in 10 regional languages using Google Vertex AI (Gemini), "
        "Google Cloud Translation, and Google Cloud Text-to-Speech."
    ),
    version=settings.app_version,
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc",     # ReDoc UI at /redoc
)


# ─── Static Assets ────────────────────────────────────────────────────────────
# Serves all files under /static at the URL path /static.
# Examples: /static/js/app.js, /static/css/style.css, /static/translations.json
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Jinja2 Template Engine ───────────────────────────────────────────────────
# Loads HTML templates from the /templates directory for server-side rendering.
templates = Jinja2Templates(directory="templates")


# ─── API Router ───────────────────────────────────────────────────────────────
# All endpoints in api/routes.py are available under the /api prefix:
#   GET  /api/health       → health check
#   GET  /api/dictionary   → UI translation cache
#   POST /api/translate    → text translation
#   POST /api/tts          → text-to-speech
#   POST /api/ask          → Gemini AI Q&A
app.include_router(api_router, prefix="/api")


# ─── Page Routes ──────────────────────────────────────────────────────────────

@app.get("/", summary="Serve Dashboard", response_class=HTMLResponse, tags=["Pages"])
async def serve_home(request: Request) -> Any:
    """
    Serves the main Electoral AI single-page dashboard.

    Renders ``templates/index.html`` via Jinja2. All in-page navigation
    (Home, Features, Practice Booth, Quiz, Timeline) is handled client-side
    by ``static/js/app.js`` without page reloads.

    Args:
        request (Request): The FastAPI/Starlette request object required
                           by Jinja2Templates.TemplateResponse.

    Returns:
        TemplateResponse: Rendered ``index.html`` with the request context.
    """
    context: Dict[str, Any] = {"request": request, "title": settings.app_title}
    return templates.TemplateResponse("index.html", context)


# ─── Development Server Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,   # Enable hot-reloading in development
        log_level="info",
    )

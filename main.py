"""
main.py — Electoral AI Dashboard Application Entry Point
=========================================================
This file bootstraps the FastAPI application for the Multilingual Electoral AI
Dashboard. It is responsible for:
  - Mounting static file assets (CSS, JS, images)
  - Registering Jinja2 HTML templates for server-side rendering
  - Registering the API router for all /api/* routes
  - Serving the root HTML page
  - Starting the Uvicorn ASGI server when run directly

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api.routes import router as api_router
from config import settings
import uvicorn

# ─── App Initialization ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="A voice-first, multilingual AI dashboard for Indian election guidance.",
    version="2.0.0"
)

# ─── Static Assets ────────────────────────────────────────────────────────────
# Serves files in the /static directory at the URL path /static
# e.g., /static/js/app.js, /static/css/style.css
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── HTML Templates ───────────────────────────────────────────────────────────
# Jinja2 template engine for rendering HTML files from the /templates directory
templates = Jinja2Templates(directory="templates")

# ─── API Routes ───────────────────────────────────────────────────────────────
# All API endpoints are registered under the /api prefix (e.g., /api/ask, /api/tts)
app.include_router(api_router, prefix="/api")


# ─── Page Routes ──────────────────────────────────────────────────────────────

@app.get("/", summary="Serve Home Page")
async def serve_home(request: Request):
    """
    Serves the main single-page dashboard (index.html).
    All navigation is handled client-side via JavaScript.
    """
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home"})


# ─── Development Server ───────────────────────────────────────────────────────
if __name__ == "__main__":
    # Starts a hot-reloading dev server when running `python main.py`
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api.routes import router as api_router
from config import settings
import uvicorn

app = FastAPI(title=settings.app_name)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home"})

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)

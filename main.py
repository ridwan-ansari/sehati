from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.src.router.api import router
from app.src.core.templates import get_templates

templates = get_templates()
app = FastAPI(title="MRA Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root(request: Request):
    """Redirect ke dashboard login"""
    return RedirectResponse(url="/dashboard/login")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("errors/404.html", {"request": request}, status_code=404)
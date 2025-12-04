from __future__ import annotations

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException

from app.src.router.chat.api import ws_router
from app.src.core.templates import get_templates
from app.src.router.api import router, router_dashboard

templates = get_templates()
app = FastAPI(title="SEHATI")

app.mount("/static", StaticFiles(directory="app/src/static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(router_dashboard)
app.include_router(ws_router, prefix="/ws", tags=["Chat WebSocket"])

@app.get("/")
async def root(request: Request):
    """Redirect ke dashboard login"""
    return RedirectResponse(url="/dashboard/login")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("errors/404.html", {"request": request}, status_code=404)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 302 and exc.headers and "Location" in exc.headers:
        return RedirectResponse(
            url=exc.headers["Location"],
            status_code=302
        )
    return {"detail": exc.detail}
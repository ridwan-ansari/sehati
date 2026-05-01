from __future__ import annotations

from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from app.src.router.chat.api import ws_router
from app.src.core.templates import get_templates
from app.src.router.api import router, router_dashboard
from app.src.utils.execeptions import UnauthorizedException, ForbiddenException

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


def _is_dashboard(request: Request) -> bool:
    return request.url.path.startswith("/dashboard")


def _admin_error(request: Request, status_code: int, detail: str | None = None):
    return templates.TemplateResponse(
        "admin/error.html",
        {
            "request": request,
            "status_code": status_code,
            "detail": detail,
            "year": datetime.now().year,
        },
        status_code=status_code,
    )


@app.get("/")
async def root(request: Request):
    return RedirectResponse(url="/dashboard/login")

@app.get("/privacy-policy")
async def privacy_policy(request: Request):
    return templates.TemplateResponse("/privacy_policy/index.html", {"request": request, "year": datetime.now().year}, status_code=200)

@app.get("/term-of-service")
async def term_of_service(request: Request):
    return templates.TemplateResponse("/term_of_service/index.html", {"request": request, "year": datetime.now().year}, status_code=200)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    if _is_dashboard(request):
        return _admin_error(request, 404, "Halaman yang Anda cari tidak ditemukan.")
    return templates.TemplateResponse("errors/404.html", {"request": request}, status_code=404)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 302 and exc.headers and "Location" in exc.headers:
        return RedirectResponse(url=exc.headers["Location"], status_code=302)

    if _is_dashboard(request):
        return _admin_error(request, exc.status_code, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if _is_dashboard(request):
        first_error = exc.errors()[0].get("msg", "Data tidak valid") if exc.errors() else "Data tidak valid"
        return _admin_error(request, 422, first_error)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "status_code": 422,
            "message": "Validation error",
            "data": exc.errors(),
        },
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    if _is_dashboard(request):
        return _admin_error(request, 500, None)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status_code": 500,
            "message": "Internal server error",
            "data": None,
        },
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    if _is_dashboard(request):
        return _admin_error(request, 401, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    if _is_dashboard(request):
        return _admin_error(request, 403, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )
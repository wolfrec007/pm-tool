import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.email_worker import email_worker_lifespan
from app.exceptions import (
    ConflictWithLeaveError,
    NotFoundError,
    OverAllocationError,
    ValidationError,
)
from app.routers import (
    admin_settings,
    assignments,
    auth,
    clients,
    dashboard,
    engagements,
    health,
    leaves,
    outbox,
    reports,
    team_members,
    users,
)


@asynccontextmanager
async def lifespan(app):
    async with email_worker_lifespan():
        yield


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

# Session middleware (required for auth)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=False,  # Allow HTTP in development
)

# Templates
from app.templates_setup import templates


def csrf_token(request: Request) -> str:
    """Get or generate a CSRF token stored in the session."""
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        request.session["csrf_token"] = token
    return token


@app.middleware("http")
async def flash_middleware(request: Request, call_next):
    """Pop flash message after response so it shows only once."""
    response = await call_next(request)
    request.session.pop("_flash", None)
    return response


# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(team_members.router)
app.include_router(clients.router)
app.include_router(engagements.router)
app.include_router(assignments.router)
app.include_router(leaves.router)
app.include_router(reports.router)
app.include_router(admin_settings.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(outbox.router)


@app.get("/test")
def test_page(request: Request):
    return templates.TemplateResponse(request, "test.html")


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard", status_code=303)


# Global exception handlers
@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "errors/error.html", {
            "status_code": 404, "detail": str(exc),
        }, status_code=404)
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(OverAllocationError)
def over_allocation_handler(request: Request, exc: OverAllocationError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "errors/error.html", {
            "status_code": 409, "detail": str(exc),
        }, status_code=409)
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ConflictWithLeaveError)
def conflict_leave_handler(request: Request, exc: ConflictWithLeaveError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "errors/error.html", {
            "status_code": 409, "detail": str(exc),
        }, status_code=409)
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
def validation_handler(request: Request, exc: ValidationError):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "errors/error.html", {
            "status_code": 422, "detail": str(exc),
        }, status_code=422)
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "errors/error.html", {
            "status_code": exc.status_code, "detail": exc.detail,
        }, status_code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

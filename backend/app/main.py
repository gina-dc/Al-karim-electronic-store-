from contextlib import asynccontextmanager
from html import escape

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from tortoise import connections
from tortoise.contrib.fastapi import RegisterTortoise
from tortoise.exceptions import DBConnectionError, IntegrityError, OperationalError

from app.api.v1.auth import router as auth_router
from app.api.v1.business import router as business_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router
from app.api.v1.workforce import router as workforce_router
from app.core.config import get_settings
from app.db.config import TORTOISE_ORM


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(app, config=TORTOISE_ORM, generate_schemas=False):
        yield


settings = get_settings()
app = FastAPI(
    title="Electronics Shop Management",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.environment != "production" else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(business_router, prefix="/api/v1")
app.include_router(workforce_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "A record with these unique details already exists"},
    )


@app.get("/api/health/live")
async def live():
    return {"status": "ok"}


@app.get("/api/health/ready")
async def ready():
    try:
        await connections.get("default").execute_query("SELECT 1")
    except (TimeoutError, OperationalError, DBConnectionError, OSError):
        return JSONResponse(status_code=503, content={"status": "database unavailable"})
    return {"status": "ready"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def api_home():
    frontend = escape(settings.frontend_origin, quote=True)
    docs = '<p><a href="/api/docs">API documentation</a></p>' if app.docs_url else ""
    return HTMLResponse(f"""<!doctype html>
<html lang="ur" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Al-Karim — API</title>
<style>body{{font-family:system-ui,sans-serif;background:#f4f7f5;color:#173d30;margin:0;padding:32px}}main{{max-width:620px;margin:60px auto;padding:32px;border-radius:16px;background:white}}a{{color:#126b56}}.open{{display:inline-block;padding:12px 20px;background:#126b56;color:white;border-radius:8px;text-decoration:none}}</style>
</head><body><main><h1>سرور چل رہا ہے</h1>
<p>دکان کی ایپلیکیشن کھولنے کے لیے نیچے کلک کریں۔ فرنٹ اینڈ بھی چلنا چاہیے۔</p>
<p lang="en" dir="ltr">The backend is running. Open the shop application using the link below. Keep the frontend server running as well.</p>
<p><a class="open" href="{frontend}">ایپلیکیشن کھولیں / Open application</a></p>
<p dir="ltr">{frontend}</p>{docs}</main></body></html>""")


@app.get("/favicon.ico", include_in_schema=False, status_code=204)
async def favicon():
    return Response(status_code=204)

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.auth import auth_middleware
from api.db.database import init_db
from api.routers import brief, dashboard, log, metrics

app = FastAPI(title="Forge")

app.middleware("http")(auth_middleware)

app.include_router(dashboard.router)
app.include_router(log.router)
app.include_router(metrics.router)
app.include_router(brief.router)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


@app.on_event("startup")
def on_startup() -> None:
    init_db()

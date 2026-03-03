from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="PurpleForge API",
    description="Detection Validation Layer for Attack Technique Simulation",
    version="0.1.0",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/dashboard")
def dashboard():
    return FileResponse("app/static/index.html")

@app.get("/")
def root():
    return {"message": "PurpleForge API is running", "version": "0.1.0"}

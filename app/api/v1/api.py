from fastapi import APIRouter
from app.api.v1.endpoints import executions, techniques

api_router = APIRouter()
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(techniques.router, prefix="/techniques", tags=["techniques"])

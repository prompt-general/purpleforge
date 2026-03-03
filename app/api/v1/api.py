from fastapi import APIRouter
from app.api.v1.endpoints import executions, techniques, rules, reports

api_router = APIRouter()
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(techniques.router, prefix="/techniques", tags=["techniques"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

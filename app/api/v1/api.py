from fastapi import APIRouter
from app.api.v1.endpoints import executions, techniques, rules, reports, chains, collaboration, intel, integrations\n

api_router = APIRouter()
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(techniques.router, prefix="/techniques", tags=["techniques"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(chains.router, prefix="/chains", tags=["chains"])
api_router.include_router(collaboration.router, prefix="/collab", tags=["collaboration"])
api_router.include_router(intel.router, prefix="/intel", tags=["intel"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])\n

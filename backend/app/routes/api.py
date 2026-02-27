from fastapi import APIRouter

from app.routes.catalogs import router as catalogs_router
from app.routes.jobs import router as jobs_router
from app.routes.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(upload_router)
api_router.include_router(jobs_router)
api_router.include_router(catalogs_router)


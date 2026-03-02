from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_catalogs_repo, get_jobs_repo
from app.models.schemas import CatalogResponse, UpdateCatalogRequest, UpdateCatalogResponse
from app.repo.interfaces import CatalogsRepo, JobsRepo

router = APIRouter(tags=["catalogs"])


@router.get("/jobs/{video_id}/catalog", response_model=CatalogResponse)
def get_job_catalog(
    video_id: str,
    jobs_repo: JobsRepo = Depends(get_jobs_repo),
    catalogs_repo: CatalogsRepo = Depends(get_catalogs_repo),
) -> CatalogResponse:
    job = jobs_repo.get_by_video_id(video_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found for video_id")

    if job["status"] != "COMPLETED":
        raise HTTPException(status_code=409, detail="Catalog not ready yet")

    catalog = catalogs_repo.get_by_job_id(job["job_id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    return CatalogResponse(**catalog)


@router.put("/catalogs/{catalog_id}", response_model=UpdateCatalogResponse)
def update_catalog(
    catalog_id: str,
    payload: UpdateCatalogRequest,
    catalogs_repo: CatalogsRepo = Depends(get_catalogs_repo),
) -> UpdateCatalogResponse:
    catalog = catalogs_repo.get_by_catalog_id(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    catalogs_repo.update_catalog(catalog_id, [item.model_dump() for item in payload.products])
    return UpdateCatalogResponse(status="updated", catalog_id=catalog_id)

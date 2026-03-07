from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    content_type: str = "video/mp4"
    file_size: int = Field(..., ge=1)


class PresignedUrlResponse(BaseModel):
    video_id: str
    job_id: str
    upload_url: str
    expires_in: int


class UseSampleResponse(BaseModel):
    """Response for use-sample: use a video from sample_video without upload."""

    video_id: str
    job_id: str
    message: str = "No upload needed. Call POST /jobs/{video_id}/process to run the pipeline."


class ProcessJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    video_id: str
    status: str
    product_count: int = 0
    error_message: str | None = None
    catalog_id: str | None = None
    updated_at: datetime


class NutritionFacts(BaseModel):
    model_config = {"extra": "allow"}
    energy: str | None = None
    protein: str | None = None
    fat: str | None = None
    carbs: str | None = None
    sodium: str | None = None


class ProductImage(BaseModel):
    model_config = {"extra": "allow"}
    image_id: str
    image_url: str
    frame_type: str | None = None


class CatalogProduct(BaseModel):
    model_config = {"extra": "allow"}

    product_id: str
    brand: str | None = None
    product_name: str

    variant: str | None = None
    category: str | None = None
    net_weight: str | None = None
    price: float | None = None
    image_url: str | None = None

    # Rich fields from multi-frame extraction
    ingredients: str | None = None
    nutrition_facts: NutritionFacts | dict | None = None
    barcode: str | None = None
    fssai_license: str | None = None
    manufacturer: str | None = None
    shelf_life: str | None = None
    description: str | None = None
    tags: list[str] | None = None

    # Multiple images from different angles
    images: list[ProductImage] | list[dict] | None = None


class CatalogResponse(BaseModel):
    catalog_id: str
    job_id: str
    status: str
    products: list[CatalogProduct]
    ondc_catalog: dict[str, Any]
    created_at: datetime


class UpdateCatalogRequest(BaseModel):
    products: list[CatalogProduct]


class UpdateCatalogResponse(BaseModel):
    status: str
    catalog_id: str

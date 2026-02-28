from __future__ import annotations

from typing import Protocol


class JobsRepo(Protocol):
    def create_job(self, video_id: str) -> dict: ...

    def get_by_video_id(self, video_id: str) -> dict | None: ...

    def get_by_job_id(self, job_id: str) -> dict | None: ...

    def update_status(
        self,
        job_id: str,
        status: str,
        *,
        product_count: int | None = None,
        error_message: str | None = None,
        catalog_id: str | None = None,
    ) -> dict: ...


class CatalogsRepo(Protocol):
    def create_catalog(
        self,
        job_id: str,
        *,
        products: list[dict],
        ondc_catalog: dict,
        status: str = "DRAFT",
    ) -> dict: ...

    def get_by_catalog_id(self, catalog_id: str) -> dict | None: ...

    def get_by_job_id(self, job_id: str) -> dict | None: ...

    def update_catalog(self, catalog_id: str, products: list[dict]) -> dict: ...


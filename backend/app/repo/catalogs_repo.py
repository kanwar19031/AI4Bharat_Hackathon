from datetime import datetime, timezone
from uuid import uuid4


class CatalogsRepository:
    """Temporary in-memory repository.

    Swap this implementation with DynamoDB access once AWS wiring is added.
    """

    def __init__(self) -> None:
        self._catalogs_by_id: dict[str, dict] = {}
        self._catalog_id_by_job: dict[str, str] = {}

    def create_catalog(
        self,
        job_id: str,
        *,
        products: list[dict],
        ondc_catalog: dict,
        status: str = "DRAFT",
    ) -> dict:
        now = datetime.now(timezone.utc)
        catalog_id = str(uuid4())
        record = {
            "catalog_id": catalog_id,
            "job_id": job_id,
            "status": status,
            "products": products,
            "ondc_catalog": ondc_catalog,
            "created_at": now,
            "updated_at": now,
        }
        self._catalogs_by_id[catalog_id] = record
        self._catalog_id_by_job[job_id] = catalog_id
        return record

    def get_by_catalog_id(self, catalog_id: str) -> dict | None:
        return self._catalogs_by_id.get(catalog_id)

    def get_by_job_id(self, job_id: str) -> dict | None:
        catalog_id = self._catalog_id_by_job.get(job_id)
        if not catalog_id:
            return None
        return self._catalogs_by_id.get(catalog_id)

    def update_catalog(self, catalog_id: str, products: list[dict]) -> dict:
        catalog = self._catalogs_by_id[catalog_id]
        catalog["products"] = products
        catalog["updated_at"] = datetime.now(timezone.utc)
        return catalog


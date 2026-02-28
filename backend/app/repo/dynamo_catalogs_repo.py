from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from boto3.dynamodb.conditions import Key

from app.services.dynamo_service import DynamoService


class DynamoCatalogsRepository:
    def __init__(self, dynamo: DynamoService) -> None:
        self._dynamo = dynamo

    @property
    def _table(self):
        return self._dynamo.table(self._dynamo.settings.catalogs_table_name)

    def create_catalog(
        self,
        job_id: str,
        *,
        products: list[dict],
        ondc_catalog: dict,
        status: str = "DRAFT",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        catalog_id = str(uuid4())
        item = {
            "catalog_id": catalog_id,
            "job_id": job_id,
            "status": status,
            "products": products,
            "ondc_catalog": ondc_catalog,
            "created_at": now,
            "updated_at": now,
        }
        self._table.put_item(Item=item)
        return item

    def get_by_catalog_id(self, catalog_id: str) -> dict | None:
        resp = self._table.get_item(Key={"catalog_id": catalog_id})
        item = resp.get("Item")
        if not item:
            return None
        return self._dynamo.normalize_item(item)

    def get_by_job_id(self, job_id: str) -> dict | None:
        resp = self._table.query(
            IndexName="job_id-index",
            KeyConditionExpression=Key("job_id").eq(job_id),
            Limit=1,
        )
        items = resp.get("Items") or []
        if not items:
            return None
        return self._dynamo.normalize_item(items[0])

    def update_catalog(self, catalog_id: str, products: list[dict]) -> dict:
        resp = self._table.update_item(
            Key={"catalog_id": catalog_id},
            UpdateExpression="SET products = :p, updated_at = :u",
            ExpressionAttributeValues={
                ":p": products,
                ":u": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return self._dynamo.normalize_item(resp["Attributes"])


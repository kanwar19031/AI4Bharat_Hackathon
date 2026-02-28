from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from boto3.dynamodb.conditions import Key

from app.services.dynamo_service import DynamoService


class DynamoJobsRepository:
    def __init__(self, dynamo: DynamoService) -> None:
        self._dynamo = dynamo

    @property
    def _table(self):
        return self._dynamo.table(self._dynamo.settings.jobs_table_name)

    def create_job(self, video_id: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        job_id = str(uuid4())
        item = {
            "job_id": job_id,
            "video_id": video_id,
            "status": "UPLOADED",
            "product_count": 0,
            "error_message": None,
            "catalog_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self._table.put_item(Item=item)
        return item

    def get_by_video_id(self, video_id: str) -> dict | None:
        resp = self._table.query(
            IndexName="video_id-index",
            KeyConditionExpression=Key("video_id").eq(video_id),
            Limit=1,
        )
        items = resp.get("Items") or []
        if not items:
            return None
        return self._dynamo.normalize_item(items[0])

    def get_by_job_id(self, job_id: str) -> dict | None:
        resp = self._table.get_item(Key={"job_id": job_id})
        item = resp.get("Item")
        if not item:
            return None
        return self._dynamo.normalize_item(item)

    def update_status(
        self,
        job_id: str,
        status: str,
        *,
        product_count: int | None = None,
        error_message: str | None = None,
        catalog_id: str | None = None,
    ) -> dict:
        updates: list[str] = ["#s = :s", "updated_at = :u"]
        names = {"#s": "status"}
        values: dict[str, object] = {
            ":s": status,
            ":u": datetime.now(timezone.utc).isoformat(),
        }

        if product_count is not None:
            updates.append("product_count = :pc")
            values[":pc"] = int(product_count)
        if error_message is not None:
            updates.append("error_message = :em")
            values[":em"] = error_message
        if catalog_id is not None:
            updates.append("catalog_id = :cid")
            values[":cid"] = catalog_id

        resp = self._table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET " + ", ".join(updates),
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
        return self._dynamo.normalize_item(resp["Attributes"])


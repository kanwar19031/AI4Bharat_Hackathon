from __future__ import annotations

from decimal import Decimal
from typing import Any

import boto3
from botocore.config import Config

from app.config.settings import Settings


class DynamoService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._resource = None

    @property
    def resource(self):
        if self._resource is None:
            self._resource = boto3.resource(
                "dynamodb",
                region_name=self.settings.aws_region,
                config=Config(retries={"max_attempts": 5, "mode": "standard"}),
            )
        return self._resource

    def table(self, table_name: str):
        return self.resource.Table(table_name)

    def normalize_item(self, item: Any) -> Any:
        """
        DynamoDB returns Decimal for all numbers. Convert to int/float recursively
        so Pydantic responses and arithmetic behave predictably.
        """

        if isinstance(item, list):
            return [self.normalize_item(v) for v in item]
        if isinstance(item, dict):
            return {k: self.normalize_item(v) for k, v in item.items()}
        if isinstance(item, Decimal):
            if item % 1 == 0:
                return int(item)
            return float(item)
        return item

    def healthcheck(self) -> dict[str, Any]:
        # A lightweight call that exercises credentials + endpoint access.
        client = self.resource.meta.client
        resp = client.list_tables(Limit=5)
        return {
            "jobs_table": self.settings.jobs_table_name,
            "catalogs_table": self.settings.catalogs_table_name,
            "status": "ok",
            "tables_visible": resp.get("TableNames", []),
        }

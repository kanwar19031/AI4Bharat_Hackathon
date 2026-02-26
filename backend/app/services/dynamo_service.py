from app.config.settings import Settings


class DynamoService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def healthcheck(self) -> dict:
        # Placeholder for future boto3 DynamoDB client checks.
        return {
            "jobs_table": self.settings.jobs_table_name,
            "catalogs_table": self.settings.catalogs_table_name,
            "status": "not_configured",
        }


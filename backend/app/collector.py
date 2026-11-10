from datetime import datetime, timezone
from typing import List, Optional

import httpx

from .database import SessionLocal, Run


N8N_API_EXECUTIONS_ENDPOINT = "/api/v1/executions"
N8N_BASE_URL = "http://localhost:5678"


class Collector:
    """Collector interface for ingesting n8n run data into Flowwatch."""

    def __init__(self, base_url: str = N8N_BASE_URL, api_key: str = ""):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self.client.aclose()

    async def fetch_runs(self, limit: int = 100) -> List[dict]:
        """Fetch runs from the n8n API.

        This should be overridden by subclasses for different n8n API patterns.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    async def collect(self, limit: int = 100) -> int:
        """Fetch and ingest runs into the database. Returns the number of runs ingested."""
        runs = await self.fetch_runs(limit=limit)
        ingested = 0

        async with self.client:
            for run_data in runs:
                normalized = self.normalize(run_data)
                count = await self.upsert_run(normalized)
                ingested += count

        return ingested

    def normalize(self, run_data: dict) -> dict:
        """Normalize n8n API response to Flowwatch's standardized run record."""
        # Extract execution ID
        execution_id = run_data.get("id") or run_data.get("executionId") or ""

        # Extract workflow ID and name from the data
        workflow = run_data.get("workflow", {})
        workflow_id = workflow.get("id", "") if workflow else ""
        workflow_name = workflow.get("name", "") if workflow else ""

        # Extract status
        status = run_data.get("status", "unknown")

        # Extract timestamps
        started_at = run_data.get("startedAt") or run_data.get("startTime")
        finished_at = run_data.get("finishedAt") or run_data.get("endTime")

        # Parse datetime strings
        started_dt = self._parse_datetime(started_at)
        finished_dt = self._parse_datetime(finished_at)

        # Calculate duration
        duration = None
        if started_dt and finished_dt:
            duration = (finished_dt - started_dt).total_seconds()

        # Extract error message and failing node
        error_message = run_data.get("error") or run_data.get("errorMessage") or ""
        failing_node = run_data.get("errorWorkflow", {}).get("name") or ""
        failing_node_type = ""

        return {
            "instance": self.base_url,
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "status": status,
            "started_at": started_dt,
            "finished_at": finished_dt,
            "duration": duration,
            "error_message": error_message,
            "failing_node_name": failing_node,
            "failing_node_type": failing_node_type,
        }

    async def upsert_run(self, normalized: dict) -> int:
        """Upsert a normalized run record. Returns 1 if inserted/updated, 0 if skipped."""
        async with SessionLocal() as session:
            existing = (
                session.query(Run)
                .filter(Run.execution_id == normalized["execution_id"])
                .first()
            )

            if existing:
                # Already ingested - idempotent, skip
                return 0

            run = Run(
                instance=normalized.get("instance", ""),
                execution_id=normalized["execution_id"],
                workflow_id=normalized["workflow_id"],
                workflow_name=normalized["workflow_name"],
                status=normalized["status"],
                started_at=normalized["started_at"],
                finished_at=normalized["finished_at"],
                duration=normalized.get("duration"),
                error_message=normalized.get("error_message"),
                failing_node_name=normalized.get("failing_node_name"),
                failing_node_type=normalized.get("failing_node_type"),
            )

            session.add(run)
            await session.commit()
            return 1

    async def ping(self) -> bool:
        """Check if the n8n instance is reachable."""
        try:
            await self.client.get(f"{self.base_url}/health")
            return True
        except Exception:
            return False


class PollingCollector(Collector):
    """Polling collector that fetches runs from n8n on a scheduled interval."""

    async def fetch_runs(self, limit: int = 100) -> List[dict]:
        """Fetch runs from n8n REST API."""
        url = f"{self.base_url}{N8N_API_EXECUTIONS_ENDPOINT}"

        headers = {}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        response = await self.client.get(url, headers=headers, params={"limit": limit})
        response.raise_for_status()

        data = response.json()
        # n8n returns {executions: [...], ...}
        executions = data.get("executions", data.get("data", []))

        return executions if isinstance(executions, list) else [executions]


class WebhookCollector(Collector):
    """Webhook collector that receives failures from n8n Error Trigger workflow."""

    async def fetch_runs(self, limit: int = 100) -> List[dict]:
        """This collector expects runs to be posted via webhook.

        The webhook payload should contain normalized run data.
        Override fetch_runs to read from a queue or request body instead.
        return []  # Webhook mode typically doesn't poll
        """
        return []
"""
FastAPI backend exposing the RentMatrix AI triage pipeline via Swagger UI.

The pipeline already lives under `agent/`. We keep a single shared pipeline
instance (no randomness per request) and accept only a `description` input
for the triage agent as requested.
"""

import asyncio
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from langfuse import get_client
# Ensure project root is on path when running via `uvicorn api.app:app` or `python api/app.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if "" not in sys.path:
    sys.path.insert(0, "")

# Load environment variables (e.g., OpenAI/Langfuse keys)
load_dotenv()

from agent import DEFAULT_AGENT_CONFIG, TriagePipeline  # noqa: E402


class TriageRequest(BaseModel):
    """Request body containing only the maintenance description."""

    description: str = Field(
        ...,
        description="Raw maintenance issue description text",
        min_length=3,
    )


class TriageResponse(BaseModel):
    """Normalized API response from the triage pipeline."""

    triage: Dict[str, Any]
    priority: Dict[str, Any]
    explanation: Dict[str, Any]
    confidence: Dict[str, Any]
    sla: Dict[str, Any]


app = FastAPI(
    title="RentMatrix AI Triage API",
    description=(
        "Maintenance triage and priority scoring via RentMatrix AI agents. "
        "Includes 5 specialized agents: Triage Classifier, Priority Calculator, "
        "Explainer, Confidence Evaluator, and SLA Mapper."
    ),
    version="1.0.0",
)

# Enable wide CORS so the lightweight frontend can call the API locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrumentation and Langfuse setup (mirrors agent/main.py behavior)
OpenAIAgentsInstrumentor().instrument()
try:
    _langfuse_client = get_client()
    if not _langfuse_client.auth_check():  # type: ignore[attr-defined]
        _langfuse_client = None
except Exception:
    _langfuse_client = None

# Single shared pipeline instance to avoid per-request randomness/overhead
pipeline = TriagePipeline(
    triage_model=DEFAULT_AGENT_CONFIG.triage_model,
    confidence_model="gpt-5-mini",  # Agent 4: Confidence Evaluator
    use_deterministic_priority=True,  # Agent 2: Deterministic (instant)
    verbose=False,
)

# Predefined request template; only the description is filled from the user.
DEFAULT_REQUEST_TEMPLATE: Dict[str, Any] = {
    "test_id": "API_DEFAULT",
    "request": {
        "request_id": "api-req-001",
        "description": "",  # populated per request
        "images": [],
        "reported_at": "2024-12-09T23:30:00Z",
        "channel": "API",
        "category": "GENERAL",
    },
    "context": {
        "weather": {
            "temperature": 50,
            "condition": "clear",
            "forecast": "Clear skies",
            "alerts": [],
        },
        "tenant": {
            "age": 35,
            "is_elderly": False,
            "has_infant": False,
            "has_medical_condition": False,
            "is_pregnant": False,
            "occupant_count": 2,
            "tenure_months": 12,
        },
        "property": {
            "type": "Apartment",
            "age": 10,
            "floor": 2,
            "total_units": 24,
            "has_elevator": True,
        },
        "timing": {
            "day_of_week": "Monday",
            "hour": 12,
            "is_after_hours": False,
            "is_weekend": False,
            "is_holiday": False,
            "is_late_night": False,
        },
        "history": {
            "recent_issues_count": 0,
            "last_repair_date": None,
            "recurring_category": None,
            "previous_repair_failed": False,
            "avg_resolution_time_hours": None,
        },
        "similar_cases": [],
    },
}


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResponse)
async def run_triage(request: TriageRequest) -> Dict[str, Any]:
    """
    Run the complete 5-agent triage pipeline using the provided description.

    Pipeline Flow:
    1. Agent 1 (Triage Classifier): Classifies severity and trade category
    2. Agent 2 (Priority Calculator): Calculates numerical priority score
    3. Agent 3 (Explainer): Generates PM and tenant explanations
    4. Agent 4 (Confidence Evaluator): Assesses confidence and recommends routing
    5. Agent 5 (SLA Mapper): Maps priority to response/resolution deadlines

    Returns:
        - triage: Severity, trade, reasoning, and triage confidence
        - priority: Priority score (0-100) with applied modifiers
        - explanation: PM and tenant-facing explanations
        - confidence: Overall confidence score, routing decision, risk flags
        - sla: SLA tier, response deadline, resolution deadline, vendor tier

    The agent prompts are built inside the pipeline; we supply just the
    description payload to match the existing triage agent contract, while
    keeping the other fields predefined for stability.
    """
    request_payload = deepcopy(DEFAULT_REQUEST_TEMPLATE)
    request_payload["request"]["description"] = request.description

    try:
        result = await pipeline.run_with_data(request_payload)
        return result.to_dict()
    except Exception as exc:  # pragma: no cover - surfaced via HTTP 500
        raise HTTPException(status_code=500, detail="Pipeline execution failed") from exc


@app.on_event("shutdown")
async def _shutdown_langfuse() -> None:
    if _langfuse_client:
        try:
            _langfuse_client.flush()  # type: ignore[attr-defined]
        except Exception:
            pass


if __name__ == "__main__":
    # Enable `python api/app.py` to start the server directly.
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)


"""
FastAPI backend exposing the RentMatrix AI triage pipeline via Swagger UI.

The pipeline already lives under `agent/`. We keep a single shared pipeline
instance (no randomness per request) and accept only a `description` input
for the triage agent as requested.

Supports:
- Maintenance description input
- Location input (city name, address, or coordinates)
- Weather API integration for real-time weather context
- Simple round-robin vendor assignment (separate endpoint)
"""

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from langfuse import get_client

# Ensure project root is on path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if "" not in sys.path:
    sys.path.insert(0, "")

# Load environment variables
load_dotenv()

from agent import DEFAULT_AGENT_CONFIG, TriagePipeline  # noqa: E402
from agent.core_agents.vendor_assignment import assign_vendors_simple  # noqa: E402
from api.weather_service import get_weather_for_triage  # noqa: E402


# ==================== Request/Response Models ====================

class LocationInput(BaseModel):
    """Location input - either text query or coordinates."""
    query: Optional[str] = Field(None, description="City name, address, zipcode")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class TriageRequest(BaseModel):
    """Request body for maintenance triage."""
    description: str = Field(..., description="Maintenance issue description", min_length=3)
    location: Optional[LocationInput] = Field(None, description="Location for weather context")


class TriageResponse(BaseModel):
    """Response from triage pipeline (Agents 1-5)."""
    triage: Dict[str, Any]
    priority: Dict[str, Any]
    explanation: Dict[str, Any]
    confidence: Dict[str, Any]
    sla: Dict[str, Any]
    weather: Optional[Dict[str, Any]] = None


class VendorInput(BaseModel):
    """Single vendor input."""
    vendor_id: Optional[str] = None
    company_name: str
    primary_trade: str
    secondary_trades: Optional[List[str]] = []
    phone: Optional[str] = None
    email: Optional[str] = None
    # Accept any additional fields
    class Config:
        extra = "allow"


class VendorAssignmentRequest(BaseModel):
    """Request for vendor assignment."""
    trade: str = Field(..., description="Trade category (PLUMBING, ELECTRICAL, HVAC, etc.)")
    vendors: List[Dict[str, Any]] = Field(..., description="List of available vendors from PM")
    tenant_preferred_times: Optional[List[str]] = Field(
        None,
        description="Tenant's 3 preferred time slots (e.g., ['Monday 09:00-12:00', 'Wednesday 14:00-17:00'])"
    )


class AssignedVendor(BaseModel):
    """Single assigned vendor."""
    vendor: Dict[str, Any]
    role: str  # "primary" or "backup"
    matched_times: List[str] = []  # Which tenant times this vendor can match


class VendorAssignmentResponse(BaseModel):
    """Response from vendor assignment."""
    success: bool
    trade: str
    total_available: int = 0
    tenant_preferred_times: List[str] = []
    assigned_vendors: List[AssignedVendor] = []
    error: Optional[str] = None


# ==================== FastAPI App ====================

app = FastAPI(
    title="RentMatrix AI Triage API",
    description=(
        "Maintenance triage and priority scoring via RentMatrix AI agents.\n\n"
        "**Pipeline (Agents 1-5):** Triage -> Priority -> Explainer -> Confidence -> SLA\n\n"
        "**Vendor Assignment:** Separate endpoint with simple round-robin (no LLM)"
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrumentation
OpenAIAgentsInstrumentor().instrument()
try:
    _langfuse_client = get_client()
    if not _langfuse_client.auth_check():
        _langfuse_client = None
except Exception:
    _langfuse_client = None

# Shared pipeline instance (Agents 1-5 only)
pipeline = TriagePipeline(
    triage_model=DEFAULT_AGENT_CONFIG.triage_model,
    priority_model="gpt-5-mini",
    confidence_model="gpt-5-mini",
    verbose=False,
)

# Default request template
DEFAULT_REQUEST_TEMPLATE: Dict[str, Any] = {
    "test_id": "API_DEFAULT",
    "request": {
        "request_id": "api-req-001",
        "description": "",
        "images": [],
        "reported_at": "2024-12-09T23:30:00Z",
        "channel": "API",
        "category": "GENERAL",
    },
    "context": {
        "weather": {
            "temperature": 70,
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


def build_weather_context(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build weather context from API data."""
    alerts = weather_data.get("alerts", [])
    urgency = weather_data.get("urgency_modifiers", {})
    urgency_notes = urgency.get("weather_urgency_notes", [])
    if urgency_notes:
        alerts = alerts + urgency_notes

    return {
        "temperature": weather_data.get("temperature", 70),
        "temperature_c": weather_data.get("temperature_c", 21),
        "feelslike_f": weather_data.get("feelslike_f", 70),
        "feelslike_c": weather_data.get("feelslike_c", 21),
        "condition": weather_data.get("condition", "clear"),
        "humidity": weather_data.get("humidity", 50),
        "wind_mph": weather_data.get("wind_mph", 0),
        "forecast": weather_data.get("forecast", "Clear skies"),
        "alerts": alerts,
        "is_extreme_cold": urgency.get("is_extreme_cold", False),
        "is_extreme_heat": urgency.get("is_extreme_heat", False),
        "freeze_risk": urgency.get("freeze_risk", False),
    }


# ==================== Endpoints ====================

@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/weather")
async def get_weather(
    location: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None
) -> Dict[str, Any]:
    """Get weather for a location."""
    if not location and (lat is None or lon is None):
        raise HTTPException(400, "Provide 'location' or both 'lat' and 'lon'")

    try:
        return await get_weather_for_triage(location=location, latitude=lat, longitude=lon)
    except Exception as exc:
        raise HTTPException(500, f"Weather fetch failed: {str(exc)}") from exc


@app.post("/triage", response_model=TriageResponse)
async def run_triage(request: TriageRequest) -> Dict[str, Any]:
    """
    Run triage pipeline (Agents 1-5).

    **Flow:**
    1. Agent 1 (Triage): Classify severity + trade
    2. Agent 2 (Priority): Calculate priority score (0-100)
    3. Agent 3 (Explainer): Generate PM/tenant explanations
    4. Agent 4 (Confidence): Assess confidence + routing
    5. Agent 5 (SLA): Map to response/resolution deadlines

    **After triage:** Call `/assign-vendors` with the trade from response.
    """
    request_payload = deepcopy(DEFAULT_REQUEST_TEMPLATE)
    request_payload["request"]["description"] = request.description

    # Fetch weather if location provided
    weather_data = None
    if request.location:
        loc = request.location
        weather_data = await get_weather_for_triage(
            location=loc.query,
            latitude=loc.latitude,
            longitude=loc.longitude
        )
        request_payload["context"]["weather"] = build_weather_context(weather_data)

    try:
        result = await pipeline.run_with_data(request_payload)
        response = result.to_dict()

        if weather_data:
            response["weather"] = weather_data

        return response
    except Exception as exc:
        raise HTTPException(500, "Pipeline execution failed") from exc


@app.post("/assign-vendors", response_model=VendorAssignmentResponse)
async def assign_vendors(request: VendorAssignmentRequest) -> Dict[str, Any]:
    """
    Assign vendors using round-robin with time matching (no LLM).

    **Call this AFTER /triage** with the trade from triage response.

    **Input:**
    - `trade`: Trade category from triage (e.g., "PLUMBING")
    - `vendors`: List of available vendors with their availability
    - `tenant_preferred_times`: Tenant's 3 preferred time slots

    **Output:**
    - 3 vendors: 1 primary + 2 backups
    - Vendors with more matching times are prioritized
    - Round-robin ensures fair distribution

    **Example:**
    ```json
    {
      "trade": "PLUMBING",
      "tenant_preferred_times": [
        "Monday 09:00-12:00",
        "Wednesday 14:00-17:00",
        "Friday 10:00-15:00"
      ],
      "vendors": [
        {
          "vendor_id": "V1",
          "company_name": "QuickFix",
          "primary_trade": "PLUMBING",
          "availability": ["Monday 08:00-17:00", "Wednesday 08:00-17:00"]
        }
      ]
    }
    ```
    """
    if not request.vendors:
        return {
            "success": False,
            "trade": request.trade,
            "total_available": 0,
            "tenant_preferred_times": request.tenant_preferred_times or [],
            "assigned_vendors": [],
            "error": "No vendors provided"
        }

    result = assign_vendors_simple(
        trade=request.trade,
        vendors=request.vendors,
        tenant_times=request.tenant_preferred_times,
        count=3
    )

    return result


@app.on_event("shutdown")
async def _shutdown_langfuse() -> None:
    if _langfuse_client:
        try:
            _langfuse_client.flush()
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)

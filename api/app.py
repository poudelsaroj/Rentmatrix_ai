"""
FastAPI backend exposing the RentMatrix AI triage pipeline via Swagger UI.

The pipeline already lives under `agent/`. We keep a single shared pipeline
instance (no randomness per request) and accept only a `description` input
for the triage agent as requested.

Supports:
- Maintenance description input
- Location input (city name, address, or coordinates)
- Weather API integration for real-time weather context
"""

import asyncio
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

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
from agent.core_agents import VendorMatchingAgent  # noqa: E402
from agent.data import MOCK_VENDORS  # noqa: E402
from api.weather_service import get_weather_for_triage, WeatherAPIError  # noqa: E402


class LocationInput(BaseModel):
    """Location input - either text query or coordinates."""
    
    query: Optional[str] = Field(
        None,
        description="Location query (city name, address, zipcode, etc.)",
        examples=["New York", "10001", "Los Angeles, CA"]
    )
    latitude: Optional[float] = Field(
        None,
        description="Latitude coordinate (-90 to 90)",
        ge=-90,
        le=90
    )
    longitude: Optional[float] = Field(
        None,
        description="Longitude coordinate (-180 to 180)",
        ge=-180,
        le=180
    )


class TriageRequest(BaseModel):
    """Request body for maintenance triage with optional location and vendor matching."""

    description: str = Field(
        ...,
        description="Raw maintenance issue description text",
        min_length=3,
    )
    location: Optional[LocationInput] = Field(
        None,
        description="Location for weather context. Can be a text query or coordinates."
    )
    tenant_preferred_times: Optional[list[str]] = Field(
        None,
        description="Tenant's 3 preferred time slots for vendor visit (e.g., ['Monday 09:00-12:00', 'Wednesday 14:00-17:00', 'Friday 10:00-15:00'])",
        examples=[["Monday 09:00-12:00", "Wednesday 14:00-17:00", "Friday 10:00-15:00"]]
    )
    include_vendor_matching: bool = Field(
        False,
        description="Whether to include vendor matching recommendations in the response"
    )


class TriageResponse(BaseModel):
    """Normalized API response from the triage pipeline."""

    triage: Dict[str, Any]
    priority: Dict[str, Any]
    explanation: Dict[str, Any]
    confidence: Dict[str, Any]
    sla: Dict[str, Any]
    weather: Optional[Dict[str, Any]] = Field(
        None,
        description="Weather context used for triage (if location was provided)"
    )
    vendors: Optional[Dict[str, Any]] = Field(
        None,
        description="Vendor matching recommendations (if requested and tenant times provided)"
    )


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
    priority_model="gpt-5-mini",  # Agent 2: LLM-based Priority Calculator (default)
    confidence_model="gpt-5-mini",  # Agent 4: Confidence Evaluator
    verbose=False,
)

# Vendor matching agent (Agent 6)
vendor_agent = VendorMatchingAgent(model="gpt-5-mini", vendors=MOCK_VENDORS)

# Predefined request template; description and weather are populated per request.
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
            "temperature": 70,  # Default comfortable temperature
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
    """
    Build weather context for the request template from weather API data.
    
    Args:
        weather_data: Weather data from weather_service.get_weather_for_triage()
        
    Returns:
        Weather context dict matching the template format
    """
    alerts = weather_data.get("alerts", [])
    urgency = weather_data.get("urgency_modifiers", {})
    
    # Add urgency notes to alerts for AI context
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
    """
    Get current weather data for a location.
    
    Provide either:
    - `location`: City name, address, zipcode (e.g., "New York", "10001")
    - `lat` and `lon`: Coordinates (e.g., lat=40.7128, lon=-74.0060)
    
    Returns weather data including temperature, conditions, forecast, and alerts.
    Also includes urgency modifiers relevant for maintenance triage.
    """
    if not location and (lat is None or lon is None):
        raise HTTPException(
            status_code=400,
            detail="Provide either 'location' query parameter or both 'lat' and 'lon'"
        )
    
    try:
        weather_data = await get_weather_for_triage(
            location=location,
            latitude=lat,
            longitude=lon
        )
        return weather_data
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch weather data: {str(exc)}"
        ) from exc


@app.post("/triage", response_model=TriageResponse)
async def run_triage(request: TriageRequest) -> Dict[str, Any]:
    """
    Run the complete triage pipeline (5 agents) with optional vendor matching (Agent 6).

    Pipeline Flow:
    1. Agent 1 (Triage Classifier): Classifies severity and trade category
    2. Agent 2 (Priority Calculator): Calculates numerical priority score
    3. Agent 3 (Explainer): Generates PM and tenant explanations
    4. Agent 4 (Confidence Evaluator): Assesses confidence and recommends routing
    5. Agent 5 (SLA Mapper): Maps priority to response/resolution deadlines
    6. Agent 6 (Vendor Matching): Matches best vendors (optional)

    Request Body:
        - description: Maintenance issue description (required)
        - location: Optional location for weather context
            - query: City name, address, or zipcode
            - latitude/longitude: Coordinates
        - tenant_preferred_times: List of 3 preferred time slots (optional)
            - Example: ["Monday 09:00-12:00", "Wednesday 14:00-17:00", "Friday 10:00-15:00"]
        - include_vendor_matching: Enable vendor matching (default: false)

    Returns:
        - triage: Severity, trade, reasoning, and triage confidence
        - priority: Priority score (0-100) with applied modifiers
        - explanation: PM and tenant-facing explanations
        - confidence: Overall confidence score, routing decision, risk flags
        - sla: SLA tier, response deadline, resolution deadline, vendor tier
        - weather: Weather context used (if location provided)
        - vendors: Vendor recommendations (if requested with tenant times)

    The agent prompts are built inside the pipeline; we supply the
    description and weather context while keeping other fields predefined.
    """
    request_payload = deepcopy(DEFAULT_REQUEST_TEMPLATE)
    request_payload["request"]["description"] = request.description
    
    # Fetch weather data if location is provided
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
        
        # Include weather data in response if fetched
        if weather_data:
            response["weather"] = weather_data
        
        # Run vendor matching if requested and tenant times provided
        if request.include_vendor_matching and request.tenant_preferred_times:
            try:
                # Extract location for vendor matching
                location_dict = {}
                if request.location and request.location.query:
                    # Parse location query (simple approach)
                    parts = request.location.query.split(",")
                    location_dict["city"] = parts[0].strip() if len(parts) > 0 else "Boston"
                    location_dict["state"] = parts[1].strip() if len(parts) > 1 else "MA"
                    location_dict["zip_code"] = parts[2].strip() if len(parts) > 2 else "02101"
                else:
                    # Default location
                    location_dict = {"city": "Boston", "state": "MA", "zip_code": "02101"}
                
                # Build vendor matching prompt
                vendor_prompt = vendor_agent.build_prompt(
                    triage_output=result.triage_parsed or {},
                    priority_output=result.priority_parsed or {},
                    request_data=request_payload,
                    tenant_preferred_times=request.tenant_preferred_times,
                    property_location=location_dict
                )
                
                # Run vendor matching
                vendor_result = await vendor_agent.run(vendor_prompt)
                
                # Parse vendor matching output
                import json
                try:
                    vendor_data = json.loads(vendor_result.final_output)
                    response["vendors"] = vendor_data
                except json.JSONDecodeError:
                    response["vendors"] = {
                        "error": "Failed to parse vendor matching output",
                        "raw_output": vendor_result.final_output
                    }
            except Exception as vendor_exc:
                response["vendors"] = {
                    "error": f"Vendor matching failed: {str(vendor_exc)}"
                }
        
        return response
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


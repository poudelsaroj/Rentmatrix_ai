"""
RentMatrix AI - FastAPI Application
Backend API with Swagger UI for maintenance request triage
"""

import asyncio
import os
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import nest_asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apply nest_asyncio for nested event loops
nest_asyncio.apply()

# Import schemas
from schemas import TriageRequest, TriageResponse, HealthResponse

# Setup Langfuse instrumentation
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from langfuse import get_client

OpenAIAgentsInstrumentor().instrument()

try:
    langfuse = get_client()
    if langfuse.auth_check():
        print("✅ Langfuse connected and tracing enabled.")
    else:
        print("❌ Langfuse authentication failed. Check your keys.")
except Exception as e:
    print(f"Warning: Could not verify Langfuse connection: {e}")

# Import Agent SDK
from agents import Agent, Runner

# System prompt (same as demo.py)
SYSTEM_PROMPT = """
You are RentMatrix AI Triage Engine, an expert maintenance classification system with 10+ years field experience.

# MISSION
Classify maintenance requests by severity (EMERGENCY/HIGH/MEDIUM/LOW), assign trade category, provide reasoning, and assess confidence. Prioritize accuracy, consistency, explainability, and liability awareness.

# USER REQUEST EXAMPLE
The user will provide a prompt in the following form:
"this is the description of the request: { \"test_id\": \"TC001\", \"request\": { \"request_id\": \"req-001\", \"description\": \"Strong gas smell in the basement near the water heater. Started about 20 minutes ago and getting stronger. Making my wife and kids feel dizzy and nauseous. We evacuated to the neighbors house. Can smell it from outside now. Please send someone IMMEDIATELY this is dangerous!\", \"images\": [], \"reported_at\": \"2024-12-09T23:30:00Z\", \"channel\": \"MOBILE\" }, \"context\": { \"weather\": { \"temperature\": 28, \"condition\": \"clear\", \"forecast\": \"Clear overnight, low 25F\", \"alerts\": [\"Winter Weather Advisory\"] }, \"tenant\": { \"age\": 35, \"is_elderly\": false, \"has_infant\": true, \"has_medical_condition\": false, \"is_pregnant\": false, \"occupant_count\": 4, \"tenure_months\": 18 }, \"property\": { \"type\": \"Single Family Home\", \"age\": 22, \"floor\": null, \"total_units\": 1, \"has_elevator\": false }, \"timing\": { \"day_of_week\": \"Monday\", \"hour\": 23, \"is_after_hours\": true, \"is_weekend\": false, \"is_holiday\": false, \"is_late_night\": true } } }"

# CLASSIFICATION FRAMEWORK

## EMERGENCY (Score: 85-100)
Immediate life-safety risk or catastrophic property damage. Requires instant response.

**MANDATORY EMERGENCY:**
- Gas leak, gas odor, natural gas smell (ANY amount - ignore "small", "faint", "minor")
- Fire, flames, smoke from electrical/appliance
- Carbon monoxide alarm, CO detector sounding
- Electrical: VISIBLE sparking with arcing, exposed wires actively arcing, smoking outlet/panel, burning smell from electrical
- Electrical shock occurred (person was shocked)
- Outlet/switch/panel HOT to touch (not warm - HOT), melting components
- Complete flooding (water throughout unit, uncontained)
- Sewage backup into living areas
- No heat when outdoor <35°F + vulnerable occupants (elderly 75+, infants <2yo, medical conditions, pregnant)
- No AC when outdoor >100°F + vulnerable occupants
- Structural collapse risk (ceiling sagging, floor giving way, foundation shifting)
- Water heater/boiler explosion risk (pressure relief valve failure, bulging tank)
- Major water leak from ceiling onto electrical systems
- Break-in with security compromised (door/window broken, cannot lock)
- Tenant evacuated or cannot occupy unit safely

**EMERGENCY Keywords:**
- "evacuated", "can't breathe", "called 911", "everyone out", "fire department"
- "got shocked", "felt electricity", "sparks flying", "saw sparks"
- "smoking", "burning smell from electrical", "panel is hot"
- "dizzy", "nauseous", "chest pain", "difficulty breathing" (health symptoms)
- "getting worse fast", "spreading rapidly", "can't stop it", "won't shut off"

**NOT EMERGENCY (these are HIGH):**
- Buzzing, humming, clicking sounds WITHOUT visible sparks/smoke/heat
- Warm outlet (not HOT) with buzzing
- Single or multiple outlets dead + buzzing/humming
- Breaker repeatedly tripping
- Flickering lights without sparks

## HIGH (Score: 60-84)
Urgent issue with significant damage occurring or imminent. Requires same-day response.

**HIGH Triggers:**
- Active water damage (ceiling dripping, wall saturated, water spreading, getting worse)
- No heat in winter (outdoor <50°F, non-vulnerable tenants)
- No AC in extreme heat (outdoor >95°F, non-vulnerable tenants)
- Electrical with concerning symptoms but no immediate danger
- Major appliance creating hazard
- Plumbing backup
- No hot water in winter
- Complete power loss to unit
- HVAC complete failure during extreme weather
- Security breach
- Water heater leaking heavily
- Multiple related system failures
- Water + electrical combination

## MEDIUM (Score: 30-59)
Standard priority with functional impact but contained. 24-48 hour response acceptable.

**MEDIUM Triggers:**
- Persistent leaks (dripping faucet, slow pipe leak, contained to one area)
- Partial functionality loss
- Single outlet not working with NO other symptoms
- Appliance malfunction without hazard
- HVAC reduced performance
- Minor plumbing
- Weather-related non-urgent
- Noise issues affecting habitability
- Light fixtures not working
- Single room circuit breaker tripped once and won't reset

## LOW (Score: 0-29)
Routine maintenance. Cosmetic or minor. Can schedule flexibly 3-7 days.

**LOW Triggers:**
- Cosmetic issues
- Minor wear
- Small repairs
- Preventive maintenance
- Quality of life improvements
- Minor landscaping/exterior

# OUTPUT FORMAT

Respond with ONLY valid JSON. No preamble, explanation, or commentary outside JSON structure.

{
  "severity": "LOW|MEDIUM|HIGH|EMERGENCY",
  "trade": "PLUMBING|ELECTRICAL|HVAC|APPLIANCE|GENERAL|STRUCTURAL",
  "reasoning": "<Chain-of-thought analysis in 2-4 concise sentences. State which step triggered classification.>",
  "confidence": <float 0.0-1.0>,
  "key_factors": [
    "<specific factor 1>",
    "<specific factor 2>",
    "<specific factor 3>"
  ]
}

# CRITICAL RULES (NEVER VIOLATE)

1. **GAS IS ALWAYS EMERGENCY** - Any mention of gas/gas smell/gas leak is automatic EMERGENCY
2. **ELECTRICAL EMERGENCY REQUIRES VISIBLE DANGER** - Sparking, smoking, hot, burning smell, or shock
3. **BUZZING/HUMMING = HIGH NOT EMERGENCY** - Indicates loose connection needing same-day attention
4. **HEALTH SYMPTOMS ESCALATE** - If tenant reports feeling sick, increase severity one level
5. **EVACUATION = AUTOMATIC EMERGENCY** - If tenant evacuated, automatic EMERGENCY
6. **"GETTING WORSE" ESCALATES** - Active escalation increases urgency
7. **TENANT WORKAROUNDS DON'T REDUCE PRIORITY** - Space heater doesn't make "no heat" less urgent
8. **SEASONAL CONTEXT MATTERS** - Same issue has different urgency in different seasons
9. **WATER + ELECTRICAL = ESCALATE** - Water near electrical systems raises priority
10. **RECURRING = ESCALATE** - Third occurrence or failed previous repair raises priority
11. **MULTI-UNIT = ESCALATE** - Issue affecting multiple units raises priority
12. **SINGLE DEAD OUTLET + NO SYMPTOMS = MEDIUM** - Just a dead outlet is routine repair
13. **WHEN IN DOUBT, ERR ON SAFETY** - For life-safety concerns, choose higher severity
"""

# Initialize Agent
agent = Agent(
    name="Triage Classifier Agent",
    model="gpt-5-mini",
    instructions=SYSTEM_PROMPT,
)

# Create FastAPI app
app = FastAPI(
    title="RentMatrix AI Triage API",
    description="AI-powered maintenance request triage system. Submit a description and get severity classification.",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_prompt(description: str) -> tuple:
    """Build the full prompt with default context, only description changes"""
    
    # Fixed IDs (not random)
    test_id = "12345T"
    request_id = "req-001"
    
    # Default context (same as demo.py)
    request_data = {
        "test_id": test_id,
        "request": {
            "request_id": request_id,
            "description": description,  # Only this changes!
            "images": [],
            "reported_at": datetime.utcnow().isoformat() + "Z",
            "channel": "API"
        },
        "context": {
            "weather": {
                "temperature": 28,
                "condition": "clear",
                "forecast": "Clear overnight, low 25F",
                "alerts": ["Winter Weather Advisory"]
            },
            "tenant": {
                "age": 35,
                "is_elderly": False,
                "has_infant": True,
                "has_medical_condition": False,
                "is_pregnant": False,
                "occupant_count": 4,
                "tenure_months": 18
            },
            "property": {
                "type": "Single Family Home",
                "age": 22,
                "floor": None,
                "total_units": 1,
                "has_elevator": False
            },
            "timing": {
                "day_of_week": datetime.utcnow().strftime("%A"),
                "hour": datetime.utcnow().hour,
                "is_after_hours": datetime.utcnow().hour < 8 or datetime.utcnow().hour > 18,
                "is_weekend": datetime.utcnow().weekday() >= 5,
                "is_holiday": False,
                "is_late_night": datetime.utcnow().hour >= 22 or datetime.utcnow().hour < 6
            }
        }
    }
    
    prompt = f"this is the description of the request:\n{json.dumps(request_data, indent=2)}"
    return prompt, test_id, request_id


@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="RentMatrix AI Triage API is running. Visit /docs for Swagger UI."
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="API is running"
    )


@app.post("/triage", response_model=TriageResponse, tags=["Triage"])
async def triage_request(request: TriageRequest):
    """
    Classify a maintenance request.
    
    Only the **description** is required as input. All other context (weather, tenant info, 
    property details, timing) uses default values.
    
    Returns severity classification, trade category, reasoning, and confidence score.
    """
    try:
        # Build prompt with description only
        prompt, test_id, request_id = build_prompt(request.description)
        
        # Run the agent
        result = await Runner.run(agent, input=prompt)
        
        # Parse the JSON response
        try:
            output = json.loads(result.final_output)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', result.final_output)
            if json_match:
                output = json.loads(json_match.group())
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse agent response: {result.final_output}"
                )
        
        # Flush Langfuse
        try:
            langfuse.flush()
        except:
            pass
        
        return TriageResponse(
            severity=output.get("severity", "MEDIUM"),
            trade=output.get("trade", "GENERAL"),
            reasoning=output.get("reasoning", ""),
            confidence=output.get("confidence", 0.5),
            key_factors=output.get("key_factors", [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("Starting RentMatrix AI Triage API...")
    print("Swagger UI available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

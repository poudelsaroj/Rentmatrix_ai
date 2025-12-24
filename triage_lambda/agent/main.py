"""
Main entry point for the RentMatrix AI Triage Pipeline.

This script demonstrates the pipeline with a sample maintenance request.
"""

import asyncio
import os
import sys
import nest_asyncio
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Apply nest_asyncio for Jupyter/nested event loops
nest_asyncio.apply()

# Setup tracing
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from langfuse import get_client

OpenAIAgentsInstrumentor().instrument()

# Verify Langfuse connection
try:
    langfuse = get_client()
    if langfuse.auth_check():
        print("✅ Langfuse connected and tracing enabled.")
    else:
        print("❌ Langfuse authentication failed. Check your keys.")
except Exception as e:
    print(f"Warning: Could not verify Langfuse connection: {e}")
    langfuse = None

# Import pipeline
from agent.pipeline import TriagePipeline


# Sample test data
SAMPLE_REQUEST = """
this is the description of the request:
{
  "test_id": "TC001",
  "request": {
    "request_id": "req-001",
    "description": "Strong gas smell in the basement near the water heater. Started about 20 minutes ago and getting stronger. Making my wife and kids feel dizzy and nauseous. We evacuated to the neighbors house. Can smell it from outside now. Please send someone IMMEDIATELY this is dangerous!",
    "images": [],
    "reported_at": "2024-12-09T23:30:00Z",
    "channel": "MOBILE"
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
      "is_elderly": false,
      "has_infant": true,
      "has_medical_condition": false,
      "is_pregnant": false,
      "occupant_count": 4,
      "tenure_months": 18
    },
    "property": {
      "type": "Single Family Home",
      "age": 22,
      "floor": null,
      "total_units": 1,
      "has_elevator": false
    },
    "timing": {
      "day_of_week": "Monday",
      "hour": 23,
      "is_after_hours": true,
      "is_weekend": false,
      "is_holiday": false,
      "is_late_night": true
    }
  }
}
"""


async def main():
    """Run the triage pipeline with sample data."""
    
    # Initialize pipeline
    pipeline = TriagePipeline(
        triage_model="gpt-5-mini",
        priority_model="gpt-5-mini",
        verbose=True
    )
    
    # Run pipeline
    result = await pipeline.run(SAMPLE_REQUEST)
    
    # Flush Langfuse traces
    if langfuse:
        langfuse.flush()
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

"""
Comprehensive Demo of RentMatrix AI Triage System with All 4 Agents

This demo shows the complete pipeline:
Agent 1: Triage Classifier
Agent 2: Priority Calculator
Agent 3: Explainer
Agent 4: Confidence Evaluator
"""

import asyncio
import json
import sys
import os
import nest_asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv()
nest_asyncio.apply()

# Setup tracing
from openinference.instrumentation.openai_agents import OpenAIAgentsIntrumentor
from langfuse import get_client

OpenAIAgentsIntrumentor().instrument()

try:
    langfuse = get_client()
    if langfuse.auth_check():
        print("✅ Langfuse connected and tracing enabled.\n")
    else:
        print("❌ Langfuse authentication failed. Check your keys.\n")
except Exception as e:
    print(f"⚠️  Warning: Could not verify Langfuse connection: {e}\n")
    langfuse = None

# Import pipeline
from agent.pipeline import TriagePipeline


# ============================================================================
# TEST CASES
# ============================================================================

TEST_CASES = [
    {
        "name": "EMERGENCY: Gas Leak with Evacuation",
        "request": """
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
    },
    {
        "name": "HIGH: Active Water Damage",
        "request": """
this is the description of the request:
{
  "test_id": "TC002",
  "request": {
    "request_id": "req-002",
    "description": "Toilet overflowed about 30 minutes ago. Water is spreading to the bedroom now. I tried to stop it but can't. The floor is soaking wet and it's still leaking. This is getting worse!",
    "images": ["image1.jpg", "image2.jpg"],
    "reported_at": "2024-12-09T22:00:00Z",
    "channel": "WEB"
  },
  "context": {
    "weather": {
      "temperature": 45,
      "condition": "clear",
      "forecast": "Clear",
      "alerts": []
    },
    "tenant": {
      "age": 78,
      "is_elderly": true,
      "has_infant": false,
      "has_medical_condition": false,
      "is_pregnant": false,
      "occupant_count": 1,
      "tenure_months": 36
    },
    "property": {
      "type": "Apartment",
      "age": 15,
      "floor": 3,
      "total_units": 20,
      "has_elevator": true
    },
    "timing": {
      "day_of_week": "Saturday",
      "hour": 22,
      "is_after_hours": true,
      "is_weekend": true,
      "is_holiday": false,
      "is_late_night": false
    }
  }
}
"""
    },
    {
        "name": "MEDIUM: Ambiguous Electrical Issue",
        "request": """
this is the description of the request:
{
  "test_id": "TC003",
  "request": {
    "request_id": "req-003",
    "description": "One of the outlets in the kitchen isn't working. Might be making a slight buzzing sound, not sure. Other outlets seem fine. Not urgent but would like someone to check it out.",
    "images": [],
    "reported_at": "2024-12-09T14:00:00Z",
    "channel": "EMAIL"
  },
  "context": {
    "weather": {
      "temperature": 72,
      "condition": "sunny",
      "forecast": "Clear and sunny",
      "alerts": []
    },
    "tenant": {
      "age": 32,
      "is_elderly": false,
      "has_infant": false,
      "has_medical_condition": false,
      "is_pregnant": false,
      "occupant_count": 2,
      "tenure_months": 12
    },
    "property": {
      "type": "Apartment",
      "age": 8,
      "floor": 2,
      "total_units": 50,
      "has_elevator": true
    },
    "timing": {
      "day_of_week": "Tuesday",
      "hour": 14,
      "is_after_hours": false,
      "is_weekend": false,
      "is_holiday": false,
      "is_late_night": false
    }
  }
}
"""
    }
]


async def run_demo():
    """Run comprehensive demo of all agents."""
    
    print("=" * 80)
    print("RENTMATRIX AI TRIAGE SYSTEM - COMPLETE DEMO")
    print("Demonstrating All 4 Agents")
    print("=" * 80)
    print()
    
    # Initialize pipeline
    pipeline = TriagePipeline(
        triage_model="gpt-5-mini",
        priority_model="gpt-5-mini",
        explainer_model="gpt-5-mini",
        confidence_model="gpt-5-mini",
        verbose=True
    )
    
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print("\n" + "=" * 80)
        print(f"TEST CASE {i}/{len(TEST_CASES)}: {test_case['name']}")
        print("=" * 80)
        
        try:
            # Run pipeline
            result = await pipeline.run(test_case['request'])
            
            # Store result
            results.append({
                "test_case": test_case['name'],
                "result": result.to_dict()
            })
            
            print("\n" + "-" * 80)
            print("COMPLETE RESULT (JSON):")
            print("-" * 80)
            print(result.to_json())
            
        except Exception as e:
            print(f"\n❌ Error in test case: {e}")
            import traceback
            traceback.print_exc()
        
        # Small delay between test cases
        if i < len(TEST_CASES):
            await asyncio.sleep(2)
    
    # Flush Langfuse traces
    if langfuse:
        langfuse.flush()
    
    # Print summary
    print("\n" + "=" * 80)
    print("DEMO COMPLETE - SUMMARY OF ALL RESULTS")
    print("=" * 80)
    
    for i, res in enumerate(results, 1):
        print(f"\n{i}. {res['test_case']}")
        print("-" * 40)
        
        data = res['result']
        
        if 'triage' in data and isinstance(data['triage'], dict):
            triage = data['triage']
            print(f"   Severity: {triage.get('severity', 'N/A')}")
            print(f"   Trade: {triage.get('trade', 'N/A')}")
        
        if 'priority' in data and isinstance(data['priority'], dict):
            priority = data['priority']
            print(f"   Priority Score: {priority.get('priority_score', 'N/A')}/100")
        
        if 'confidence' in data and isinstance(data['confidence'], dict):
            confidence = data['confidence']
            print(f"   Confidence: {confidence.get('confidence', 'N/A')}")
            print(f"   Routing: {confidence.get('routing', 'N/A')}")
            risk_flags = confidence.get('risk_flags', [])
            if risk_flags:
                print(f"   Risk Flags: {', '.join(risk_flags)}")
    
    print("\n" + "=" * 80)
    print("✅ All test cases completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())

import requests
import os
from dotenv import load_dotenv
import asyncio
import sys
from pathlib import Path
import json
import re

# Add parent directory to path to import agent modules
sys.path.append(str(Path(__file__).parent.parent))

from agent.core_agents.triage_agent import TriageAgent
from agent.core_agents.priority_agent import PriorityAgent
from agent.core_agents.explainer_agent import ExplainerAgent
from agent.core_agents.confidence_agent import ConfidenceAgent


load_dotenv()

# Configuration
AUTH0_DOMAIN = os.getenv("Auth0Management__Domain")
CLIENT_ID = os.getenv("Auth0Management__ClientId")
CLIENT_SECRET = os.getenv("Auth0Management__ClientSecret")
AUDIENCE = os.getenv("Auth0Management__Audience")   

MAINTENANCE_ID = "8ec5ee0b-1952-4c66-8773-55baf33faba1"
BACKEND_URL = f"https://3kiiv9aysj.execute-api.us-west-2.amazonaws.com/api/v1.0/maintenance/{MAINTENANCE_ID}/triage"


# Get Auth0 token
token_url = f"{AUTH0_DOMAIN}/oauth/token"
token_payload = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "audience": AUDIENCE,
    "grant_type": "client_credentials"
}

def extract_result_text(result):
    """Extract text from RunResult object"""
    if hasattr(result, 'data'):
        return str(result.data)
    elif hasattr(result, 'content'):
        return str(result.content)
    elif hasattr(result, 'text'):
        return str(result.text)
    else:
        return str(result)


def parse_json_result(result_text, search_key="severity"):
    """Parse JSON from result text with fallback regex"""
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        # Try to find JSON embedded in RunResult text
        # Look for the pattern: Final output (str): followed by JSON
        if 'Final output (str):' in result_text:
            # Extract everything after "Final output (str):"
            start_idx = result_text.find('Final output (str):') + len('Final output (str):')
            remainder = result_text[start_idx:]
            
            # Find the JSON object - look for opening brace
            json_start = remainder.find('{')
            if json_start != -1:
                # Extract from first { to the matching }
                # Count braces to find the complete JSON
                brace_count = 0
                json_end = -1
                for i in range(json_start, len(remainder)):
                    if remainder[i] == '{':
                        brace_count += 1
                    elif remainder[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end != -1:
                    json_str = remainder[json_start:json_end]
                    # Clean up excessive whitespace and indentation
                    json_str = re.sub(r'\n\s+', ' ', json_str)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
        
        # Fallback: try to find any JSON with the search key
        json_match = re.search(r'\{[^{}]*"' + search_key + r'"[^{}]*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"raw_output": result_text}


def snake_to_camel(snake_str):
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def convert_keys_to_camel(obj):
    """Recursively convert all dictionary keys from snake_case to camelCase"""
    if isinstance(obj, dict):
        return {snake_to_camel(k): convert_keys_to_camel(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_camel(item) for item in obj]
    else:
        return obj


async def main():
    token_response = requests.post(token_url, json=token_payload)
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    print(f"Token obtained: {access_token[:30]}...")

    # Make GET request
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(BACKEND_URL, headers=headers)
    response.raise_for_status()

    print(f"\nResponse: {response.json()}")

    # Send to triage agent
    print("\n" + "="*60)
    print("Processing with Triage Agent...")
    print("="*60 + "\n")

    triage_agent = TriageAgent()
    prompt = triage_agent.build_prompt(response.json())

    # Run the agent
    triage_result = await triage_agent.run(prompt)
    
    # Extract and parse triage result
    triage_text = extract_result_text(triage_result)
    triage_json = parse_json_result(triage_text, "severity")
    
    # Print the triage JSON
    print(json.dumps(triage_json, indent=2))

    # Send to priority agent
    print("\n" + "="*60)
    print("Processing with Priority Agent...")
    print("="*60 + "\n")
    
    priority_agent = PriorityAgent()
    prompt = priority_agent.build_prompt(triage_text, response.json())

    # Run the agent
    priority_result_raw = await priority_agent.run(prompt)
    priority_text = extract_result_text(priority_result_raw)
    priority_json = parse_json_result(priority_text, "priority_score")

    print("Priority Agent Final Response:")
    print("="*60)
    print(json.dumps(priority_json, indent=2))
    print("="*60)

    #send to explainer agent
    print("\n" + "="*60)
    print("Processing with Explainer Agent...")
    print("="*60 + "\n")
    
    explainer_agent = ExplainerAgent()
    prompt = explainer_agent.build_prompt(triage_text, priority_text, response.json())
    
    # Run the agent
    explainer_result_raw = await explainer_agent.run(prompt)
    explainer_text = extract_result_text(explainer_result_raw)
    explainer_json = parse_json_result(explainer_text, "explanation")

    print("Explainer Agent Final Response:")
    print("="*60)
    print(json.dumps(explainer_json, indent=2))
    print("="*60)

    #send to confidence agent
    print("\n" + "="*60)
    print("Processing with Confidence Agent...")
    print("="*60 + "\n")
    
    confidence_agent = ConfidenceAgent()
    prompt = confidence_agent.build_prompt(triage_text, priority_text, explainer_text, response.json())
    
    # Run the agent
    confidence_result_raw = await confidence_agent.run(prompt)
    confidence_text = extract_result_text(confidence_result_raw)
    confidence_json = parse_json_result(confidence_text, "confidence")

    print("Confidence Agent Final Response:")
    print("="*60)
    print(json.dumps(confidence_json, indent=2))
    print("="*60)

    # Format final result according to specification
    # Wrap in "dto" as required by backend
    final_result = {
        "dto": {
            "triage": convert_keys_to_camel({
                "severity": triage_json.get("severity"),
                "trade": triage_json.get("trade"),
                "reasoning": triage_json.get("reasoning"),
                "confidence": triage_json.get("confidence", 0),
                "key_factors": triage_json.get("key_factors", [])
            }),
            "priority": convert_keys_to_camel({
                "priority_score": priority_json.get("priority_score", 0),
                "severity": priority_json.get("severity"),
                "base_hazard": priority_json.get("base_hazard", 0),
                "combined_hazard": priority_json.get("combined_hazard", 0),
                "applied_factors": priority_json.get("applied_factors", []),
                "applied_interactions": priority_json.get("applied_interactions", []),
                "calculation_trace": priority_json.get("calculation_trace"),
                "confidence": priority_json.get("confidence", 0)
            }),
            "explanation": convert_keys_to_camel({
                "pm_explanation": explainer_json.get("pm_explanation"),
                "tenant_explanation": explainer_json.get("tenant_explanation")
            }),
            "confidence": convert_keys_to_camel({
                "confidence": confidence_json.get("confidence", 0),
                "routing": confidence_json.get("routing"),
                "confidence_factors": confidence_json.get("confidence_factors", []),
                "risk_flags": confidence_json.get("risk_flags", []),
                "recommendation": confidence_json.get("recommendation")
            }),
            "sla": {
                "tier": None,
                "responseDeadline": None,
                "resolutionDeadline": None,
                "responseHours": 0,
                "resolutionHours": 0,
                "businessHoursOnly": False,
                "vendorTier": None
            },
            "weather": {
                "temperature": 0,
                "temperatureC": 0,
                "feelsLikeF": 0,
                "feelsLikeC": 0,
                "condition": None,
                "humidity": 0,
                "windMph": 0,
                "forecast": None,
                "alerts": [],
                "isExtremeCold": False,
                "isExtremeHeat": False,
                "freezeRisk": False
            }
        }
    }

    print("\n" + "="*60)
    print("FINAL COMBINED RESULT")
    print("="*60)
    print(json.dumps(final_result, indent=2))
    
    # Return the final result for use in API endpoints
    return final_result

if __name__ == "__main__":
    # Run and store the result
    result = asyncio.run(main())
    
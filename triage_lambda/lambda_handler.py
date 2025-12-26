"""
AWS Lambda Handler for RentMatrix AI Triage Engine
Processes maintenance requests and returns triage analysis
"""

import json
import os
import asyncio
from typing import Dict, Any
from datetime import datetime
import requests
from dotenv import load_dotenv
from dateutil import parser as date_parser

from agent.core_agents.triage_agent import TriageAgent
from agent.core_agents.priority_agent import PriorityAgent
from agent.core_agents.explainer_agent import ExplainerAgent
from agent.core_agents.confidence_agent import ConfidenceAgent
from agent.core_agents.sla_mapper_agent import SLAMapperAgent

# Load environment variables
load_dotenv()

# Helper functions (from triage_processor.py)
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
    import re
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        # Try to find JSON embedded in RunResult text
        if 'Final output (str):' in result_text:
            start_idx = result_text.find('Final output (str):') + len('Final output (str):')
            remainder = result_text[start_idx:]
            
            json_start = remainder.find('{')
            if json_start != -1:
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
                    json_str = re.sub(r'\n\s+', ' ', json_str)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
        
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


async def process_triage(maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process maintenance request through all triage agents
    
    Args:
        maintenance_data: The maintenance request data from backend
        
    Returns:
        Complete triage analysis in dto format
    """
    
    # Triage Agent
    triage_agent = TriageAgent()
    triage_prompt = triage_agent.build_prompt(maintenance_data)
    triage_result_raw = await triage_agent.run(triage_prompt)
    triage_text = extract_result_text(triage_result_raw)
    triage_json = parse_json_result(triage_text, "severity")
    
    # Priority Agent
    priority_agent = PriorityAgent()
    priority_prompt = priority_agent.build_prompt(triage_text, maintenance_data)
    priority_result_raw = await priority_agent.run(priority_prompt)
    priority_text = extract_result_text(priority_result_raw)
    priority_json = parse_json_result(priority_text, "priority_score")
    
    # Explainer Agent
    explainer_agent = ExplainerAgent()
    explainer_prompt = explainer_agent.build_prompt(triage_text, priority_text, maintenance_data)
    explainer_result_raw = await explainer_agent.run(explainer_prompt)
    explainer_text = extract_result_text(explainer_result_raw)
    explainer_json = parse_json_result(explainer_text, "explanation")
    
    # Confidence Agent
    confidence_agent = ConfidenceAgent()
    confidence_prompt = confidence_agent.build_prompt(triage_text, priority_text, explainer_text, maintenance_data)
    confidence_result_raw = await confidence_agent.run(confidence_prompt)
    confidence_text = extract_result_text(confidence_result_raw)
    confidence_json = parse_json_result(confidence_text, "confidence")
    
    # SLA Mapper Agent (deterministic, no LLM)
    sla_mapper_agent = SLAMapperAgent()
    priority_score = int(priority_json.get("priority_score", 0))
    
    # Get submission time from maintenance data or use current time
    from dateutil import parser as date_parser
    if maintenance_data.get("request", {}).get("reportedAt"):
        submission_time = date_parser.isoparse(maintenance_data["request"]["reportedAt"])
    else:
        submission_time = datetime.utcnow()
    
    # Run SLA calculation (returns SLAResult object)
    sla_result = sla_mapper_agent.run(priority_score, submission_time)
    sla_mapper_json = sla_result.to_dict()
    
    # Format final result
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
            "sla": convert_keys_to_camel({
                "tier": sla_mapper_json.get("tier"),
                "response_deadline": sla_mapper_json.get("response_deadline"),
                "resolution_deadline": sla_mapper_json.get("resolution_deadline"),
                "response_hours": sla_mapper_json.get("response_hours", 0),
                "resolution_hours": sla_mapper_json.get("resolution_hours", 0),
                "business_hours_only": sla_mapper_json.get("business_hours_only", False),
                "vendor_tier": sla_mapper_json.get("vendor_tier")
            }),
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
    
    return final_result


def lambda_handler(event, context):
    """
    AWS Lambda handler function
    
    Expected event format:
    {
        "maintenanceId": "uuid",
        OR
        "maintenanceData": { ... full data ... }
    }
    """
    
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Check if maintenance data is provided directly
        if "maintenanceData" in event:
            maintenance_data = event["maintenanceData"]
        elif "maintenanceId" in event:
            # Fetch from backend
            maintenance_id = event["maintenanceId"]
            
            # Get Auth0 token
            auth0_domain = os.getenv("Auth0Management__Domain")
            client_id = os.getenv("Auth0Management__ClientId")
            client_secret = os.getenv("Auth0Management__ClientSecret")
            audience = os.getenv("Auth0Management__Audience")
            
            token_url = f"{auth0_domain}/oauth/token"
            token_payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": audience,
                "grant_type": "client_credentials"
            }
            
            token_response = requests.post(token_url, json=token_payload)
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]
            
            # Fetch maintenance data
            backend_url = f"https://3kiiv9aysj.execute-api.us-west-2.amazonaws.com/api/v1.0/maintenance/{maintenance_id}/triage"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(backend_url, headers=headers)
            response.raise_for_status()
            maintenance_data = response.json()
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required field: maintenanceId or maintenanceData"
                })
            }
        
        # Process through triage pipeline
        result = asyncio.run(process_triage(maintenance_data))
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "detail": str(e)
            })
        }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "maintenanceId": "8ec5ee0b-1952-4c66-8773-55baf33faba1"
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))


"""
API Test Script for RentMatrix AI Triage System
Tests all 4 agents through the FastAPI endpoints
"""

import requests
import json
from typing import Dict, Any


# API Configuration
API_BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def test_health():
    """Test the health endpoint."""
    print("=" * 80)
    print("Testing Health Endpoint")
    print("=" * 80)
    
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_triage(description: str, test_name: str = "Test Case"):
    """Test the triage endpoint with a maintenance description."""
    print("=" * 80)
    print(f"{test_name}")
    print("=" * 80)
    print(f"\nDescription: {description}\n")
    
    payload = {"description": description}
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/triage",
            headers=HEADERS,
            json=payload
        )
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            result = response.json()
            
            # Display results from all 4 agents
            print("=" * 80)
            print("AGENT OUTPUTS")
            print("=" * 80)
            
            # Agent 1: Triage
            if "triage" in result:
                print("\n[Agent 1] Triage Classifier:")
                print("-" * 40)
                triage = result["triage"]
                print(f"  Severity: {triage.get('severity', 'N/A')}")
                print(f"  Trade: {triage.get('trade', 'N/A')}")
                print(f"  Triage Confidence: {triage.get('confidence', 'N/A')}")
                print(f"  Reasoning: {triage.get('reasoning', 'N/A')}")
            
            # Agent 2: Priority
            if "priority" in result:
                print("\n[Agent 2] Priority Calculator:")
                print("-" * 40)
                priority = result["priority"]
                print(f"  Priority Score: {priority.get('priority_score', 'N/A')}/100")
                print(f"  Base Score: {priority.get('base_score', 'N/A')}")
                print(f"  Total Modifiers: +{priority.get('total_modifiers', 0)}")
                if "applied_modifiers" in priority and priority["applied_modifiers"]:
                    print(f"  Applied Modifiers: {len(priority['applied_modifiers'])} modifier(s)")
            
            # Agent 3: Explainer
            if "explanation" in result:
                print("\n[Agent 3] Explainer:")
                print("-" * 40)
                explanation = result["explanation"]
                print(f"  PM Explanation: {explanation.get('pm_explanation', 'N/A')}")
                print(f"  Tenant Explanation: {explanation.get('tenant_explanation', 'N/A')}")
            
            # Agent 4: Confidence Evaluator ⭐ NEW!
            if "confidence" in result:
                print("\n[Agent 4] Confidence Evaluator: ⭐")
                print("-" * 40)
                confidence = result["confidence"]
                print(f"  Overall Confidence: {confidence.get('confidence', 'N/A')}")
                print(f"  Routing Decision: {confidence.get('routing', 'N/A')}")
                
                risk_flags = confidence.get('risk_flags', [])
                if risk_flags:
                    print(f"  Risk Flags: {', '.join(risk_flags)}")
                else:
                    print("  Risk Flags: None")
                
                print(f"  Recommendation: {confidence.get('recommendation', 'N/A')}")
                
                # Show confidence factors
                factors = confidence.get('confidence_factors', [])
                if factors:
                    print(f"\n  Confidence Factors ({len(factors)}):")
                    for i, factor in enumerate(factors, 1):
                        impact = factor.get('impact', 'N/A')
                        points = factor.get('points', 0)
                        sign = '+' if points >= 0 else ''
                        print(f"    {i}. {factor.get('factor', 'N/A')} ({impact}): {sign}{points}")
            
            # Summary
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            
            severity = result.get('triage', {}).get('severity', 'N/A')
            priority_score = result.get('priority', {}).get('priority_score', 'N/A')
            overall_confidence = result.get('confidence', {}).get('confidence', 'N/A')
            routing = result.get('confidence', {}).get('routing', 'N/A')
            
            print(f"  Classification: {severity}")
            print(f"  Priority: {priority_score}/100")
            print(f"  Confidence: {overall_confidence}")
            print(f"  Routing: {routing}")
            
            # Routing explanation
            print("\n  Routing Meaning:")
            if routing == "AUTO_APPROVE":
                print("    ✅ High confidence - Automatically approved (85% of cases)")
            elif routing == "PM_REVIEW_QUEUE":
                print("    ⚠️  Moderate confidence - Queued for PM review (12% of cases)")
            elif routing == "PM_IMMEDIATE_REVIEW":
                print("    🚨 Low confidence - Requires immediate PM attention (3% of cases)")
            
            print("\n" + "=" * 80)
            print()
            
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the server is running:")
        print("   Run: python api/app.py")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()


def main():
    """Run all test cases."""
    print("\n" + "=" * 80)
    print("RENTMATRIX AI TRIAGE API - TESTING ALL 4 AGENTS")
    print("=" * 80)
    print()
    
    # Test health endpoint
    test_health()
    
    # Test Case 1: EMERGENCY - Gas Leak
    test_triage(
        description=(
            "Strong gas smell in the basement near the water heater. "
            "Started about 20 minutes ago and getting stronger. "
            "Making my wife and kids feel dizzy and nauseous. "
            "We evacuated to the neighbor's house. "
            "Can smell it from outside now. "
            "Please send someone IMMEDIATELY this is dangerous!"
        ),
        test_name="Test Case 1: EMERGENCY - Gas Leak with Evacuation"
    )
    
    # Test Case 2: HIGH - Active Water Damage
    test_triage(
        description=(
            "Toilet overflowed about 30 minutes ago. "
            "Water is spreading to the bedroom now. "
            "I tried to stop it but can't. "
            "The floor is soaking wet and it's still leaking. "
            "This is getting worse!"
        ),
        test_name="Test Case 2: HIGH - Active Water Damage"
    )
    
    # Test Case 3: MEDIUM - Ambiguous Electrical Issue
    test_triage(
        description=(
            "One of the outlets in the kitchen isn't working. "
            "Might be making a slight buzzing sound, not sure. "
            "Other outlets seem fine. "
            "Not urgent but would like someone to check it out."
        ),
        test_name="Test Case 3: MEDIUM - Ambiguous Electrical Issue (Low Confidence Expected)"
    )
    
    # Test Case 4: LOW - Cosmetic Issue
    test_triage(
        description=(
            "There's a small paint chip on the wall in the living room. "
            "About 2 inches wide. Not getting bigger. "
            "Just cosmetic, but would be nice to get it touched up when convenient."
        ),
        test_name="Test Case 4: LOW - Cosmetic Paint Issue"
    )
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)
    print("\nNote: The API now includes all 4 agents:")
    print("  1. Triage Classifier")
    print("  2. Priority Calculator")
    print("  3. Explainer")
    print("  4. Confidence Evaluator ⭐ NEW!")
    print()


if __name__ == "__main__":
    main()

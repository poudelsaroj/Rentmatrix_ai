"""
Test Vendor Matching Algorithm
Demonstrates intelligent LLM-based vendor matching with tenant time preferences.
"""

import asyncio
import json
from agent.core_agents import VendorMatchingAgent
from agent.data import MOCK_VENDORS, get_vendors_by_trade


async def test_vendor_matching():
    """Test vendor matching with various scenarios."""
    
    print("="*80)
    print("RENTMATRIX AI - VENDOR MATCHING ALGORITHM TEST")
    print("="*80)
    print()
    
    # Initialize vendor matching agent
    agent = VendorMatchingAgent(model="gpt-5-mini", vendors=MOCK_VENDORS)
    
    print(f"[INFO] Loaded {len(MOCK_VENDORS)} vendors from mock database")
    print()
    
    # ========================================================================
    # TEST CASE 1: Emergency Gas Leak (High Priority)
    # ========================================================================
    
    print("="*80)
    print("TEST CASE 1: Emergency Gas Leak")
    print("="*80)
    print()
    
    triage_output_1 = {
        "severity": "EMERGENCY",
        "trade": "PLUMBING",
        "reasoning": "Gas leak detected, tenant evacuated, immediate life safety risk",
        "confidence": 0.98,
        "key_factors": [
            "Gas smell reported",
            "Tenant evacuated",
            "Getting worse over time"
        ]
    }
    
    priority_output_1 = {
        "priority_score": 98.3,
        "severity": "EMERGENCY",
        "base_hazard": 5.667,
        "combined_hazard": 57.379
    }
    
    request_data_1 = {
        "request": {
            "request_id": "req-001",
            "description": "Strong gas smell in basement near water heater. Getting worse. We evacuated 15 minutes ago. Need immediate help!",
            "reported_at": "2024-12-17T23:30:00Z",
            "channel": "MOBILE"
        },
        "context": {
            "weather": {
                "temperature": 32,
                "condition": "clear"
            },
            "tenant": {
                "age": 78,
                "is_elderly": True,
                "has_infant": False,
                "occupant_count": 2
            },
            "property": {
                "type": "Single Family Home",
                "age": 25
            },
            "timing": {
                "day_of_week": "Tuesday",
                "hour": 23,
                "is_after_hours": True,
                "is_weekend": False,
                "is_late_night": True
            }
        }
    }
    
    tenant_times_1 = [
        "ASAP - Emergency",
        "Within 1 hour",
        "Any time tonight"
    ]
    
    print("Request: Emergency gas leak, elderly tenants, late night")
    print(f"Severity: {triage_output_1['severity']}")
    print(f"Priority Score: {priority_output_1['priority_score']}/100")
    print(f"Tenant Preferred Times: {tenant_times_1}")
    print()
    
    # Build prompt and run agent
    prompt_1 = agent.build_prompt(
        triage_output=triage_output_1,
        priority_output=priority_output_1,
        request_data=request_data_1,
        tenant_preferred_times=tenant_times_1,
        property_location={"city": "Boston", "state": "MA", "zip_code": "02101"}
    )
    
    print("[Running LLM-based vendor matching...]")
    print()
    
    result_1 = await agent.run(prompt_1)
    
    print("-"*80)
    print("VENDOR MATCHING RESULTS:")
    print("-"*80)
    print()
    
    try:
        result_json = json.loads(result_1.final_output)
        display_vendor_results(result_json)
    except json.JSONDecodeError:
        print("[WARNING] Could not parse JSON output:")
        print(result_1.final_output)
    
    print()
    print()
    
    # ========================================================================
    # TEST CASE 2: Routine Faucet Repair (Medium Priority)
    # ========================================================================
    
    print("="*80)
    print("TEST CASE 2: Routine Faucet Repair")
    print("="*80)
    print()
    
    triage_output_2 = {
        "severity": "MEDIUM",
        "trade": "PLUMBING",
        "reasoning": "Slow leak under kitchen sink, contained but needs repair within 24-48 hours",
        "confidence": 0.92,
        "key_factors": [
            "Leak contained",
            "No active spreading",
            "Standard repair timeframe"
        ]
    }
    
    priority_output_2 = {
        "priority_score": 35.2,
        "severity": "MEDIUM",
        "base_hazard": 0.429,
        "combined_hazard": 0.545
    }
    
    request_data_2 = {
        "request": {
            "request_id": "req-002",
            "description": "Kitchen faucet dripping slowly. Small puddle under sink. Not urgent but should be fixed soon.",
            "reported_at": "2024-12-17T14:30:00Z",
            "channel": "WEB"
        },
        "context": {
            "weather": {
                "temperature": 45,
                "condition": "partly cloudy"
            },
            "tenant": {
                "age": 32,
                "is_elderly": False,
                "has_infant": False,
                "occupant_count": 2
            },
            "property": {
                "type": "Apartment",
                "age": 15
            },
            "timing": {
                "day_of_week": "Tuesday",
                "hour": 14,
                "is_after_hours": False,
                "is_weekend": False
            }
        }
    }
    
    tenant_times_2 = [
        "Monday 09:00-12:00",
        "Wednesday 14:00-17:00",
        "Friday 10:00-15:00"
    ]
    
    print("Request: Routine faucet repair, standard tenant, business hours")
    print(f"Severity: {triage_output_2['severity']}")
    print(f"Priority Score: {priority_output_2['priority_score']}/100")
    print(f"Tenant Preferred Times: {tenant_times_2}")
    print()
    
    prompt_2 = agent.build_prompt(
        triage_output=triage_output_2,
        priority_output=priority_output_2,
        request_data=request_data_2,
        tenant_preferred_times=tenant_times_2,
        property_location={"city": "Boston", "state": "MA", "zip_code": "02115"}
    )
    
    print("[Running LLM-based vendor matching...]")
    print()
    
    result_2 = await agent.run(prompt_2)
    
    print("-"*80)
    print("VENDOR MATCHING RESULTS:")
    print("-"*80)
    print()
    
    try:
        result_json = json.loads(result_2.final_output)
        display_vendor_results(result_json)
    except json.JSONDecodeError:
        print("[WARNING] Could not parse JSON output:")
        print(result_2.final_output)
    
    print()
    print()
    
    # ========================================================================
    # TEST CASE 3: Electrical Outlet Not Working (Medium Priority)
    # ========================================================================
    
    print("="*80)
    print("TEST CASE 3: Electrical Outlet Not Working")
    print("="*80)
    print()
    
    triage_output_3 = {
        "severity": "MEDIUM",
        "trade": "ELECTRICAL",
        "reasoning": "Single outlet dead with no other symptoms, standard repair needed",
        "confidence": 0.88,
        "key_factors": [
            "Single outlet affected",
            "No buzzing or warmth",
            "Safe but needs repair"
        ]
    }
    
    priority_output_3 = {
        "priority_score": 32.5,
        "severity": "MEDIUM",
        "base_hazard": 0.429,
        "combined_hazard": 0.481
    }
    
    request_data_3 = {
        "request": {
            "request_id": "req-003",
            "description": "Outlet in bedroom not working. Changed bulb in lamp but still nothing. Other outlets work fine.",
            "reported_at": "2024-12-17T16:00:00Z",
            "channel": "MOBILE"
        },
        "context": {
            "weather": {
                "temperature": 52,
                "condition": "cloudy"
            },
            "tenant": {
                "age": 28,
                "is_elderly": False,
                "has_infant": False,
                "occupant_count": 1
            },
            "property": {
                "type": "Studio Apartment",
                "age": 10
            },
            "timing": {
                "day_of_week": "Tuesday",
                "hour": 16,
                "is_after_hours": False,
                "is_weekend": False
            }
        }
    }
    
    tenant_times_3 = [
        "Tuesday 10:00-13:00",
        "Thursday 15:00-18:00",
        "Saturday 09:00-12:00"
    ]
    
    print("Request: Dead outlet, no other symptoms, flexible timing")
    print(f"Severity: {triage_output_3['severity']}")
    print(f"Priority Score: {priority_output_3['priority_score']}/100")
    print(f"Tenant Preferred Times: {tenant_times_3}")
    print()
    
    prompt_3 = agent.build_prompt(
        triage_output=triage_output_3,
        priority_output=priority_output_3,
        request_data=request_data_3,
        tenant_preferred_times=tenant_times_3,
        property_location={"city": "Somerville", "state": "MA", "zip_code": "02143"}
    )
    
    print("[Running LLM-based vendor matching...]")
    print()
    
    result_3 = await agent.run(prompt_3)
    
    print("-"*80)
    print("VENDOR MATCHING RESULTS:")
    print("-"*80)
    print()
    
    try:
        result_json = json.loads(result_3.final_output)
        display_vendor_results(result_json)
    except json.JSONDecodeError:
        print("[WARNING] Could not parse JSON output:")
        print(result_3.final_output)
    
    print()
    print("="*80)
    print("VENDOR MATCHING TEST COMPLETED")
    print("="*80)


def display_vendor_results(result_json: dict):
    """Display vendor matching results in a formatted way."""
    
    matched_vendors = result_json.get("matched_vendors", [])
    summary = result_json.get("summary", {})
    recommendations = result_json.get("recommendations", {})
    confidence = result_json.get("confidence", 0.0)
    
    # Display summary
    print(f"[SUMMARY]")
    print(f"  Total Vendors Evaluated: {summary.get('total_vendors_evaluated', 'N/A')}")
    print(f"  Vendors Recommended: {summary.get('vendors_recommended', 'N/A')}")
    print(f"  Match Confidence: {confidence:.2f}")
    print()
    
    # Display recommendations
    if matched_vendors:
        print(f"[TOP {len(matched_vendors)} VENDOR RECOMMENDATIONS]")
        print()
        
        for vendor in matched_vendors:
            rank = vendor.get("rank", "?")
            company = vendor.get("company_name", "Unknown")
            vendor_id = vendor.get("vendor_id", "N/A")
            match_score = vendor.get("match_score", 0)
            availability_match = vendor.get("availability_match", "Unknown")
            
            print(f"{'='*60}")
            print(f"RANK #{rank}: {company} ({vendor_id})")
            print(f"{'='*60}")
            print(f"Match Score: {match_score}/100")
            print(f"Availability Match: {availability_match}")
            print()
            
            # Contact info
            contact = vendor.get("contact", {})
            print(f"Contact: {contact.get('name', 'N/A')}")
            print(f"Phone: {contact.get('phone', 'N/A')}")
            print(f"Email: {contact.get('email', 'N/A')}")
            print()
            
            # Score breakdown
            breakdown = vendor.get("score_breakdown", {})
            print(f"Score Breakdown:")
            print(f"  - Expertise: {breakdown.get('expertise', 0)}/30")
            print(f"  - Availability: {breakdown.get('availability', 0)}/25")
            print(f"  - Ratings: {breakdown.get('ratings', 0)}/25")
            print(f"  - Location: {breakdown.get('location', 0)}/15")
            print(f"  - Cost: {breakdown.get('cost', 0)}/10")
            print(f"  - Special Factors: {breakdown.get('special_factors', 0)}/10")
            print()
            
            # Matching time slots
            matching_slots = vendor.get("matching_time_slots", [])
            if matching_slots:
                print(f"Matching Time Slots:")
                for slot in matching_slots:
                    print(f"  - {slot}")
                print()
            
            # Estimated cost
            cost = vendor.get("estimated_cost", {})
            if cost:
                print(f"Estimated Cost:")
                print(f"  - Hourly Rate: ${cost.get('hourly_rate', 0):.2f}/hour")
                print(f"  - Estimated Hours: {cost.get('estimated_hours', 0):.1f}")
                print(f"  - Trip Fee: ${cost.get('trip_fee', 0):.2f}")
                print(f"  - Multipliers: {cost.get('multipliers', 'None')}")
                print(f"  - Total Estimate: ${cost.get('estimated_total_min', 0):.2f} - ${cost.get('estimated_total_max', 0):.2f}")
                print()
            
            # Strengths
            strengths = vendor.get("strengths", [])
            if strengths:
                print(f"Strengths:")
                for strength in strengths:
                    print(f"  + {strength}")
                print()
            
            # Considerations
            considerations = vendor.get("considerations", [])
            if considerations:
                print(f"Considerations:")
                for consideration in considerations:
                    print(f"  ! {consideration}")
                print()
            
            # Recommendation reason
            reason = vendor.get("recommendation_reason", "")
            if reason:
                print(f"Why This Vendor:")
                print(f"  {reason}")
                print()
    
    # Display primary recommendation
    if recommendations:
        print(f"{'='*60}")
        print(f"[PRIMARY RECOMMENDATION]")
        print(f"{'='*60}")
        print(f"Vendor: {recommendations.get('primary_choice', 'N/A')}")
        print(f"Reason: {recommendations.get('primary_reason', 'N/A')}")
        print()
        print(f"[BACKUP OPTION]")
        print(f"Vendor: {recommendations.get('backup_choice', 'N/A')}")
        print(f"Reason: {recommendations.get('backup_reason', 'N/A')}")
        print()


if __name__ == "__main__":
    asyncio.run(test_vendor_matching())








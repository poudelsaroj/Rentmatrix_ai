"""
Complete Demo: RentMatrix AI Triage + Vendor Matching
Demonstrates the full workflow from triage to vendor selection.
"""

import asyncio
import json
from agent.pipeline.triage_pipeline import TriagePipeline
from agent.core_agents import VendorMatchingAgent
from agent.data import MOCK_VENDORS


# Sample maintenance request
SAMPLE_REQUEST_PLUMBING = {
    "test_id": "DEMO_001",
    "request": {
        "request_id": "req-plumbing-001",
        "description": "Kitchen sink faucet is dripping constantly. Small puddle forming under the sink. Not getting worse but annoying and wasting water. Would like this fixed in the next few days when convenient.",
        "images": [],
        "reported_at": "2024-12-17T14:30:00Z",
        "channel": "WEB"
    },
    "context": {
        "weather": {
            "temperature": 45,
            "condition": "partly cloudy",
            "forecast": "Clear, highs in mid 40s",
            "alerts": []
        },
        "tenant": {
            "age": 32,
            "is_elderly": False,
            "has_infant": False,
            "has_medical_condition": False,
            "is_pregnant": False,
            "occupant_count": 2,
            "tenure_months": 18
        },
        "property": {
            "type": "Apartment",
            "age": 15,
            "floor": 3,
            "total_units": 12,
            "has_elevator": True
        },
        "timing": {
            "day_of_week": "Tuesday",
            "hour": 14,
            "is_after_hours": False,
            "is_weekend": False,
            "is_holiday": False,
            "is_late_night": False
        }
    }
}

SAMPLE_REQUEST_EMERGENCY = {
    "test_id": "DEMO_002",
    "request": {
        "request_id": "req-emergency-001",
        "description": "Strong gas smell in basement near the water heater! Started about 30 minutes ago and it's getting stronger. My wife and I evacuated to the neighbor's house. We can smell it from outside now. This is really scary - please send someone IMMEDIATELY!",
        "images": [],
        "reported_at": "2024-12-17T23:15:00Z",
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
            "age": 78,
            "is_elderly": True,
            "has_infant": False,
            "has_medical_condition": False,
            "is_pregnant": False,
            "occupant_count": 2,
            "tenure_months": 48
        },
        "property": {
            "type": "Single Family Home",
            "age": 25,
            "floor": None,
            "total_units": 1,
            "has_elevator": False
        },
        "timing": {
            "day_of_week": "Tuesday",
            "hour": 23,
            "is_after_hours": True,
            "is_weekend": False,
            "is_holiday": False,
            "is_late_night": True
        }
    }
}


def format_request_prompt(request_data: dict) -> str:
    """Format request data into prompt string."""
    return f"this is the description of the request: {json.dumps(request_data)}"


async def run_complete_demo(request_data: dict, tenant_preferred_times: list, property_location: dict):
    """Run complete triage + vendor matching workflow."""
    
    print("="*80)
    print("RENTMATRIX AI - COMPLETE WORKFLOW DEMO")
    print("Triage Classification → Priority Scoring → Vendor Matching")
    print("="*80)
    print()
    
    # ========================================================================
    # STEP 1: Triage Pipeline (Agents 1-5)
    # ========================================================================
    
    print("[STEP 1] Running Triage Pipeline...")
    print("-"*80)
    
    pipeline = TriagePipeline(
        triage_model="gpt-5-mini",
        priority_model="gpt-5-mini",
        explainer_model="gpt-5-mini",
        confidence_model="gpt-5-mini",
        verbose=False
    )
    
    request_prompt = format_request_prompt(request_data)
    result = await pipeline.run(request_prompt, request_data)
    
    # Parse results
    triage_parsed = result.triage_parsed
    priority_parsed = result.priority_parsed
    
    print()
    print("[Triage Results]")
    print(f"  Severity: {triage_parsed.get('severity', 'N/A')}")
    print(f"  Trade: {triage_parsed.get('trade', 'N/A')}")
    print(f"  Priority Score: {priority_parsed.get('priority_score', 'N/A')}/100")
    print(f"  Confidence: {triage_parsed.get('confidence', 'N/A')}")
    print()
    
    # ========================================================================
    # STEP 2: Vendor Matching (Agent 6)
    # ========================================================================
    
    print("[STEP 2] Running Vendor Matching Agent...")
    print("-"*80)
    print()
    
    vendor_agent = VendorMatchingAgent(model="gpt-5-mini", vendors=MOCK_VENDORS)
    
    print(f"[INFO] Tenant Preferred Times:")
    for time in tenant_preferred_times:
        print(f"  - {time}")
    print()
    
    print(f"[INFO] Property Location: {property_location.get('city')}, {property_location.get('state')} {property_location.get('zip_code')}")
    print()
    
    vendor_prompt = vendor_agent.build_prompt(
        triage_output=triage_parsed,
        priority_output=priority_parsed,
        request_data=request_data,
        tenant_preferred_times=tenant_preferred_times,
        property_location=property_location
    )
    
    print("[INFO] Analyzing vendors and matching to request...")
    vendor_result = await vendor_agent.run(vendor_prompt)
    
    print()
    print("="*80)
    print("VENDOR MATCHING RESULTS")
    print("="*80)
    print()
    
    try:
        vendor_json = json.loads(vendor_result.final_output)
        display_results(vendor_json)
    except json.JSONDecodeError:
        print("[WARNING] Could not parse vendor matching output:")
        print(vendor_result.final_output)
    
    print()
    print("="*80)
    print("WORKFLOW COMPLETED")
    print("="*80)
    print()
    
    return {
        "triage": triage_parsed,
        "priority": priority_parsed,
        "vendors": vendor_json if 'vendor_json' in locals() else None
    }


def display_results(vendor_json: dict):
    """Display vendor matching results."""
    
    matched_vendors = vendor_json.get("matched_vendors", [])
    summary = vendor_json.get("summary", {})
    recommendations = vendor_json.get("recommendations", {})
    confidence = vendor_json.get("confidence", 0.0)
    
    print(f"Match Confidence: {confidence:.2%}")
    print(f"Vendors Evaluated: {summary.get('total_vendors_evaluated', 0)}")
    print(f"Vendors Recommended: {summary.get('vendors_recommended', 0)}")
    print()
    
    if matched_vendors:
        print(f"TOP {len(matched_vendors)} RECOMMENDED VENDORS:")
        print()
        
        for i, vendor in enumerate(matched_vendors, 1):
            print(f"{i}. {vendor.get('company_name', 'Unknown')} (Score: {vendor.get('match_score', 0)}/100)")
            print(f"   Contact: {vendor.get('contact', {}).get('name', 'N/A')} | {vendor.get('contact', {}).get('phone', 'N/A')}")
            print(f"   Availability: {vendor.get('availability_match', 'N/A')}")
            
            cost = vendor.get('estimated_cost', {})
            if cost:
                cost_min = cost.get('estimated_total_min', 0)
                cost_max = cost.get('estimated_total_max', 0)
                print(f"   Estimated Cost: ${cost_min:.2f} - ${cost_max:.2f}")
            
            print(f"   Why: {vendor.get('recommendation_reason', 'N/A')}")
            print()
    
    if recommendations:
        print("-"*80)
        print(f"PRIMARY RECOMMENDATION: {recommendations.get('primary_choice', 'N/A')}")
        print(f"  → {recommendations.get('primary_reason', 'N/A')}")
        print()
        print(f"BACKUP OPTION: {recommendations.get('backup_choice', 'N/A')}")
        print(f"  → {recommendations.get('backup_reason', 'N/A')}")


async def main():
    """Run demo scenarios."""
    
    print()
    print("██████╗ ███████╗███╗   ██╗████████╗███╗   ███╗ █████╗ ████████╗██████╗ ██╗██╗  ██╗")
    print("██╔══██╗██╔════╝████╗  ██║╚══██╔══╝████╗ ████║██╔══██╗╚══██╔══╝██╔══██╗██║╚██╗██╔╝")
    print("██████╔╝█████╗  ██╔██╗ ██║   ██║   ██╔████╔██║███████║   ██║   ██████╔╝██║ ╚███╔╝ ")
    print("██╔══██╗██╔══╝  ██║╚██╗██║   ██║   ██║╚██╔╝██║██╔══██║   ██║   ██╔══██╗██║ ██╔██╗ ")
    print("██║  ██║███████╗██║ ╚████║   ██║   ██║ ╚═╝ ██║██║  ██║   ██║   ██║  ██║██║██╔╝ ██╗")
    print("╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝")
    print()
    print("AI-Powered Maintenance Triage & Vendor Matching System")
    print()
    
    # ========================================================================
    # DEMO 1: Routine Plumbing Repair
    # ========================================================================
    
    print("\n" + "="*80)
    print("DEMO 1: Routine Plumbing Repair")
    print("="*80)
    print()
    
    await run_complete_demo(
        request_data=SAMPLE_REQUEST_PLUMBING,
        tenant_preferred_times=[
            "Monday 09:00-12:00",
            "Wednesday 14:00-17:00",
            "Friday 10:00-15:00"
        ],
        property_location={
            "city": "Boston",
            "state": "MA",
            "zip_code": "02115"
        }
    )
    
    print("\n" + "="*80)
    print()
    input("Press Enter to continue to Demo 2...")
    print()
    
    # ========================================================================
    # DEMO 2: Emergency Gas Leak
    # ========================================================================
    
    print("\n" + "="*80)
    print("DEMO 2: Emergency Gas Leak")
    print("="*80)
    print()
    
    await run_complete_demo(
        request_data=SAMPLE_REQUEST_EMERGENCY,
        tenant_preferred_times=[
            "ASAP - Emergency",
            "Within 1 hour",
            "Any time tonight"
        ],
        property_location={
            "city": "Boston",
            "state": "MA",
            "zip_code": "02101"
        }
    )
    
    print()
    print("="*80)
    print("ALL DEMOS COMPLETED!")
    print("="*80)
    print()
    print("Summary:")
    print("  - Agent 1 (Triage): Classified severity and trade")
    print("  - Agent 2 (Priority): Calculated priority score")
    print("  - Agent 3 (Explainer): Provided clear explanations")
    print("  - Agent 4 (Confidence): Evaluated confidence")
    print("  - Agent 5 (SLA): Mapped to response deadlines")
    print("  - Agent 6 (Vendor Matching): Matched best vendors")
    print()
    print("The system successfully matched vendors based on:")
    print("  ✓ Trade expertise and specializations")
    print("  ✓ Tenant time preferences")
    print("  ✓ Vendor availability")
    print("  ✓ Performance ratings")
    print("  ✓ Cost considerations")
    print("  ✓ Location and service area")
    print("  ✓ Emergency capability (when needed)")
    print()


if __name__ == "__main__":
    asyncio.run(main())






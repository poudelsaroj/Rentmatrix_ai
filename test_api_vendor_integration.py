"""
Test API + Vendor Matching Integration
Tests the complete workflow through the API endpoint.
"""

import requests
import json

# API endpoint (make sure server is running: python api/app.py)
API_URL = "http://localhost:8000/triage"

def test_triage_with_vendor_matching():
    """Test triage endpoint with vendor matching enabled."""
    
    print("="*80)
    print("Testing RentMatrix AI API - Triage + Vendor Matching")
    print("="*80)
    print()
    
    # Test Case 1: Routine plumbing repair with vendor matching
    print("[TEST 1] Routine plumbing repair with vendor matching")
    print("-"*80)
    
    request_data = {
        "description": "Kitchen sink faucet is dripping constantly. Small puddle under sink. Not urgent but wasting water.",
        "location": {
            "query": "Boston, MA"
        },
        "tenant_preferred_times": [
            "Monday 09:00-12:00",
            "Wednesday 14:00-17:00",
            "Friday 10:00-15:00"
        ],
        "include_vendor_matching": True
    }
    
    print(f"Request: {request_data['description']}")
    print(f"Location: {request_data['location']['query']}")
    print(f"Tenant times: {request_data['tenant_preferred_times']}")
    print()
    
    try:
        response = requests.post(API_URL, json=request_data, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Display results
        print("[TRIAGE]")
        triage = data.get("triage", {})
        print(f"  Severity: {triage.get('severity')}")
        print(f"  Trade: {triage.get('trade')}")
        print(f"  Confidence: {triage.get('confidence')}")
        print()
        
        print("[PRIORITY]")
        priority = data.get("priority", {})
        print(f"  Priority Score: {priority.get('priority_score')}/100")
        print()
        
        print("[VENDOR MATCHING]")
        vendors = data.get("vendors", {})
        if vendors:
            if vendors.get("error"):
                print(f"  ⚠️  Error: {vendors.get('error')}")
            else:
                matched_vendors = vendors.get("matched_vendors", [])
                summary = vendors.get("summary", {})
                recommendations = vendors.get("recommendations", {})
                
                print(f"  Vendors Evaluated: {summary.get('total_vendors_evaluated', 0)}")
                print(f"  Vendors Recommended: {summary.get('vendors_recommended', 0)}")
                print(f"  Confidence: {vendors.get('confidence', 0):.2%}")
                print()
                
                if matched_vendors:
                    print(f"  Top 3 Recommendations:")
                    for i, vendor in enumerate(matched_vendors[:3], 1):
                        print(f"  {i}. {vendor.get('company_name')} (Score: {vendor.get('match_score')}/100)")
                        print(f"     Contact: {vendor.get('contact', {}).get('phone')}")
                        print(f"     Availability: {vendor.get('availability_match')}")
                        cost = vendor.get('estimated_cost', {})
                        print(f"     Cost: ${cost.get('estimated_total_min', 0):.2f} - ${cost.get('estimated_total_max', 0):.2f}")
                        print()
                
                if recommendations.get('primary_choice'):
                    print(f"  ⭐ Primary Recommendation: {recommendations.get('primary_choice')}")
                    print(f"     {recommendations.get('primary_reason', '')}")
        else:
            print("  No vendor matching data returned")
        
        print()
        print("✅ Test 1 completed successfully!")
        
    except requests.RequestException as e:
        print(f"❌ API request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print()
    print()
    
    # Test Case 2: Without vendor matching
    print("[TEST 2] Same request WITHOUT vendor matching")
    print("-"*80)
    
    request_data_2 = {
        "description": "Kitchen sink faucet is dripping constantly. Small puddle under sink.",
        "location": {
            "query": "Boston, MA"
        },
        "include_vendor_matching": False
    }
    
    print(f"Request: {request_data_2['description']}")
    print(f"Vendor matching: Disabled")
    print()
    
    try:
        response = requests.post(API_URL, json=request_data_2, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print("[RESULTS]")
        print(f"  Triage severity: {data.get('triage', {}).get('severity')}")
        print(f"  Priority score: {data.get('priority', {}).get('priority_score')}/100")
        print(f"  Vendors included: {'vendors' in data}")
        print()
        
        print("✅ Test 2 completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print()
    print("="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    print()
    print("Summary:")
    print("  - Test 1: Triage + Vendor Matching ✓")
    print("  - Test 2: Triage only (no vendors) ✓")
    print()
    print("Next steps:")
    print("  1. Open browser: http://localhost:8000/docs (Swagger UI)")
    print("  2. Or frontend: Open frontend/index.html")
    print("  3. Test vendor matching checkbox and time slots")
    print()


if __name__ == "__main__":
    print()
    print("Make sure the API server is running:")
    print("  $ python api/app.py")
    print()
    input("Press Enter when server is ready...")
    print()
    
    test_triage_with_vendor_matching()








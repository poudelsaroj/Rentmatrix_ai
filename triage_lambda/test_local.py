"""
Local test script for Lambda handler
Run this to test the Lambda function locally before deployment
"""

import json
from lambda_handler import lambda_handler

def test_with_maintenance_id():
    """Test with maintenanceId (requires backend access)"""
    print("="*70)
    print("Test 1: With MaintenanceId")
    print("="*70)
    
    event = {
        "maintenanceId": "8ec5ee0b-1952-4c66-8773-55baf33faba1"
    }
    
    result = lambda_handler(event, None)
    
    print(f"\nStatus Code: {result['statusCode']}")
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print("\nResponse:")
        print(json.dumps(body, indent=2))
    else:
        print(f"\nError: {result['body']}")


def test_with_maintenance_data():
    """Test with direct maintenanceData"""
    print("\n" + "="*70)
    print("Test 2: With MaintenanceData")
    print("="*70)
    
    event = {
        "maintenanceData": {
            "request": {
                "requestId": "test-001",
                "description": "pipe cracked",
                "images": [],
                "reportedAt": "2025-12-24T10:00:00Z",
                "channel": "MOBILE"
            },
            "tenant": {
                "age": 25,
                "isElderly": False,
                "hasInfant": False,
                "hasMedicalCondition": False,
                "isPregnant": False,
                "occupantCount": 6,
                "tenureMonths": 0
            },
            "property": {
                "type": "Apartment",
                "age": 0,
                "floor": 1,
                "totalUnits": 4,
                "hasElevator": False
            },
            "timing": {
                "dayOfWeek": "Tuesday",
                "hour": 8,
                "isAfterHours": True,
                "isWeekend": False,
                "isHoliday": False,
                "isLateNight": False
            },
            "history": {
                "recentIssuesCount": 1,
                "lastRepairDate": None,
                "recurringCategory": None,
                "previousRepairFailed": False,
                "avgResolutionTimeHours": None
            },
            "similarCases": []
        }
    }
    
    result = lambda_handler(event, None)
    
    print(f"\nStatus Code: {result['statusCode']}")
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print("\nResponse:")
        print(json.dumps(body, indent=2))
    else:
        print(f"\nError: {result['body']}")


if __name__ == "__main__":
    print("\n🧪 RentMatrix AI Triage Lambda - Local Testing\n")
    
    # Choose which test to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "data":
        test_with_maintenance_data()
    else:
        print("Testing with maintenanceId (requires backend access)...")
        print("Use 'python test_local.py data' to test with sample data\n")
        test_with_maintenance_id()
    
    print("\n✅ Testing complete!\n")


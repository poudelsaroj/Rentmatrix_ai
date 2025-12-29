"""
Mock Data for Quotation Analyzer
Realistic mock data for users, vendors, and quotations for testing and development.
"""

import os
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .models import (
    QuotationResult,
    VendorQuotation,
    ComparisonResult,
    ExtractionMethod,
    TimeSlot
)


# ==================== SAMPLE IMAGES PATH ====================
SAMPLE_IMAGES_DIR = Path(__file__).parent / "sample_images"


def get_sample_image_path(filename: str) -> str:
    """Get full path to a sample image."""
    return str(SAMPLE_IMAGES_DIR / filename)


def get_sample_image_base64(filename: str) -> Optional[str]:
    """Get base64 encoded sample image."""
    path = SAMPLE_IMAGES_DIR / filename
    if path.exists():
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{data}"
    return None


# ==================== MOCK USER DATA ====================

MOCK_USERS = [
    {
        "user_id": "USR-001",
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "555-1001",
        "address": "456 Oak Street, Apt 3B",
        "city": "Boston",
        "state": "MA",
        "zip_code": "02101",
        "property_type": "Apartment",
        "tenant_since": "2023-06-15",
        "preferred_contact": "email",
        "emergency_contact": "Jane Smith (555-1002)"
    },
    {
        "user_id": "USR-002",
        "name": "Maria Garcia",
        "email": "maria.garcia@email.com",
        "phone": "555-2001",
        "address": "789 Pine Avenue, Unit 5",
        "city": "Cambridge",
        "state": "MA",
        "zip_code": "02139",
        "property_type": "Condo",
        "tenant_since": "2022-03-01",
        "preferred_contact": "phone",
        "emergency_contact": "Carlos Garcia (555-2002)"
    },
    {
        "user_id": "USR-003",
        "name": "David Chen",
        "email": "david.chen@email.com",
        "phone": "555-3001",
        "address": "321 Elm Drive",
        "city": "Brookline",
        "state": "MA",
        "zip_code": "02445",
        "property_type": "Single Family Home",
        "tenant_since": "2024-01-10",
        "preferred_contact": "email",
        "emergency_contact": "Lisa Chen (555-3002)"
    },
    {
        "user_id": "USR-004",
        "name": "Sarah Johnson",
        "email": "sarah.j@email.com",
        "phone": "555-4001",
        "address": "555 Maple Lane, Apt 12A",
        "city": "Somerville",
        "state": "MA",
        "zip_code": "02143",
        "property_type": "Apartment",
        "tenant_since": "2023-09-20",
        "preferred_contact": "phone",
        "emergency_contact": "Michael Johnson (555-4002)"
    },
    {
        "user_id": "USR-005",
        "name": "Robert Williams",
        "email": "r.williams@email.com",
        "phone": "555-5001",
        "address": "888 Birch Court",
        "city": "Newton",
        "state": "MA",
        "zip_code": "02458",
        "property_type": "Townhouse",
        "tenant_since": "2021-11-05",
        "preferred_contact": "email",
        "emergency_contact": "Emily Williams (555-5002)"
    }
]


# ==================== MOCK USER AVAILABILITY ====================

def generate_future_dates(days_ahead: int = 7) -> List[str]:
    """Generate future dates starting from today."""
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, days_ahead + 1)]


def create_mock_user_availability() -> Dict[str, List[Dict[str, str]]]:
    """Create mock availability for each user."""
    dates = generate_future_dates(7)

    return {
        "USR-001": [
            {"date": dates[0], "start_time": "09:00", "end_time": "12:00"},
            {"date": dates[1], "start_time": "14:00", "end_time": "18:00"},
            {"date": dates[3], "start_time": "10:00", "end_time": "15:00"}
        ],
        "USR-002": [
            {"date": dates[0], "start_time": "08:00", "end_time": "11:00"},
            {"date": dates[2], "start_time": "13:00", "end_time": "17:00"},
            {"date": dates[4], "start_time": "09:00", "end_time": "14:00"}
        ],
        "USR-003": [
            {"date": dates[1], "start_time": "10:00", "end_time": "14:00"},
            {"date": dates[2], "start_time": "15:00", "end_time": "19:00"},
            {"date": dates[5], "start_time": "08:00", "end_time": "12:00"}
        ],
        "USR-004": [
            {"date": dates[0], "start_time": "11:00", "end_time": "16:00"},
            {"date": dates[3], "start_time": "09:00", "end_time": "13:00"},
            {"date": dates[4], "start_time": "14:00", "end_time": "18:00"}
        ],
        "USR-005": [
            {"date": dates[2], "start_time": "08:00", "end_time": "12:00"},
            {"date": dates[3], "start_time": "13:00", "end_time": "17:00"},
            {"date": dates[6], "start_time": "10:00", "end_time": "15:00"}
        ]
    }


# ==================== MOCK VENDOR QUOTATION DATA ====================

MOCK_VENDORS_FOR_QUOTATION = [
    {
        "vendor_id": "VND-QT-001",
        "vendor_name": "Elite Plumbing Pros",
        "company_address": "123 Maple Ave, Atlanta, GA 30301",
        "phone": "555-0111",
        "email": "quotes@eliteplumbingpros.com",
        "trade": "PLUMBING",
        "rating": 4.8,
        "sample_image": "image.png",
        "quote_number": "EP-2025-99"
    },
    {
        "vendor_id": "VND-QT-002",
        "vendor_name": "A&R Plumbing Solutions",
        "company_address": "1234 S Battown Street, Plumbing, TA 30043",
        "phone": "555-0222",
        "email": "info@arplumbing.com",
        "trade": "PLUMBING",
        "rating": 4.6,
        "sample_image": "image (1).png",
        "quote_number": "Q-5548"
    },
    {
        "vendor_id": "VND-QT-003",
        "vendor_name": "QuickFix Plumbing 24/7",
        "company_address": "789 Service Blvd, Boston, MA 02101",
        "phone": "555-0333",
        "email": "emergency@quickfixplumbing.com",
        "trade": "PLUMBING",
        "rating": 4.9,
        "sample_image": "image (2).png",
        "quote_number": "QF-2025-001"
    }
]


# ==================== MOCK QUOTATION RESULTS ====================

def create_mock_quotation_results() -> List[QuotationResult]:
    """Create mock quotation extraction results matching the sample images."""

    results = []

    # Elite Plumbing Pros (image.png) - $482.30
    results.append(QuotationResult(
        vendor_name="Elite Plumbing Pros",
        total_price=482.30,
        currency="USD",
        items=[
            {
                "name": "Diagnosis & Clearing Clogged Bathroom Drain (Snake, Chemical)",
                "quantity": 1,
                "unit_price": 195.00,
                "total": 195.00
            },
            {
                "name": "Remove & Replace P-Trap Assembly (Materials & Labor)",
                "quantity": 1,
                "unit_price": 150.00,
                "total": 150.00
            },
            {
                "name": "Service Call & Travel",
                "quantity": 1,
                "unit_price": 110.00,
                "total": 110.00
            }
        ],
        subtotal=455.00,
        tax_amount=27.30,
        tax_rate=6.0,
        labor_cost=150.00,
        materials_cost=195.00,
        timeline_days=2,
        timeline_description="Work can be completed within 2 business days of approval",
        warranty_months=12,
        warranty_description="12-month warranty on all parts and labor",
        payment_terms="50% deposit, balance due upon completion",
        validity_days=30,
        special_conditions=[
            "Price valid for 30 days",
            "Emergency service available with 1.5x rate"
        ],
        contact_info="Elite Plumbing Pros | 123 Maple Ave, Atlanta, GA 30301 | (555) 0111",
        date_issued="2025-12-24",
        extraction_method=ExtractionMethod.LLM,
        confidence=0.95,
        errors=[]
    ))

    # A&R Plumbing Solutions (image (1).png) - $376.30
    results.append(QuotationResult(
        vendor_name="A&R Plumbing Solutions",
        total_price=376.30,
        currency="USD",
        items=[
            {
                "name": "Diagnosis & Clearing Clogged Bathroom Drain (Snake, Chemical)",
                "quantity": 1,
                "unit_price": 150.00,
                "total": 150.00
            },
            {
                "name": "Remove & Replace P-Trap Assembly (Materials & Labor)",
                "quantity": 1,
                "unit_price": 120.00,
                "total": 120.00
            },
            {
                "name": "Service Call & Travel",
                "quantity": 1,
                "unit_price": 65.00,
                "total": 85.00
            }
        ],
        subtotal=355.00,
        tax_amount=21.30,
        tax_rate=6.0,
        labor_cost=120.00,
        materials_cost=150.00,
        timeline_days=3,
        timeline_description="Completion within 3 business days",
        warranty_months=6,
        warranty_description="6-month warranty on parts and labor",
        payment_terms="Payment due upon completion",
        validity_days=30,
        special_conditions=[
            "Valid for 30 days",
            "Terms apply"
        ],
        contact_info="A&R Plumbing Solutions | 1234 S Battown Street | (555) 0222",
        date_issued="2025-12-24",
        extraction_method=ExtractionMethod.LLM,
        confidence=0.92,
        errors=[]
    ))

    # QuickFix Plumbing (image (2).png) - same as Elite but different vendor context
    results.append(QuotationResult(
        vendor_name="QuickFix Plumbing 24/7",
        total_price=525.00,
        currency="USD",
        items=[
            {
                "name": "Emergency Drain Clearing Service",
                "quantity": 1,
                "unit_price": 225.00,
                "total": 225.00
            },
            {
                "name": "P-Trap Replacement with Premium Parts",
                "quantity": 1,
                "unit_price": 180.00,
                "total": 180.00
            },
            {
                "name": "24/7 Service Call Fee",
                "quantity": 1,
                "unit_price": 120.00,
                "total": 120.00
            }
        ],
        subtotal=525.00,
        tax_amount=0.00,
        tax_rate=0.0,
        labor_cost=180.00,
        materials_cost=225.00,
        timeline_days=1,
        timeline_description="Same-day or next-day service available",
        warranty_months=24,
        warranty_description="24-month comprehensive warranty",
        payment_terms="Full payment after service completion",
        validity_days=14,
        special_conditions=[
            "24/7 emergency service",
            "Same-day service guaranteed",
            "Premium parts included"
        ],
        contact_info="QuickFix Plumbing 24/7 | 789 Service Blvd, Boston, MA 02101 | (555) 0333",
        date_issued="2025-12-24",
        extraction_method=ExtractionMethod.LLM,
        confidence=0.94,
        errors=[]
    ))

    return results


# ==================== MOCK VENDOR QUOTATIONS WITH TIME SLOTS ====================

def create_mock_vendor_quotations() -> List[VendorQuotation]:
    """Create mock vendor quotations with time slots and extracted data."""

    dates = generate_future_dates(7)
    quotation_results = create_mock_quotation_results()

    vendor_quotations = []

    # Vendor 1: Elite Plumbing Pros
    vendor_quotations.append(VendorQuotation(
        vendor_id="VND-QT-001",
        vendor_name="Elite Plumbing Pros",
        image_path=get_sample_image_path("image.png"),
        image_base64=get_sample_image_base64("image.png"),
        extracted_data=quotation_results[0],
        rank=0,
        available_slots=[
            TimeSlot(date=dates[0], start_time="09:00", end_time="13:00"),
            TimeSlot(date=dates[1], start_time="14:00", end_time="18:00"),
            TimeSlot(date=dates[3], start_time="08:00", end_time="12:00")
        ],
        matching_slots=[],
        schedule_score=0.0
    ))

    # Vendor 2: A&R Plumbing Solutions
    vendor_quotations.append(VendorQuotation(
        vendor_id="VND-QT-002",
        vendor_name="A&R Plumbing Solutions",
        image_path=get_sample_image_path("image (1).png"),
        image_base64=get_sample_image_base64("image (1).png"),
        extracted_data=quotation_results[1],
        rank=0,
        available_slots=[
            TimeSlot(date=dates[0], start_time="10:00", end_time="14:00"),
            TimeSlot(date=dates[2], start_time="09:00", end_time="15:00"),
            TimeSlot(date=dates[4], start_time="11:00", end_time="17:00")
        ],
        matching_slots=[],
        schedule_score=0.0
    ))

    # Vendor 3: QuickFix Plumbing 24/7
    vendor_quotations.append(VendorQuotation(
        vendor_id="VND-QT-003",
        vendor_name="QuickFix Plumbing 24/7",
        image_path=get_sample_image_path("image (2).png"),
        image_base64=get_sample_image_base64("image (2).png"),
        extracted_data=quotation_results[2],
        rank=0,
        available_slots=[
            TimeSlot(date=dates[0], start_time="07:00", end_time="19:00"),
            TimeSlot(date=dates[1], start_time="07:00", end_time="19:00"),
            TimeSlot(date=dates[2], start_time="07:00", end_time="19:00")
        ],
        matching_slots=[],
        schedule_score=0.0
    ))

    return vendor_quotations


# ==================== MOCK COMPARISON REQUEST DATA ====================

def create_mock_comparison_request(user_id: str = "USR-001") -> Dict[str, Any]:
    """Create a complete mock comparison request with user and vendor data."""

    user_availability = create_mock_user_availability()
    user_slots = user_availability.get(user_id, user_availability["USR-001"])
    vendor_quotations = create_mock_vendor_quotations()

    # Build request payload matching the API format
    quotations = []
    for vq in vendor_quotations:
        quotation = {
            "vendor_id": vq.vendor_id,
            "vendor_name": vq.vendor_name,
            "image": vq.image_base64 or vq.image_path,
            "available_slots": [slot.to_dict() for slot in vq.available_slots]
        }
        quotations.append(quotation)

    return {
        "use_llm": True,
        "quotations": quotations,
        "user_available_slots": user_slots
    }


# ==================== MOCK COMPARISON RESULT ====================

def create_mock_comparison_result() -> ComparisonResult:
    """Create a complete mock comparison result for testing."""

    dates = generate_future_dates(7)
    vendor_quotations = create_mock_vendor_quotations()

    # User availability
    user_slots = [
        TimeSlot(date=dates[0], start_time="09:00", end_time="12:00"),
        TimeSlot(date=dates[1], start_time="14:00", end_time="18:00"),
        TimeSlot(date=dates[3], start_time="10:00", end_time="15:00")
    ]

    # Calculate matching slots for each vendor
    for vq in vendor_quotations:
        matching = []
        for user_slot in user_slots:
            for vendor_slot in vq.available_slots:
                if user_slot.overlaps_with(vendor_slot):
                    matching.append(vendor_slot)
                    break
        vq.matching_slots = matching
        vq.schedule_score = len(matching) / len(user_slots) if user_slots else 0.0

    # Rank vendors (A&R has lowest price)
    vendor_quotations[1].rank = 1  # A&R Plumbing - $376.30 (best price)
    vendor_quotations[0].rank = 2  # Elite Plumbing - $482.30
    vendor_quotations[2].rank = 3  # QuickFix - $525.00 (fastest but most expensive)

    # Build ranked vendors list
    ranked_vendors = [
        {
            "rank": 1,
            "vendor_id": "VND-QT-002",
            "vendor_name": "A&R Plumbing Solutions",
            "total_price": 376.30,
            "currency": "USD",
            "timeline_days": 3,
            "warranty_months": 6,
            "score": 301.04,
            "confidence": 0.92,
            "schedule_score": 0.67,
            "matching_slots_count": 2,
            "available_slots": [s.to_dict() for s in vendor_quotations[1].available_slots],
            "matching_slots": [s.to_dict() for s in vendor_quotations[1].matching_slots]
        },
        {
            "rank": 2,
            "vendor_id": "VND-QT-001",
            "vendor_name": "Elite Plumbing Pros",
            "total_price": 482.30,
            "currency": "USD",
            "timeline_days": 2,
            "warranty_months": 12,
            "score": 385.84,
            "confidence": 0.95,
            "schedule_score": 0.67,
            "matching_slots_count": 2,
            "available_slots": [s.to_dict() for s in vendor_quotations[0].available_slots],
            "matching_slots": [s.to_dict() for s in vendor_quotations[0].matching_slots]
        },
        {
            "rank": 3,
            "vendor_id": "VND-QT-003",
            "vendor_name": "QuickFix Plumbing 24/7",
            "total_price": 525.00,
            "currency": "USD",
            "timeline_days": 1,
            "warranty_months": 24,
            "score": 420.00,
            "confidence": 0.94,
            "schedule_score": 1.0,
            "matching_slots_count": 3,
            "available_slots": [s.to_dict() for s in vendor_quotations[2].available_slots],
            "matching_slots": [s.to_dict() for s in vendor_quotations[2].matching_slots]
        }
    ]

    # Summary
    summary = {
        "lowest_price_vendor": "A&R Plumbing Solutions",
        "lowest_price": 376.30,
        "highest_price_vendor": "QuickFix Plumbing 24/7",
        "highest_price": 525.00,
        "average_price": 461.20,
        "price_range": 148.70,
        "price_difference_percent": 39.5,
        "fastest_timeline_vendor": "QuickFix Plumbing 24/7",
        "fastest_timeline_days": 1,
        "best_warranty_vendor": "QuickFix Plumbing 24/7",
        "best_warranty_months": 24
    }

    # Recommendation
    recommendation = {
        "recommended_vendor_id": "VND-QT-002",
        "recommended_vendor_name": "A&R Plumbing Solutions",
        "total_price": 376.30,
        "reason": "Best price at $376.30 | 2 matching time slot(s) | 3 days timeline | 6 months warranty",
        "confidence": 0.92,
        "schedule_score": 0.67,
        "matching_slots": [s.to_dict() for s in vendor_quotations[1].matching_slots]
    }

    # Red flags
    red_flags = [
        "A&R Plumbing Solutions: Only 1 matching time slot (limited flexibility)"
    ]

    # Schedule summary
    schedule_summary = {
        "schedule_considered": True,
        "user_slots_count": 3,
        "best_schedule_match_vendor": "QuickFix Plumbing 24/7",
        "best_match_count": 3,
        "perfect_match_vendors": ["QuickFix Plumbing 24/7"],
        "no_match_vendors": [],
        "message": "Best schedule compatibility: QuickFix Plumbing 24/7 (3 matching slots)"
    }

    return ComparisonResult(
        quotations=vendor_quotations,
        ranked_vendors=ranked_vendors,
        recommendation=recommendation,
        summary=summary,
        red_flags=red_flags,
        extraction_method=ExtractionMethod.LLM,
        overall_confidence=0.94,
        user_available_slots=user_slots,
        schedule_summary=schedule_summary
    )


# ==================== MAINTENANCE REQUEST MOCK DATA ====================

MOCK_MAINTENANCE_REQUESTS = [
    {
        "request_id": "REQ-2025-001",
        "user_id": "USR-001",
        "description": "Bathroom sink is clogged and draining very slowly. Water backs up when running the faucet.",
        "category": "PLUMBING",
        "severity": "MEDIUM",
        "created_at": "2025-12-24T10:30:00",
        "status": "PENDING_QUOTES",
        "property_address": "456 Oak Street, Apt 3B, Boston, MA 02101"
    },
    {
        "request_id": "REQ-2025-002",
        "user_id": "USR-002",
        "description": "Kitchen outlet stopped working. Tried resetting breaker but no luck.",
        "category": "ELECTRICAL",
        "severity": "MEDIUM",
        "created_at": "2025-12-23T15:45:00",
        "status": "QUOTES_RECEIVED",
        "property_address": "789 Pine Avenue, Unit 5, Cambridge, MA 02139"
    },
    {
        "request_id": "REQ-2025-003",
        "user_id": "USR-003",
        "description": "AC unit making loud grinding noise and not cooling properly.",
        "category": "HVAC",
        "severity": "HIGH",
        "created_at": "2025-12-22T09:00:00",
        "status": "VENDOR_ASSIGNED",
        "property_address": "321 Elm Drive, Brookline, MA 02445"
    },
    {
        "request_id": "REQ-2025-004",
        "user_id": "USR-004",
        "description": "Water heater pilot light keeps going out. No hot water for 2 days.",
        "category": "PLUMBING",
        "severity": "HIGH",
        "created_at": "2025-12-21T18:20:00",
        "status": "COMPLETED",
        "property_address": "555 Maple Lane, Apt 12A, Somerville, MA 02143"
    },
    {
        "request_id": "REQ-2025-005",
        "user_id": "USR-005",
        "description": "Front door lock is jammed and difficult to open from outside.",
        "category": "LOCKSMITH",
        "severity": "MEDIUM",
        "created_at": "2025-12-20T14:00:00",
        "status": "PENDING_QUOTES",
        "property_address": "888 Birch Court, Newton, MA 02458"
    }
]


# ==================== HELPER FUNCTIONS ====================

def get_mock_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a mock user by ID."""
    for user in MOCK_USERS:
        if user["user_id"] == user_id:
            return user
    return None


def get_mock_vendor_for_quotation(vendor_id: str) -> Optional[Dict[str, Any]]:
    """Get a mock vendor by ID."""
    for vendor in MOCK_VENDORS_FOR_QUOTATION:
        if vendor["vendor_id"] == vendor_id:
            return vendor
    return None


def get_mock_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Get a mock maintenance request by ID."""
    for request in MOCK_MAINTENANCE_REQUESTS:
        if request["request_id"] == request_id:
            return request
    return None


def get_all_mock_data() -> Dict[str, Any]:
    """Get all mock data as a single dictionary."""
    return {
        "users": MOCK_USERS,
        "user_availability": create_mock_user_availability(),
        "vendors": MOCK_VENDORS_FOR_QUOTATION,
        "vendor_quotations": [vq.to_dict() for vq in create_mock_vendor_quotations()],
        "quotation_results": [qr.to_dict() for qr in create_mock_quotation_results()],
        "maintenance_requests": MOCK_MAINTENANCE_REQUESTS,
        "sample_comparison_request": create_mock_comparison_request(),
        "sample_comparison_result": create_mock_comparison_result().to_dict()
    }


# ==================== DEMO FUNCTION ====================

def run_mock_demo():
    """Run a demo showing all mock data."""
    print("\n" + "=" * 60)
    print("QUOTATION ANALYZER - MOCK DATA DEMO")
    print("=" * 60)

    print("\n--- MOCK USERS ---")
    for user in MOCK_USERS:
        print(f"  {user['user_id']}: {user['name']} ({user['email']})")

    print("\n--- MOCK USER AVAILABILITY ---")
    availability = create_mock_user_availability()
    for user_id, slots in availability.items():
        print(f"  {user_id}:")
        for slot in slots:
            print(f"    - {slot['date']} {slot['start_time']}-{slot['end_time']}")

    print("\n--- MOCK VENDORS FOR QUOTATION ---")
    for vendor in MOCK_VENDORS_FOR_QUOTATION:
        print(f"  {vendor['vendor_id']}: {vendor['vendor_name']} ({vendor['trade']})")
        print(f"    Sample Image: {vendor['sample_image']}")

    print("\n--- MOCK QUOTATION RESULTS ---")
    results = create_mock_quotation_results()
    for result in results:
        print(f"  {result.vendor_name}:")
        print(f"    Total: ${result.total_price:.2f}")
        print(f"    Timeline: {result.timeline_days} days | Warranty: {result.warranty_months} months")

    print("\n--- SAMPLE COMPARISON RESULT ---")
    comparison = create_mock_comparison_result()
    print(f"  Recommended: {comparison.recommendation['recommended_vendor_name']}")
    print(f"  Best Price: ${comparison.summary['lowest_price']:.2f} ({comparison.summary['lowest_price_vendor']})")
    print(f"  Fastest: {comparison.summary['fastest_timeline_days']} days ({comparison.summary['fastest_timeline_vendor']})")
    print(f"  Best Warranty: {comparison.summary['best_warranty_months']} months ({comparison.summary['best_warranty_vendor']})")

    print("\n" + "=" * 60)
    print("Mock data ready for use!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_mock_demo()

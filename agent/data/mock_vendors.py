"""
Mock Vendor Database
Realistic vendor data for testing the vendor matching algorithm.
"""

from typing import List, Dict, Any
from agent.models.vendor_models import (
    Vendor, VendorTier, VendorLocation, VendorExpertise, 
    VendorRating, VendorPricing, TimeSlot, TradeCategory
)


def create_mock_vendors() -> List[Vendor]:
    """Create a realistic mock vendor database."""
    
    vendors = []
    
    # ==================== PLUMBING VENDORS ====================
    
    vendors.append(Vendor(
        vendor_id="VND-PL-001",
        company_name="QuickFix Plumbing 24/7",
        contact_name="Mike Johnson",
        phone="555-0101",
        email="mike@quickfixplumbing.com",
        tier=VendorTier.EMERGENCY,
        location=VendorLocation(
            address="123 Main St",
            city="Boston",
            state="MA",
            zip_code="02101",
            latitude=42.3601,
            longitude=-71.0589,
            service_radius_miles=25
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.PLUMBING,
            secondary_trades=[TradeCategory.GENERAL],
            specializations=["Emergency Repairs", "Gas Lines", "Water Heaters", "Pipe Bursts"],
            certifications=["Master Plumber", "Gas Fitting License", "Backflow Prevention"],
            years_experience=15,
            handles_emergency=True
        ),
        rating=VendorRating(
            overall_rating=4.8,
            total_jobs=342,
            completed_jobs=338,
            response_time_avg_minutes=25,
            quality_score=4.9,
            reliability_score=4.7,
            communication_score=4.8
        ),
        pricing=VendorPricing(
            hourly_rate=125.0,
            emergency_multiplier=1.5,
            weekend_multiplier=1.25,
            after_hours_multiplier=1.3,
            trip_fee=50.0
        ),
        availability=[
            TimeSlot("Monday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Tuesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Wednesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Thursday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Friday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Saturday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Sunday", "00:00", "23:59", is_emergency=True),
        ],
        preferred_vendor=True,
        license_number="MPL-15847",
        insurance_verified=True,
        is_verified=True
    ))
    
    vendors.append(Vendor(
        vendor_id="VND-PL-002",
        company_name="Reliable Plumbing Services",
        contact_name="Sarah Chen",
        phone="555-0102",
        email="sarah@reliableplumbing.com",
        tier=VendorTier.PREMIUM,
        location=VendorLocation(
            address="456 Oak Ave",
            city="Boston",
            state="MA",
            zip_code="02115",
            latitude=42.3434,
            longitude=-71.0892,
            service_radius_miles=20
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.PLUMBING,
            secondary_trades=[],
            specializations=["Drain Cleaning", "Fixture Installation", "Leak Detection", "Sewer Lines"],
            certifications=["Licensed Plumber", "Drain Specialist"],
            years_experience=10,
            handles_emergency=False
        ),
        rating=VendorRating(
            overall_rating=4.6,
            total_jobs=218,
            completed_jobs=215,
            response_time_avg_minutes=90,
            quality_score=4.7,
            reliability_score=4.5,
            communication_score=4.6
        ),
        pricing=VendorPricing(
            hourly_rate=95.0,
            weekend_multiplier=1.15,
            trip_fee=35.0
        ),
        availability=[
            TimeSlot("Monday", "08:00", "17:00"),
            TimeSlot("Tuesday", "08:00", "17:00"),
            TimeSlot("Wednesday", "08:00", "17:00"),
            TimeSlot("Thursday", "08:00", "17:00"),
            TimeSlot("Friday", "08:00", "17:00"),
            TimeSlot("Saturday", "09:00", "13:00"),
        ],
        license_number="PL-10234",
        insurance_verified=True,
        is_verified=True
    ))
    
    vendors.append(Vendor(
        vendor_id="VND-PL-003",
        company_name="Budget Plumbing Co",
        contact_name="Tom Martinez",
        phone="555-0103",
        email="tom@budgetplumbing.com",
        tier=VendorTier.BUDGET,
        location=VendorLocation(
            address="789 Elm St",
            city="Cambridge",
            state="MA",
            zip_code="02139",
            latitude=42.3736,
            longitude=-71.1097,
            service_radius_miles=15
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.PLUMBING,
            secondary_trades=[TradeCategory.GENERAL],
            specializations=["Basic Repairs", "Faucet Replacement", "Toilet Repair"],
            certifications=["Journeyman Plumber"],
            years_experience=5,
            handles_emergency=False
        ),
        rating=VendorRating(
            overall_rating=4.2,
            total_jobs=145,
            completed_jobs=138,
            response_time_avg_minutes=180,
            quality_score=4.0,
            reliability_score=4.3,
            communication_score=4.1
        ),
        pricing=VendorPricing(
            hourly_rate=75.0,
            weekend_multiplier=1.1,
            trip_fee=25.0
        ),
        availability=[
            TimeSlot("Monday", "09:00", "16:00"),
            TimeSlot("Wednesday", "09:00", "16:00"),
            TimeSlot("Friday", "09:00", "16:00"),
            TimeSlot("Saturday", "10:00", "14:00"),
        ],
        license_number="PL-8921",
        insurance_verified=True,
        is_verified=True
    ))
    
    # ==================== ELECTRICAL VENDORS ====================
    
    vendors.append(Vendor(
        vendor_id="VND-EL-001",
        company_name="Elite Electric 24/7",
        contact_name="David Kim",
        phone="555-0201",
        email="david@eliteelectric.com",
        tier=VendorTier.EMERGENCY,
        location=VendorLocation(
            address="321 Electric Blvd",
            city="Boston",
            state="MA",
            zip_code="02118",
            latitude=42.3428,
            longitude=-71.0701,
            service_radius_miles=30
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.ELECTRICAL,
            secondary_trades=[TradeCategory.GENERAL],
            specializations=["Emergency Repairs", "Panel Upgrades", "Circuit Breakers", "Wiring", "Generator Installation"],
            certifications=["Master Electrician", "Licensed Electrical Contractor", "OSHA Certified"],
            years_experience=20,
            handles_emergency=True
        ),
        rating=VendorRating(
            overall_rating=4.9,
            total_jobs=412,
            completed_jobs=410,
            response_time_avg_minutes=20,
            quality_score=5.0,
            reliability_score=4.8,
            communication_score=4.9
        ),
        pricing=VendorPricing(
            hourly_rate=145.0,
            emergency_multiplier=1.6,
            weekend_multiplier=1.3,
            after_hours_multiplier=1.4,
            trip_fee=75.0
        ),
        availability=[
            TimeSlot("Monday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Tuesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Wednesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Thursday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Friday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Saturday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Sunday", "00:00", "23:59", is_emergency=True),
        ],
        preferred_vendor=True,
        license_number="ME-25847",
        insurance_verified=True,
        is_verified=True
    ))
    
    vendors.append(Vendor(
        vendor_id="VND-EL-002",
        company_name="Bright Spark Electrical",
        contact_name="Jennifer Lopez",
        phone="555-0202",
        email="jen@brightspark.com",
        tier=VendorTier.STANDARD,
        location=VendorLocation(
            address="555 Volt St",
            city="Somerville",
            state="MA",
            zip_code="02143",
            latitude=42.3876,
            longitude=-71.0995,
            service_radius_miles=18
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.ELECTRICAL,
            secondary_trades=[],
            specializations=["Outlet Installation", "Lighting", "Appliance Wiring", "Code Compliance"],
            certifications=["Licensed Electrician", "Residential Specialist"],
            years_experience=8,
            handles_emergency=False
        ),
        rating=VendorRating(
            overall_rating=4.5,
            total_jobs=189,
            completed_jobs=185,
            response_time_avg_minutes=120,
            quality_score=4.6,
            reliability_score=4.4,
            communication_score=4.5
        ),
        pricing=VendorPricing(
            hourly_rate=110.0,
            weekend_multiplier=1.2,
            trip_fee=45.0
        ),
        availability=[
            TimeSlot("Monday", "08:00", "18:00"),
            TimeSlot("Tuesday", "08:00", "18:00"),
            TimeSlot("Wednesday", "08:00", "18:00"),
            TimeSlot("Thursday", "08:00", "18:00"),
            TimeSlot("Friday", "08:00", "18:00"),
        ],
        license_number="EL-11234",
        insurance_verified=True,
        is_verified=True
    ))
    
    # ==================== HVAC VENDORS ====================
    
    vendors.append(Vendor(
        vendor_id="VND-HV-001",
        company_name="CoolBreeze HVAC Emergency",
        contact_name="Robert Wilson",
        phone="555-0301",
        email="robert@coolbreeze.com",
        tier=VendorTier.EMERGENCY,
        location=VendorLocation(
            address="888 Climate Dr",
            city="Boston",
            state="MA",
            zip_code="02108",
            latitude=42.3588,
            longitude=-71.0707,
            service_radius_miles=35
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.HVAC,
            secondary_trades=[TradeCategory.GENERAL],
            specializations=["Emergency Heating", "Emergency AC", "Furnace Repair", "Boiler Service", "Heat Pumps"],
            certifications=["HVAC Master License", "EPA 608 Certified", "NATE Certified"],
            years_experience=18,
            handles_emergency=True
        ),
        rating=VendorRating(
            overall_rating=4.7,
            total_jobs=387,
            completed_jobs=382,
            response_time_avg_minutes=35,
            quality_score=4.8,
            reliability_score=4.6,
            communication_score=4.7
        ),
        pricing=VendorPricing(
            hourly_rate=135.0,
            emergency_multiplier=1.5,
            weekend_multiplier=1.25,
            after_hours_multiplier=1.35,
            trip_fee=65.0
        ),
        availability=[
            TimeSlot("Monday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Tuesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Wednesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Thursday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Friday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Saturday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Sunday", "00:00", "23:59", is_emergency=True),
        ],
        preferred_vendor=True,
        license_number="HVAC-18471",
        insurance_verified=True,
        is_verified=True
    ))
    
    vendors.append(Vendor(
        vendor_id="VND-HV-002",
        company_name="ComfortZone HVAC",
        contact_name="Lisa Anderson",
        phone="555-0302",
        email="lisa@comfortzone.com",
        tier=VendorTier.PREMIUM,
        location=VendorLocation(
            address="222 Thermostat Ln",
            city="Brookline",
            state="MA",
            zip_code="02445",
            latitude=42.3318,
            longitude=-71.1212,
            service_radius_miles=20
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.HVAC,
            secondary_trades=[],
            specializations=["AC Maintenance", "Furnace Tune-ups", "Duct Cleaning", "Thermostat Installation"],
            certifications=["HVAC Licensed", "EPA Certified"],
            years_experience=12,
            handles_emergency=False
        ),
        rating=VendorRating(
            overall_rating=4.6,
            total_jobs=256,
            completed_jobs=253,
            response_time_avg_minutes=75,
            quality_score=4.7,
            reliability_score=4.5,
            communication_score=4.6
        ),
        pricing=VendorPricing(
            hourly_rate=115.0,
            weekend_multiplier=1.2,
            trip_fee=50.0
        ),
        availability=[
            TimeSlot("Monday", "07:00", "18:00"),
            TimeSlot("Tuesday", "07:00", "18:00"),
            TimeSlot("Wednesday", "07:00", "18:00"),
            TimeSlot("Thursday", "07:00", "18:00"),
            TimeSlot("Friday", "07:00", "18:00"),
            TimeSlot("Saturday", "08:00", "14:00"),
        ],
        license_number="HVAC-12456",
        insurance_verified=True,
        is_verified=True
    ))
    
    # ==================== APPLIANCE VENDORS ====================
    
    vendors.append(Vendor(
        vendor_id="VND-AP-001",
        company_name="ApplianceFix Pro",
        contact_name="Mark Thompson",
        phone="555-0401",
        email="mark@appliancefix.com",
        tier=VendorTier.PREMIUM,
        location=VendorLocation(
            address="444 Repair Rd",
            city="Boston",
            state="MA",
            zip_code="02116",
            latitude=42.3467,
            longitude=-71.0818,
            service_radius_miles=22
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.APPLIANCE,
            secondary_trades=[TradeCategory.ELECTRICAL],
            specializations=["Refrigerators", "Washers/Dryers", "Dishwashers", "Stoves/Ovens", "Microwaves"],
            certifications=["Appliance Repair Certified", "Factory Authorized"],
            years_experience=14,
            handles_emergency=False
        ),
        rating=VendorRating(
            overall_rating=4.7,
            total_jobs=298,
            completed_jobs=294,
            response_time_avg_minutes=60,
            quality_score=4.8,
            reliability_score=4.6,
            communication_score=4.7
        ),
        pricing=VendorPricing(
            hourly_rate=105.0,
            weekend_multiplier=1.15,
            trip_fee=40.0
        ),
        availability=[
            TimeSlot("Monday", "08:00", "17:00"),
            TimeSlot("Tuesday", "08:00", "17:00"),
            TimeSlot("Wednesday", "08:00", "17:00"),
            TimeSlot("Thursday", "08:00", "17:00"),
            TimeSlot("Friday", "08:00", "17:00"),
            TimeSlot("Saturday", "09:00", "15:00"),
        ],
        license_number="AP-9874",
        insurance_verified=True,
        is_verified=True
    ))
    
    # ==================== GENERAL/HANDYMAN VENDORS ====================
    
    vendors.append(Vendor(
        vendor_id="VND-GN-001",
        company_name="Jack of All Trades Handyman",
        contact_name="James Brown",
        phone="555-0501",
        email="james@jackofalltrades.com",
        tier=VendorTier.STANDARD,
        location=VendorLocation(
            address="777 Handy St",
            city="Boston",
            state="MA",
            zip_code="02127",
            latitude=42.3334,
            longitude=-71.0523,
            service_radius_miles=15
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.GENERAL,
            secondary_trades=[TradeCategory.CARPENTRY, TradeCategory.PAINTING, TradeCategory.DRYWALL],
            specializations=["General Repairs", "Carpentry", "Painting", "Drywall", "Doors/Windows"],
            certifications=["General Contractor", "Insured"],
            years_experience=10,
            handles_emergency=False
        ),
        rating=VendorRating(
            overall_rating=4.4,
            total_jobs=312,
            completed_jobs=305,
            response_time_avg_minutes=100,
            quality_score=4.3,
            reliability_score=4.5,
            communication_score=4.4
        ),
        pricing=VendorPricing(
            hourly_rate=85.0,
            weekend_multiplier=1.1,
            trip_fee=30.0
        ),
        availability=[
            TimeSlot("Monday", "08:00", "16:00"),
            TimeSlot("Tuesday", "08:00", "16:00"),
            TimeSlot("Wednesday", "08:00", "16:00"),
            TimeSlot("Thursday", "08:00", "16:00"),
            TimeSlot("Friday", "08:00", "16:00"),
            TimeSlot("Saturday", "09:00", "13:00"),
        ],
        license_number="GC-5432",
        insurance_verified=True,
        is_verified=True
    ))
    
    # ==================== LOCKSMITH VENDORS ====================
    
    vendors.append(Vendor(
        vendor_id="VND-LK-001",
        company_name="24/7 Secure Locksmith",
        contact_name="Kevin White",
        phone="555-0601",
        email="kevin@securelocksmith.com",
        tier=VendorTier.EMERGENCY,
        location=VendorLocation(
            address="999 Lock Lane",
            city="Boston",
            state="MA",
            zip_code="02114",
            latitude=42.3645,
            longitude=-71.0654,
            service_radius_miles=25
        ),
        expertise=VendorExpertise(
            primary_trade=TradeCategory.LOCKSMITH,
            secondary_trades=[TradeCategory.DOORS],
            specializations=["Emergency Lockouts", "Lock Replacement", "Key Duplication", "Security Systems"],
            certifications=["Licensed Locksmith", "Security Specialist"],
            years_experience=16,
            handles_emergency=True
        ),
        rating=VendorRating(
            overall_rating=4.8,
            total_jobs=456,
            completed_jobs=453,
            response_time_avg_minutes=15,
            quality_score=4.9,
            reliability_score=4.7,
            communication_score=4.8
        ),
        pricing=VendorPricing(
            hourly_rate=120.0,
            emergency_multiplier=1.5,
            weekend_multiplier=1.2,
            after_hours_multiplier=1.3,
            trip_fee=55.0
        ),
        availability=[
            TimeSlot("Monday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Tuesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Wednesday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Thursday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Friday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Saturday", "00:00", "23:59", is_emergency=True),
            TimeSlot("Sunday", "00:00", "23:59", is_emergency=True),
        ],
        preferred_vendor=True,
        license_number="LS-7845",
        insurance_verified=True,
        is_verified=True
    ))
    
    return vendors


def get_vendors_by_trade(trade: str, vendors: List[Vendor] = None) -> List[Vendor]:
    """Filter vendors by trade category."""
    if vendors is None:
        vendors = create_mock_vendors()
    
    return [v for v in vendors if v.expertise.can_handle_trade(trade) and v.is_active]


def get_emergency_vendors(vendors: List[Vendor] = None) -> List[Vendor]:
    """Get vendors that handle emergency calls."""
    if vendors is None:
        vendors = create_mock_vendors()
    
    return [v for v in vendors if v.expertise.handles_emergency and v.is_active]


def get_vendor_by_id(vendor_id: str, vendors: List[Vendor] = None) -> Vendor:
    """Get vendor by ID."""
    if vendors is None:
        vendors = create_mock_vendors()
    
    for vendor in vendors:
        if vendor.vendor_id == vendor_id:
            return vendor
    return None


# Export for easy access
MOCK_VENDORS = create_mock_vendors()




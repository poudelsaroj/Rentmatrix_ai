"""
Vendor Data Models
Defines vendor profiles, availability, expertise, and ratings.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TradeCategory(str, Enum):
    """Trade categories matching the triage system."""
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    HVAC = "HVAC"
    APPLIANCE = "APPLIANCE"
    CARPENTRY = "CARPENTRY"
    PAINTING = "PAINTING"
    FLOORING = "FLOORING"
    ROOFING = "ROOFING"
    MASONRY = "MASONRY"
    PEST_CONTROL = "PEST_CONTROL"
    LOCKSMITH = "LOCKSMITH"
    LANDSCAPING = "LANDSCAPING"
    WINDOWS_GLASS = "WINDOWS_GLASS"
    DOORS = "DOORS"
    DRYWALL = "DRYWALL"
    STRUCTURAL = "STRUCTURAL"
    GENERAL = "GENERAL"


class VendorTier(str, Enum):
    """Vendor service tier."""
    EMERGENCY = "EMERGENCY"  # 24/7, handles emergencies
    PREMIUM = "PREMIUM"      # High-end, excellent ratings
    STANDARD = "STANDARD"    # Reliable, good quality
    BUDGET = "BUDGET"        # Cost-effective


@dataclass
class TimeSlot:
    """Available time slot."""
    day: str          # e.g., "Monday", "2024-12-18"
    start_time: str   # e.g., "09:00"
    end_time: str     # e.g., "17:00"
    is_emergency: bool = False  # Available for emergency calls
    
    def __str__(self):
        emergency = " (Emergency Available)" if self.is_emergency else ""
        return f"{self.day} {self.start_time}-{self.end_time}{emergency}"


@dataclass
class VendorRating:
    """Vendor performance ratings."""
    overall_rating: float  # 1.0-5.0
    total_jobs: int
    completed_jobs: int
    response_time_avg_minutes: int
    quality_score: float  # 1.0-5.0
    reliability_score: float  # 1.0-5.0
    communication_score: float  # 1.0-5.0
    
    @property
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        if self.total_jobs == 0:
            return 0.0
        return (self.completed_jobs / self.total_jobs) * 100


@dataclass
class VendorLocation:
    """Vendor location and service area."""
    address: str
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    service_radius_miles: int


@dataclass
class VendorExpertise:
    """Vendor expertise and specializations."""
    primary_trade: TradeCategory
    secondary_trades: List[TradeCategory] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    years_experience: int = 0
    handles_emergency: bool = False
    
    def can_handle_trade(self, trade: str) -> bool:
        """Check if vendor can handle a trade category."""
        trade_upper = trade.upper()
        if self.primary_trade.value == trade_upper:
            return True
        return any(t.value == trade_upper for t in self.secondary_trades)


@dataclass
class VendorPricing:
    """Vendor pricing structure."""
    hourly_rate: float
    emergency_multiplier: float = 1.5  # 1.5x for emergency
    weekend_multiplier: float = 1.25   # 1.25x for weekends
    after_hours_multiplier: float = 1.3  # 1.3x for after hours
    minimum_charge: float = 0.0
    materials_markup: float = 1.15  # 15% markup on materials
    trip_fee: float = 0.0


@dataclass
class Vendor:
    """Complete vendor profile."""
    vendor_id: str
    company_name: str
    contact_name: str
    phone: str
    email: str
    tier: VendorTier
    location: VendorLocation
    expertise: VendorExpertise
    rating: VendorRating
    pricing: VendorPricing
    availability: List[TimeSlot] = field(default_factory=list)
    
    # Additional metadata
    is_active: bool = True
    is_verified: bool = True
    insurance_verified: bool = True
    license_number: Optional[str] = None
    preferred_vendor: bool = False  # RentMatrix preferred vendor
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vendor to dictionary."""
        return {
            "vendor_id": self.vendor_id,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "phone": self.phone,
            "email": self.email,
            "tier": self.tier.value,
            "location": {
                "address": self.location.address,
                "city": self.location.city,
                "state": self.location.state,
                "zip_code": self.location.zip_code,
                "service_radius_miles": self.location.service_radius_miles
            },
            "expertise": {
                "primary_trade": self.expertise.primary_trade.value,
                "secondary_trades": [t.value for t in self.expertise.secondary_trades],
                "specializations": self.expertise.specializations,
                "certifications": self.expertise.certifications,
                "years_experience": self.expertise.years_experience,
                "handles_emergency": self.expertise.handles_emergency
            },
            "rating": {
                "overall_rating": self.rating.overall_rating,
                "total_jobs": self.rating.total_jobs,
                "completion_rate": round(self.rating.completion_rate, 1),
                "response_time_avg_minutes": self.rating.response_time_avg_minutes,
                "quality_score": self.rating.quality_score,
                "reliability_score": self.rating.reliability_score,
                "communication_score": self.rating.communication_score
            },
            "pricing": {
                "hourly_rate": self.pricing.hourly_rate,
                "emergency_multiplier": self.pricing.emergency_multiplier,
                "trip_fee": self.pricing.trip_fee
            },
            "availability": [str(slot) for slot in self.availability],
            "is_active": self.is_active,
            "preferred_vendor": self.preferred_vendor,
            "license_number": self.license_number
        }
    
    def get_estimated_hourly_cost(self, is_emergency: bool = False, 
                                   is_weekend: bool = False, 
                                   is_after_hours: bool = False) -> float:
        """Calculate estimated hourly cost with multipliers."""
        cost = self.pricing.hourly_rate
        
        if is_emergency:
            cost *= self.pricing.emergency_multiplier
        if is_weekend:
            cost *= self.pricing.weekend_multiplier
        if is_after_hours:
            cost *= self.pricing.after_hours_multiplier
            
        return round(cost, 2)









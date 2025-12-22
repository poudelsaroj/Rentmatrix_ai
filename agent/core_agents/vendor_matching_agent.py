"""
Agent 6: Vendor Matching Agent
Intelligently matches vendors to maintenance requests using LLM reasoning.
"""

from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent
from ..prompts.vendor_matching_prompt import SYSTEM_PROMPT_VENDOR_MATCHING
from ..models.vendor_models import Vendor
from ..data.mock_vendors import MOCK_VENDORS, get_vendors_by_trade


class VendorMatchingAgent(BaseAgent):
    """
    Vendor Matching Agent
    
    Uses LLM to intelligently match vendors to maintenance requests based on:
    - Trade expertise and specializations
    - Location and service area
    - Availability vs tenant preferences
    - Performance ratings and track record
    - Cost considerations
    - Emergency capability (when required)
    
    Output includes:
    - Ranked vendor recommendations (3-5 vendors)
    - Match scores with detailed breakdown
    - Cost estimates
    - Availability analysis
    - Clear reasoning for each recommendation
    """
    
    def __init__(self, model: str = "gpt-5-mini", vendors: List[Vendor] = None):
        """
        Initialize the vendor matching agent.
        
        Args:
            model: LLM model to use for intelligent matching.
            vendors: List of available vendors. If None, uses mock vendors.
        """
        super().__init__(
            name="Vendor Matching Agent",
            model=model,
            temperature=0.2  # Low but not zero - allow some creativity in reasoning
        )
        self.vendors = vendors if vendors is not None else MOCK_VENDORS
    
    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_VENDOR_MATCHING
    
    def build_prompt(
        self,
        triage_output: Dict[str, Any],
        priority_output: Dict[str, Any],
        request_data: Dict[str, Any],
        tenant_preferred_times: List[str],
        property_location: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build the user prompt for vendor matching.
        
        Args:
            triage_output: Parsed JSON from Triage Agent (severity, trade, etc.)
            priority_output: Parsed JSON from Priority Agent (priority_score, etc.)
            request_data: Original maintenance request with context
            tenant_preferred_times: List of tenant's 3 preferred time slots
            property_location: Property location info (city, zip, etc.)
            
        Returns:
            Formatted prompt string for the LLM.
        """
        # Extract key information
        severity = triage_output.get("severity", "MEDIUM")
        trade = triage_output.get("trade", "GENERAL")
        description = request_data.get("request", {}).get("description", "")
        priority_score = priority_output.get("priority_score", 50)
        
        # Get property location
        if property_location is None:
            property_location = {
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101"
            }
        
        # Filter vendors by trade
        eligible_vendors = get_vendors_by_trade(trade, self.vendors)
        
        # If no exact trade match, get all vendors (for general work)
        if not eligible_vendors:
            eligible_vendors = [v for v in self.vendors if v.is_active]
        
        # Format vendor data for LLM
        vendors_formatted = self._format_vendors_for_prompt(eligible_vendors)
        
        # Format tenant preferences
        tenant_times_formatted = "\n".join([f"  - {time}" for time in tenant_preferred_times])
        
        # Build the prompt
        prompt = f"""# MAINTENANCE REQUEST ANALYSIS

## Triage Classification
- **Severity**: {severity}
- **Trade Category**: {trade}
- **Priority Score**: {priority_score}/100

## Request Details
**Description**: {description}

**Key Factors**: {triage_output.get('key_factors', [])}

## Property Location
- **City**: {property_location.get('city', 'Unknown')}
- **State**: {property_location.get('state', 'Unknown')}
- **Zip Code**: {property_location.get('zip_code', 'Unknown')}

## Tenant Preferred Time Slots
{tenant_times_formatted}

## Request Context
{self._format_request_context(request_data)}

---

# AVAILABLE VENDORS ({len(eligible_vendors)} vendors eligible for {trade})

{vendors_formatted}

---

# YOUR TASK

Analyze the maintenance request and available vendors to provide intelligent vendor matching recommendations.

**Remember to:**
1. Consider severity level when prioritizing factors (emergency = speed, routine = value)
2. Match vendor availability with tenant's preferred time slots
3. Ensure vendor can handle the specific trade and severity level
4. Provide 3-5 ranked recommendations with clear reasoning
5. Include cost estimates and highlight trade-offs
6. Note any scheduling challenges or limitations

Provide your vendor matching analysis now in the required JSON format.
"""
        
        return prompt
    
    def _format_vendors_for_prompt(self, vendors: List[Vendor]) -> str:
        """Format vendor list for the LLM prompt."""
        if not vendors:
            return "No eligible vendors found."
        
        vendor_sections = []
        for i, vendor in enumerate(vendors, 1):
            section = f"""## Vendor {i}: {vendor.company_name} ({vendor.vendor_id})

**Contact**: {vendor.contact_name} | Phone: {vendor.phone} | Email: {vendor.email}

**Tier**: {vendor.tier.value}
{" ⭐ PREFERRED VENDOR" if vendor.preferred_vendor else ""}

**Expertise**:
- Primary Trade: {vendor.expertise.primary_trade.value}
- Secondary Trades: {", ".join([t.value for t in vendor.expertise.secondary_trades]) if vendor.expertise.secondary_trades else "None"}
- Specializations: {", ".join(vendor.expertise.specializations) if vendor.expertise.specializations else "None"}
- Certifications: {", ".join(vendor.expertise.certifications) if vendor.expertise.certifications else "None"}
- Years Experience: {vendor.expertise.years_experience}
- Handles Emergency: {"YES (24/7)" if vendor.expertise.handles_emergency else "NO"}

**Location & Service Area**:
- Located in: {vendor.location.city}, {vendor.location.state} {vendor.location.zip_code}
- Service Radius: {vendor.location.service_radius_miles} miles
- Address: {vendor.location.address}

**Ratings & Performance**:
- Overall Rating: {vendor.rating.overall_rating}/5.0 ⭐
- Total Jobs: {vendor.rating.total_jobs}
- Completion Rate: {vendor.rating.completion_rate:.1f}%
- Avg Response Time: {vendor.rating.response_time_avg_minutes} minutes
- Quality Score: {vendor.rating.quality_score}/5.0
- Reliability Score: {vendor.rating.reliability_score}/5.0
- Communication Score: {vendor.rating.communication_score}/5.0

**Pricing**:
- Base Hourly Rate: ${vendor.pricing.hourly_rate:.2f}/hour
- Emergency Multiplier: {vendor.pricing.emergency_multiplier}x
- Weekend Multiplier: {vendor.pricing.weekend_multiplier}x
- After Hours Multiplier: {vendor.pricing.after_hours_multiplier}x
- Trip Fee: ${vendor.pricing.trip_fee:.2f}

**Availability**:
{self._format_availability(vendor.availability)}

**Verification**:
- License: {vendor.license_number or "N/A"}
- Insurance Verified: {"YES" if vendor.insurance_verified else "NO"}
- Platform Verified: {"YES" if vendor.is_verified else "NO"}

---
"""
            vendor_sections.append(section)
        
        return "\n".join(vendor_sections)
    
    def _format_availability(self, availability: List) -> str:
        """Format vendor availability schedule."""
        if not availability:
            return "  - Availability not specified"
        
        lines = []
        for slot in availability:
            emergency = " [EMERGENCY AVAILABLE]" if slot.is_emergency else ""
            lines.append(f"  - {slot.day}: {slot.start_time}-{slot.end_time}{emergency}")
        
        return "\n".join(lines)
    
    def _format_request_context(self, request_data: Dict[str, Any]) -> str:
        """Format additional request context."""
        context = request_data.get("context", {})
        
        lines = []
        
        # Weather
        weather = context.get("weather", {})
        if weather:
            lines.append(f"**Weather**: {weather.get('temperature', 'N/A')}°F, {weather.get('condition', 'Unknown')}")
        
        # Timing
        timing = context.get("timing", {})
        if timing:
            time_notes = []
            if timing.get("is_after_hours"):
                time_notes.append("After Hours")
            if timing.get("is_weekend"):
                time_notes.append("Weekend")
            if timing.get("is_late_night"):
                time_notes.append("Late Night")
            if timing.get("is_holiday"):
                time_notes.append("Holiday")
            
            if time_notes:
                lines.append(f"**Timing**: {', '.join(time_notes)}")
            lines.append(f"**Day/Time**: {timing.get('day_of_week', 'Unknown')}, Hour {timing.get('hour', 'N/A')}")
        
        # Tenant
        tenant = context.get("tenant", {})
        if tenant:
            tenant_notes = []
            if tenant.get("is_elderly"):
                tenant_notes.append("Elderly")
            if tenant.get("has_infant"):
                tenant_notes.append("Has Infant")
            if tenant.get("has_medical_condition"):
                tenant_notes.append("Medical Condition")
            if tenant.get("is_pregnant"):
                tenant_notes.append("Pregnant")
            
            if tenant_notes:
                lines.append(f"**Tenant**: {', '.join(tenant_notes)} ({tenant.get('occupant_count', 'Unknown')} occupants)")
        
        # Property
        property_info = context.get("property", {})
        if property_info:
            lines.append(f"**Property**: {property_info.get('type', 'Unknown')}, {property_info.get('age', 'Unknown')} years old")
        
        return "\n".join(lines) if lines else "No additional context provided."







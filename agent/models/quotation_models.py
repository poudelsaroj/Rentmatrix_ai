"""
Quotation Data Models
Defines models for vendor quotations, extracted data, and comparison results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class QuotationStatus(str, Enum):
    """Status of a quotation."""
    SUBMITTED = "submitted"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


@dataclass
class QuotationData:
    """Extracted structured data from a quotation."""
    total_price: Optional[float] = None
    currency: str = "USD"
    timeline_days: Optional[int] = None
    timeline_description: Optional[str] = None  # e.g., "3-5 business days"
    materials: List[str] = field(default_factory=list)
    warranty_months: Optional[int] = None
    warranty_description: Optional[str] = None  # e.g., "12 months parts and labor"
    payment_terms: Optional[str] = None  # e.g., "50% upfront, 50% on completion"
    special_conditions: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    labor_cost: Optional[float] = None
    materials_cost: Optional[float] = None
    tax_amount: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_price": self.total_price,
            "currency": self.currency,
            "timeline_days": self.timeline_days,
            "timeline_description": self.timeline_description,
            "materials": self.materials,
            "warranty_months": self.warranty_months,
            "warranty_description": self.warranty_description,
            "payment_terms": self.payment_terms,
            "special_conditions": self.special_conditions,
            "notes": self.notes,
            "labor_cost": self.labor_cost,
            "materials_cost": self.materials_cost,
            "tax_amount": self.tax_amount
        }


@dataclass
class Quotation:
    """Vendor quotation with images and extracted data."""
    quotation_id: str
    request_id: str
    vendor_id: str
    images: List[str] = field(default_factory=list)  # Base64 encoded or file paths
    extracted_data: Optional[QuotationData] = None
    vendor_notes: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    status: QuotationStatus = QuotationStatus.SUBMITTED
    confidence: float = 0.0  # Confidence in extraction accuracy
    extraction_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "quotation_id": self.quotation_id,
            "request_id": self.request_id,
            "vendor_id": self.vendor_id,
            "images_count": len(self.images),
            "extracted_data": self.extracted_data.to_dict() if self.extracted_data else None,
            "vendor_notes": self.vendor_notes,
            "submitted_at": self.submitted_at.isoformat(),
            "status": self.status.value,
            "confidence": self.confidence,
            "extraction_errors": self.extraction_errors
        }


@dataclass
class VendorQuotationSummary:
    """Summary of a vendor quotation for comparison."""
    vendor_id: str
    company_name: str
    quotation_id: str
    total_price: float
    currency: str
    timeline_days: Optional[int]
    warranty_months: Optional[int]
    payment_terms: Optional[str]
    rank: int = 0
    extracted_data: Optional[QuotationData] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "vendor_id": self.vendor_id,
            "company_name": self.company_name,
            "quotation_id": self.quotation_id,
            "total_price": self.total_price,
            "currency": self.currency,
            "timeline_days": self.timeline_days,
            "warranty_months": self.warranty_months,
            "payment_terms": self.payment_terms,
            "rank": self.rank
        }
        if self.extracted_data:
            result["extracted_data"] = self.extracted_data.to_dict()
        return result


@dataclass
class QuotationComparison:
    """Comparison result of three vendor quotations."""
    request_id: str
    vendor_quotations: List[VendorQuotationSummary]
    comparison_summary: Dict[str, Any]
    recommendation: Dict[str, Any]
    confidence: float
    red_flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "comparison": {
                "vendor_quotations": [vq.to_dict() for vq in self.vendor_quotations],
                "summary": self.comparison_summary,
                "recommendation": self.recommendation,
                "red_flags": self.red_flags
            },
            "confidence": self.confidence
        }


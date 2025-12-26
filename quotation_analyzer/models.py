"""
Data Models for Quotation Analyzer
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ExtractionMethod(str, Enum):
    """Method used for extraction."""
    OCR = "ocr"
    LLM = "llm"


@dataclass
class QuotationResult:
    """Extracted data from a single quotation image."""
    vendor_name: Optional[str] = None
    total_price: Optional[float] = None
    currency: str = "USD"
    items: List[Dict[str, Any]] = field(default_factory=list)  # [{name, quantity, unit_price, total}]
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    labor_cost: Optional[float] = None
    materials_cost: Optional[float] = None
    timeline_days: Optional[int] = None
    timeline_description: Optional[str] = None
    warranty_months: Optional[int] = None
    warranty_description: Optional[str] = None
    payment_terms: Optional[str] = None
    validity_days: Optional[int] = None
    special_conditions: List[str] = field(default_factory=list)
    contact_info: Optional[str] = None
    date_issued: Optional[str] = None
    raw_text: Optional[str] = None  # Raw OCR text for debugging
    extraction_method: ExtractionMethod = ExtractionMethod.OCR
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vendor_name": self.vendor_name,
            "total_price": self.total_price,
            "currency": self.currency,
            "items": self.items,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "tax_rate": self.tax_rate,
            "labor_cost": self.labor_cost,
            "materials_cost": self.materials_cost,
            "timeline_days": self.timeline_days,
            "timeline_description": self.timeline_description,
            "warranty_months": self.warranty_months,
            "warranty_description": self.warranty_description,
            "payment_terms": self.payment_terms,
            "validity_days": self.validity_days,
            "special_conditions": self.special_conditions,
            "contact_info": self.contact_info,
            "date_issued": self.date_issued,
            "extraction_method": self.extraction_method.value,
            "confidence": self.confidence,
            "errors": self.errors
        }


@dataclass
class VendorQuotation:
    """A vendor's quotation with extracted data."""
    vendor_id: str
    vendor_name: str
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    extracted_data: Optional[QuotationResult] = None
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "extracted_data": self.extracted_data.to_dict() if self.extracted_data else None,
            "rank": self.rank
        }


@dataclass
class ComparisonResult:
    """Comparison of 3 vendor quotations."""
    quotations: List[VendorQuotation] = field(default_factory=list)
    ranked_vendors: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    red_flags: List[str] = field(default_factory=list)
    extraction_method: ExtractionMethod = ExtractionMethod.OCR
    overall_confidence: float = 0.0
    processed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quotations": [q.to_dict() for q in self.quotations],
            "ranked_vendors": self.ranked_vendors,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "red_flags": self.red_flags,
            "extraction_method": self.extraction_method.value,
            "overall_confidence": self.overall_confidence,
            "processed_at": self.processed_at.isoformat()
        }

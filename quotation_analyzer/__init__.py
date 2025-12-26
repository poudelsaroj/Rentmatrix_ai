"""
Quotation Analyzer Module
Analyzes vendor quotation images using OCR or LLM (toggle-based).
Supports 3 vendors with 3 different quotation photos.
"""

from .models import QuotationResult, VendorQuotation, ComparisonResult
from .quotation_service import QuotationService

__all__ = [
    "QuotationResult",
    "VendorQuotation",
    "ComparisonResult",
    "QuotationService"
]

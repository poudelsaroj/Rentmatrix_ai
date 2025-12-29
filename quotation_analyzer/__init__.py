"""
Quotation Analyzer Module
Analyzes vendor quotation images using OCR or LLM (toggle-based).
Supports 3 vendors with 3 different quotation photos.
"""

from .models import QuotationResult, VendorQuotation, ComparisonResult, TimeSlot, ExtractionMethod
from .quotation_service import QuotationService
from .mock_data import (
    MOCK_USERS,
    MOCK_VENDORS_FOR_QUOTATION,
    MOCK_MAINTENANCE_REQUESTS,
    create_mock_user_availability,
    create_mock_quotation_results,
    create_mock_vendor_quotations,
    create_mock_comparison_request,
    create_mock_comparison_result,
    get_mock_user,
    get_mock_vendor_for_quotation,
    get_mock_request,
    get_all_mock_data
)

__all__ = [
    # Models
    "QuotationResult",
    "VendorQuotation",
    "ComparisonResult",
    "TimeSlot",
    "ExtractionMethod",
    # Service
    "QuotationService",
    # Mock Data
    "MOCK_USERS",
    "MOCK_VENDORS_FOR_QUOTATION",
    "MOCK_MAINTENANCE_REQUESTS",
    "create_mock_user_availability",
    "create_mock_quotation_results",
    "create_mock_vendor_quotations",
    "create_mock_comparison_request",
    "create_mock_comparison_result",
    "get_mock_user",
    "get_mock_vendor_for_quotation",
    "get_mock_request",
    "get_all_mock_data"
]

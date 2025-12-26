"""
LLM Extractor using OpenAI gpt-5 Vision
Extracts structured data from quotation images using vision model.
"""

import os
import json
import base64
from typing import Union, Dict, Any, Optional
from openai import OpenAI

from .base_extractor import BaseExtractor
from ..models import QuotationResult, ExtractionMethod


EXTRACTION_PROMPT = """You are an expert at analyzing vendor quotation documents.
Extract all relevant information from this quotation image and return it as JSON.

Extract the following fields:
- vendor_name: Company/vendor name
- total_price: Total amount (number only)
- currency: Currency code (USD, EUR, etc.)
- items: Array of line items, each with {name, quantity, unit_price, total}
- subtotal: Subtotal before tax
- tax_amount: Tax amount
- tax_rate: Tax percentage rate
- labor_cost: Labor/service cost if separately listed
- materials_cost: Materials/parts cost if separately listed
- timeline_days: Estimated completion time in days
- timeline_description: Text description of timeline
- warranty_months: Warranty period in months
- warranty_description: Warranty terms description
- payment_terms: Payment terms (e.g., "50% upfront, 50% on completion")
- validity_days: How long the quote is valid
- special_conditions: Array of special terms/conditions
- contact_info: Phone, email, or address
- date_issued: Date on the quotation
- confidence: Your confidence in the extraction (0.0 to 1.0)

Return ONLY valid JSON. If a field cannot be determined, use null.
For arrays, return empty array [] if no items found.

Example response:
{
    "vendor_name": "ABC Plumbing Co.",
    "total_price": 1250.00,
    "currency": "USD",
    "items": [
        {"name": "Pipe replacement", "quantity": 1, "unit_price": 800, "total": 800},
        {"name": "Labor", "quantity": 4, "unit_price": 75, "total": 300}
    ],
    "subtotal": 1100.00,
    "tax_amount": 150.00,
    "tax_rate": 13.64,
    "labor_cost": 300.00,
    "materials_cost": 800.00,
    "timeline_days": 3,
    "timeline_description": "3 business days",
    "warranty_months": 12,
    "warranty_description": "12 months parts and labor",
    "payment_terms": "50% deposit required",
    "validity_days": 30,
    "special_conditions": ["Emergency rates may apply after hours"],
    "contact_info": "(555) 123-4567",
    "date_issued": "2024-12-20",
    "confidence": 0.95
}
"""


class LLMExtractor(BaseExtractor):
    """
    OpenAI gpt-5 Vision-based quotation extractor.

    Uses vision capabilities to understand and extract structured
    data from quotation images with high accuracy.
    """

    def __init__(self, model: str = "gpt-5", api_key: Optional[str] = None):
        """
        Initialize the LLM extractor.

        Args:
            model: OpenAI vision model to use (default: gpt-5)
            api_key: OpenAI API key (optional, uses env var if not provided)
        """
        self.model = model
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def get_method_name(self) -> str:
        return f"OpenAI {self.model}"

    async def extract(self, image: Union[str, bytes]) -> QuotationResult:
        """
        Extract quotation data from an image using gpt-5 Vision.

        Args:
            image: File path, base64 string, or raw bytes

        Returns:
            QuotationResult with extracted data
        """
        try:
            # Prepare image for API
            image_content = self._prepare_image(image)

            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document analyzer. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": EXTRACTION_PROMPT},
                            {"type": "image_url", "image_url": {"url": image_content}}
                        ]
                    }
                ],
                max_completion_tokens=2000
            )

            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)

            # Convert to QuotationResult
            return self._dict_to_result(data)

        except json.JSONDecodeError as e:
            return QuotationResult(
                extraction_method=ExtractionMethod.LLM,
                confidence=0.0,
                errors=[f"JSON parsing error: {str(e)}"]
            )
        except Exception as e:
            return QuotationResult(
                extraction_method=ExtractionMethod.LLM,
                confidence=0.0,
                errors=[f"LLM extraction failed: {str(e)}"]
            )

    def _prepare_image(self, image: Union[str, bytes]) -> str:
        """Prepare image for OpenAI API."""
        if isinstance(image, bytes):
            # Raw bytes - encode to base64
            b64 = base64.b64encode(image).decode('utf-8')
            return f"data:image/png;base64,{b64}"

        if isinstance(image, str):
            # Check if already a data URI
            if image.startswith("data:image"):
                return image

            # Check if URL
            if image.startswith("http"):
                return image

            # Check if base64 without prefix
            if len(image) > 500 and not image.startswith("/") and not image.startswith("C:"):
                return f"data:image/png;base64,{image}"

            # File path - read and encode
            with open(image, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')

            # Determine mime type from extension
            if image.lower().endswith('.png'):
                mime = "image/png"
            elif image.lower().endswith('.jpg') or image.lower().endswith('.jpeg'):
                mime = "image/jpeg"
            elif image.lower().endswith('.gif'):
                mime = "image/gif"
            elif image.lower().endswith('.webp'):
                mime = "image/webp"
            else:
                mime = "image/png"

            return f"data:{mime};base64,{b64}"

        raise ValueError(f"Unsupported image type: {type(image)}")

    def _dict_to_result(self, data: Dict[str, Any]) -> QuotationResult:
        """Convert API response dict to QuotationResult."""
        return QuotationResult(
            vendor_name=data.get("vendor_name"),
            total_price=self._safe_float(data.get("total_price")),
            currency=data.get("currency", "USD"),
            items=data.get("items", []),
            subtotal=self._safe_float(data.get("subtotal")),
            tax_amount=self._safe_float(data.get("tax_amount")),
            tax_rate=self._safe_float(data.get("tax_rate")),
            labor_cost=self._safe_float(data.get("labor_cost")),
            materials_cost=self._safe_float(data.get("materials_cost")),
            timeline_days=self._safe_int(data.get("timeline_days")),
            timeline_description=data.get("timeline_description"),
            warranty_months=self._safe_int(data.get("warranty_months")),
            warranty_description=data.get("warranty_description"),
            payment_terms=data.get("payment_terms"),
            validity_days=self._safe_int(data.get("validity_days")),
            special_conditions=data.get("special_conditions", []),
            contact_info=data.get("contact_info"),
            date_issued=data.get("date_issued"),
            extraction_method=ExtractionMethod.LLM,
            confidence=min(1.0, max(0.0, float(data.get("confidence", 0.8)))),
            errors=[]
        )

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

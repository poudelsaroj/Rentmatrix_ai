"""
Quotation Analysis Agent
Extracts structured data from vendor quotation images using vision models.
"""

import json
import base64
from typing import Any, Dict, List, Optional
from openai import OpenAI
from .base_agent import BaseAgent
from ..prompts.quotation_analysis_prompt import SYSTEM_PROMPT_QUOTATION_ANALYSIS
from ..models.quotation_models import QuotationData, QuotationStatus


class QuotationAnalysisAgent(BaseAgent):
    """
    Quotation Analysis Agent
    
    Uses OpenAI Vision API (GPT-4 Vision) to extract structured data from
    vendor quotation images. Supports PDF, PNG, JPG formats.
    """
    
    def __init__(self, model: str = "gpt-5", vision_model: str = "gpt-5"):
        """
        Initialize the quotation analysis agent.
        
        Args:
            model: Base model name (for compatibility with BaseAgent)
            vision_model: Vision model to use for image analysis (default: gpt-5)
        """
        super().__init__(
            name="Quotation Analysis Agent",
            model=model,
            temperature=0.1  # Low temperature for consistent extraction
        )
        self.vision_model = vision_model
        self.client = OpenAI()
    
    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_QUOTATION_ANALYSIS
    
    async def analyze_quotation_images(
        self,
        images: List[str],
        request_id: Optional[str] = None,
        vendor_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze quotation images and extract structured data.
        
        Args:
            images: List of base64-encoded images or image URLs
            request_id: Optional request ID for context
            vendor_notes: Optional text notes from vendor
        
        Returns:
            Dictionary with extracted data and confidence score
        """
        # Prepare image content for OpenAI Vision API
        image_contents = []
        for img in images:
            # Check if image is base64 encoded or a URL
            if img.startswith("data:image") or img.startswith("http"):
                # URL or data URI
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
            else:
                # Assume base64 encoded
                # Ensure it has the data URI prefix
                if not img.startswith("data:"):
                    img = f"data:image/png;base64,{img}"
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
        
        # Build the prompt
        prompt = self._build_analysis_prompt(request_id, vendor_notes)
        
        # Prepare messages for OpenAI API
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ] + image_contents
            }
        ]
        
        try:
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            extracted_data = json.loads(content)
            
            # Validate and clean the extracted data
            cleaned_data = self._clean_extracted_data(extracted_data)
            
            return cleaned_data
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return error
            return {
                "total_price": None,
                "currency": "USD",
                "timeline_days": None,
                "timeline_description": None,
                "materials": [],
                "warranty_months": None,
                "warranty_description": None,
                "payment_terms": None,
                "special_conditions": [],
                "notes": vendor_notes,
                "labor_cost": None,
                "materials_cost": None,
                "tax_amount": None,
                "extraction_errors": [f"JSON parsing error: {str(e)}"],
                "confidence": 0.0
            }
        except Exception as e:
            # Handle other errors
            return {
                "total_price": None,
                "currency": "USD",
                "timeline_days": None,
                "timeline_description": None,
                "materials": [],
                "warranty_months": None,
                "warranty_description": None,
                "payment_terms": None,
                "special_conditions": [],
                "notes": vendor_notes,
                "labor_cost": None,
                "materials_cost": None,
                "tax_amount": None,
                "extraction_errors": [f"Extraction error: {str(e)}"],
                "confidence": 0.0
            }
    
    def _build_analysis_prompt(
        self,
        request_id: Optional[str] = None,
        vendor_notes: Optional[str] = None
    ) -> str:
        """Build the analysis prompt with context."""
        prompt_parts = [
            "Please analyze the vendor quotation image(s) and extract all structured data."
        ]
        
        if request_id:
            prompt_parts.append(f"\nRequest ID: {request_id}")
        
        if vendor_notes:
            prompt_parts.append(f"\nVendor Notes: {vendor_notes}")
        
        prompt_parts.append(
            "\nExtract all available information including price, timeline, materials, "
            "warranty, payment terms, and any special conditions."
        )
        
        return "\n".join(prompt_parts)
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted data."""
        cleaned = {
            "total_price": self._safe_float(data.get("total_price")),
            "currency": data.get("currency", "USD").upper(),
            "timeline_days": self._safe_int(data.get("timeline_days")),
            "timeline_description": data.get("timeline_description"),
            "materials": data.get("materials", []),
            "warranty_months": self._safe_int(data.get("warranty_months")),
            "warranty_description": data.get("warranty_description"),
            "payment_terms": data.get("payment_terms"),
            "special_conditions": data.get("special_conditions", []),
            "notes": data.get("notes"),
            "labor_cost": self._safe_float(data.get("labor_cost")),
            "materials_cost": self._safe_float(data.get("materials_cost")),
            "tax_amount": self._safe_float(data.get("tax_amount")),
            "extraction_errors": data.get("extraction_errors", []),
            "confidence": max(0.0, min(1.0, float(data.get("confidence", 0.0))))
        }
        
        # Ensure materials is a list
        if not isinstance(cleaned["materials"], list):
            cleaned["materials"] = []
        
        # Ensure special_conditions is a list
        if not isinstance(cleaned["special_conditions"], list):
            cleaned["special_conditions"] = []
        
        return cleaned
    
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
    
    def build_prompt(self, **kwargs) -> str:
        """Build prompt for compatibility with BaseAgent interface."""
        return self._build_analysis_prompt(
            request_id=kwargs.get("request_id"),
            vendor_notes=kwargs.get("vendor_notes")
        )
    
    async def run(self, input_prompt: str) -> Any:
        """
        Override run method for compatibility with BaseAgent interface.
        Note: analyze_quotation_images() should be used directly for image analysis.
        """
        # This method is not typically used for quotation analysis
        # analyze_quotation_images() should be called directly
        # But we implement it for interface compatibility
        return await super().run(input_prompt)


"""
Quotation Comparison Agent
Compares three vendor quotations and provides recommendations.
"""

import json
from typing import Any, Dict, List
from .base_agent import BaseAgent
from ..prompts.quotation_comparison_prompt import SYSTEM_PROMPT_QUOTATION_COMPARISON
from ..models.quotation_models import (
    Quotation,
    VendorQuotationSummary,
    QuotationComparison
)


class QuotationComparisonAgent(BaseAgent):
    """
    Quotation Comparison Agent
    
    Compares three vendor quotations and provides recommendations based primarily
    on price, with secondary factors including timeline, warranty, and terms.
    """
    
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(
            name="Quotation Comparison Agent",
            model=model,
            temperature=0.2  # Low temperature for consistent comparisons
        )
    
    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_QUOTATION_COMPARISON
    
    async def compare_quotations(
        self,
        quotations: List[Quotation],
        vendor_names: Dict[str, str]
    ) -> QuotationComparison:
        """
        Compare three vendor quotations and generate recommendation.
        
        Args:
            quotations: List of 3 Quotation objects to compare
            vendor_names: Dictionary mapping vendor_id to company_name
        
        Returns:
            QuotationComparison object with comparison results
        """
        if len(quotations) != 3:
            raise ValueError("Exactly 3 quotations are required for comparison")
        
        # Extract request_id (should be same for all)
        request_id = quotations[0].request_id
        
        # Build comparison prompt
        prompt = self._build_comparison_prompt(quotations, vendor_names)
        
        # Run the agent
        result = await self.run(prompt)
        
        # Parse the JSON response
        try:
            if isinstance(result, str):
                comparison_data = json.loads(result)
            else:
                comparison_data = result
            
            # Build VendorQuotationSummary objects
            vendor_quotations = []
            for vq_data in comparison_data.get("vendor_quotations", []):
                # Find the original quotation
                quotation = next(
                    (q for q in quotations if q.quotation_id == vq_data.get("quotation_id")),
                    None
                )
                
                vendor_quotations.append(
                    VendorQuotationSummary(
                        vendor_id=vq_data.get("vendor_id"),
                        company_name=vq_data.get("company_name", vendor_names.get(vq_data.get("vendor_id"), "Unknown")),
                        quotation_id=vq_data.get("quotation_id"),
                        total_price=vq_data.get("total_price", 0.0),
                        currency=vq_data.get("currency", "USD"),
                        timeline_days=vq_data.get("timeline_days"),
                        warranty_months=vq_data.get("warranty_months"),
                        payment_terms=vq_data.get("payment_terms"),
                        rank=vq_data.get("rank", 0),
                        extracted_data=quotation.extracted_data if quotation else None
                    )
                )
            
            # Create QuotationComparison object
            comparison = QuotationComparison(
                request_id=request_id,
                vendor_quotations=vendor_quotations,
                comparison_summary=comparison_data.get("summary", {}),
                recommendation=comparison_data.get("recommendation", {}),
                confidence=comparison_data.get("confidence", 0.0),
                red_flags=comparison_data.get("red_flags", [])
            )
            
            return comparison
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback: create basic comparison from data
            return self._create_fallback_comparison(quotations, vendor_names, str(e))
    
    def _build_comparison_prompt(
        self,
        quotations: List[Quotation],
        vendor_names: Dict[str, str]
    ) -> str:
        """Build the comparison prompt with quotation data."""
        prompt_parts = [
            "# QUOTATION COMPARISON REQUEST",
            f"\nRequest ID: {quotations[0].request_id}",
            "\nCompare the following three vendor quotations and provide a recommendation.",
            "\n## QUOTATIONS TO COMPARE:\n"
        ]
        
        for i, quotation in enumerate(quotations, 1):
            company_name = vendor_names.get(quotation.vendor_id, "Unknown Vendor")
            prompt_parts.append(f"\n### Quotation {i}: {company_name} ({quotation.vendor_id})")
            prompt_parts.append(f"Quotation ID: {quotation.quotation_id}")
            
            if quotation.extracted_data:
                data = quotation.extracted_data
                prompt_parts.append(f"- Total Price: {data.total_price} {data.currency}" if data.total_price else "- Total Price: Not specified")
                prompt_parts.append(f"- Timeline: {data.timeline_description or (f'{data.timeline_days} days' if data.timeline_days else 'Not specified')}")
                prompt_parts.append(f"- Warranty: {data.warranty_description or (f'{data.warranty_months} months' if data.warranty_months else 'Not specified')}")
                prompt_parts.append(f"- Payment Terms: {data.payment_terms or 'Not specified'}")
                if data.materials:
                    prompt_parts.append(f"- Materials: {', '.join(data.materials)}")
                if data.special_conditions:
                    prompt_parts.append(f"- Special Conditions: {', '.join(data.special_conditions)}")
                if data.extraction_errors:
                    prompt_parts.append(f"- Extraction Errors: {', '.join(data.extraction_errors)}")
            else:
                prompt_parts.append("- Status: Data extraction failed or incomplete")
            
            if quotation.vendor_notes:
                prompt_parts.append(f"- Vendor Notes: {quotation.vendor_notes}")
            
            prompt_parts.append("")
        
        prompt_parts.append(
            "\n## YOUR TASK\n"
            "Compare these three quotations primarily on price (as requested), "
            "with secondary consideration of timeline, warranty, and payment terms. "
            "Provide a recommendation with clear reasoning.\n"
        )
        
        return "\n".join(prompt_parts)
    
    def _create_fallback_comparison(
        self,
        quotations: List[Quotation],
        vendor_names: Dict[str, str],
        error: str
    ) -> QuotationComparison:
        """Create a fallback comparison when parsing fails."""
        # Sort by price (if available)
        sorted_quotations = sorted(
            quotations,
            key=lambda q: q.extracted_data.total_price if q.extracted_data and q.extracted_data.total_price else float('inf')
        )
        
        vendor_quotations = []
        prices = []
        
        for i, quotation in enumerate(sorted_quotations, 1):
            data = quotation.extracted_data
            price = data.total_price if data and data.total_price else None
            
            if price:
                prices.append(price)
            
            vendor_quotations.append(
                VendorQuotationSummary(
                    vendor_id=quotation.vendor_id,
                    company_name=vendor_names.get(quotation.vendor_id, "Unknown"),
                    quotation_id=quotation.quotation_id,
                    total_price=price or 0.0,
                    currency=data.currency if data else "USD",
                    timeline_days=data.timeline_days if data else None,
                    warranty_months=data.warranty_months if data else None,
                    payment_terms=data.payment_terms if data else None,
                    rank=i,
                    extracted_data=data
                )
            )
        
        # Calculate price range
        price_range = {
            "min": min(prices) if prices else 0.0,
            "max": max(prices) if prices else 0.0,
            "avg": sum(prices) / len(prices) if prices else 0.0
        }
        
        # Recommend lowest price (if available)
        recommended = vendor_quotations[0] if vendor_quotations else None
        
        return QuotationComparison(
            request_id=quotations[0].request_id,
            vendor_quotations=vendor_quotations,
            comparison_summary={
                "lowest_price": vendor_quotations[0].vendor_id if vendor_quotations else None,
                "highest_price": vendor_quotations[-1].vendor_id if vendor_quotations else None,
                "fastest_timeline": None,
                "best_warranty": None,
                "price_range": price_range,
                "price_difference_percent": 0.0
            },
            recommendation={
                "recommended_vendor_id": recommended.vendor_id if recommended else None,
                "reason": f"Fallback comparison (parsing error: {error}). Recommended lowest price option.",
                "confidence": 0.5
            },
            confidence=0.5,
            red_flags=[f"Comparison parsing error: {error}"]
        )
    
    def build_prompt(self, **kwargs) -> str:
        """Build prompt for compatibility with BaseAgent interface."""
        quotations = kwargs.get("quotations", [])
        vendor_names = kwargs.get("vendor_names", {})
        return self._build_comparison_prompt(quotations, vendor_names)


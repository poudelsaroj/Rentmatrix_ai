"""
Quotation Service
Main service for analyzing and comparing vendor quotations.
Supports toggle between OCR and LLM extraction methods.
"""

from typing import List, Dict, Any, Optional, Union
from .models import (
    QuotationResult,
    VendorQuotation,
    ComparisonResult,
    ExtractionMethod
)
from .extractors.ocr_extractor import OCRExtractor
from .extractors.llm_extractor import LLMExtractor


class QuotationService:
    """
    Main service for quotation analysis.

    Supports:
    - Toggle between OCR (Tesseract) and LLM (gpt-5 Vision)
    - Analyze single quotation images
    - Compare 3 vendor quotations with ranking
    """

    def __init__(
        self,
        use_llm: bool = False,
        llm_model: str = "gpt-5",
        tesseract_cmd: Optional[str] = None
    ):
        """
        Initialize the quotation service.

        Args:
            use_llm: If True, use LLM (gpt-5 Vision). If False, use OCR (Tesseract)
            llm_model: OpenAI model for LLM extraction
            tesseract_cmd: Path to Tesseract executable (for OCR mode)
        """
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.tesseract_cmd = tesseract_cmd

        # Initialize extractors lazily
        self._ocr_extractor = None
        self._llm_extractor = None

    @property
    def ocr_extractor(self) -> OCRExtractor:
        """Get or create OCR extractor."""
        if self._ocr_extractor is None:
            self._ocr_extractor = OCRExtractor(tesseract_cmd=self.tesseract_cmd)
        return self._ocr_extractor

    @property
    def llm_extractor(self) -> LLMExtractor:
        """Get or create LLM extractor."""
        if self._llm_extractor is None:
            self._llm_extractor = LLMExtractor(model=self.llm_model)
        return self._llm_extractor

    def set_extraction_method(self, use_llm: bool) -> None:
        """Toggle extraction method."""
        self.use_llm = use_llm

    async def analyze_single(
        self,
        image: Union[str, bytes],
        vendor_id: str,
        vendor_name: str
    ) -> VendorQuotation:
        """
        Analyze a single quotation image.

        Args:
            image: Image file path, base64 string, or bytes
            vendor_id: Unique vendor identifier
            vendor_name: Vendor/company name

        Returns:
            VendorQuotation with extracted data
        """
        # Choose extractor based on toggle
        if self.use_llm:
            extractor = self.llm_extractor
        else:
            extractor = self.ocr_extractor

        # Extract data
        result = await extractor.extract(image)

        # Override vendor name if not extracted
        if not result.vendor_name:
            result.vendor_name = vendor_name

        return VendorQuotation(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            extracted_data=result
        )

    async def analyze_and_compare(
        self,
        quotations: List[Dict[str, Any]]
    ) -> ComparisonResult:
        """
        Analyze and compare 3 vendor quotations.

        Args:
            quotations: List of 3 quotation dicts, each containing:
                - vendor_id: Unique vendor ID
                - vendor_name: Company name
                - image: Image data (path, base64, or bytes)

        Returns:
            ComparisonResult with ranked vendors and recommendation
        """
        if len(quotations) != 3:
            raise ValueError("Exactly 3 quotations are required")

        # Analyze each quotation
        analyzed = []
        for q in quotations:
            vendor_quotation = await self.analyze_single(
                image=q["image"],
                vendor_id=q["vendor_id"],
                vendor_name=q["vendor_name"]
            )
            analyzed.append(vendor_quotation)

        # Compare and rank
        comparison = self._compare_quotations(analyzed)

        return comparison

    def _compare_quotations(
        self,
        quotations: List[VendorQuotation]
    ) -> ComparisonResult:
        """Compare quotations and generate recommendation."""
        # Calculate scores for ranking
        scored = []
        for q in quotations:
            data = q.extracted_data
            if data and data.total_price:
                score = self._calculate_score(data)
                scored.append((q, score))
            else:
                scored.append((q, float('inf')))  # No price = worst score

        # Sort by score (lower is better for price-based)
        scored.sort(key=lambda x: x[1])

        # Assign ranks
        for i, (q, _) in enumerate(scored, 1):
            q.rank = i

        # Build ranked vendors list
        ranked_vendors = []
        for q, score in scored:
            data = q.extracted_data
            ranked_vendors.append({
                "rank": q.rank,
                "vendor_id": q.vendor_id,
                "vendor_name": q.vendor_name,
                "total_price": data.total_price if data else None,
                "currency": data.currency if data else "USD",
                "timeline_days": data.timeline_days if data else None,
                "warranty_months": data.warranty_months if data else None,
                "score": score if score != float('inf') else None,
                "confidence": data.confidence if data else 0.0
            })

        # Generate summary
        prices = [q.extracted_data.total_price for q in quotations
                  if q.extracted_data and q.extracted_data.total_price]

        summary = self._generate_summary(quotations, prices)

        # Generate recommendation
        recommendation = self._generate_recommendation(scored)

        # Identify red flags
        red_flags = self._identify_red_flags(quotations)

        # Calculate overall confidence
        confidences = [q.extracted_data.confidence for q in quotations
                       if q.extracted_data]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return ComparisonResult(
            quotations=quotations,
            ranked_vendors=ranked_vendors,
            recommendation=recommendation,
            summary=summary,
            red_flags=red_flags,
            extraction_method=ExtractionMethod.LLM if self.use_llm else ExtractionMethod.OCR,
            overall_confidence=overall_confidence
        )

    def _calculate_score(self, data: QuotationResult) -> float:
        """
        Calculate comparison score (lower is better).

        Primary factor: Price (80%)
        Secondary factors: Timeline, Warranty (20%)
        """
        if not data.total_price:
            return float('inf')

        # Price is primary factor (80%)
        score = data.total_price * 0.8

        # Faster timeline is better (10%)
        if data.timeline_days:
            # Normalize: assume 30 days is baseline
            timeline_factor = data.timeline_days / 30.0
            score += (data.total_price * 0.1 * timeline_factor)

        # Longer warranty is better (10%) - inverse relationship
        if data.warranty_months:
            # Normalize: assume 12 months is baseline
            warranty_factor = 12.0 / max(data.warranty_months, 1)
            score += (data.total_price * 0.1 * warranty_factor)

        return score

    def _generate_summary(
        self,
        quotations: List[VendorQuotation],
        prices: List[float]
    ) -> Dict[str, Any]:
        """Generate comparison summary."""
        if not prices:
            return {
                "lowest_price_vendor": None,
                "highest_price_vendor": None,
                "price_range": None,
                "average_price": None,
                "price_difference_percent": None
            }

        # Find lowest/highest price vendors
        lowest_price = min(prices)
        highest_price = max(prices)

        lowest_vendor = None
        highest_vendor = None
        fastest_vendor = None
        best_warranty_vendor = None

        min_timeline = float('inf')
        max_warranty = 0

        for q in quotations:
            data = q.extracted_data
            if data:
                if data.total_price == lowest_price:
                    lowest_vendor = q.vendor_name
                if data.total_price == highest_price:
                    highest_vendor = q.vendor_name
                if data.timeline_days and data.timeline_days < min_timeline:
                    min_timeline = data.timeline_days
                    fastest_vendor = q.vendor_name
                if data.warranty_months and data.warranty_months > max_warranty:
                    max_warranty = data.warranty_months
                    best_warranty_vendor = q.vendor_name

        price_diff = ((highest_price - lowest_price) / lowest_price * 100) if lowest_price > 0 else 0

        return {
            "lowest_price_vendor": lowest_vendor,
            "lowest_price": lowest_price,
            "highest_price_vendor": highest_vendor,
            "highest_price": highest_price,
            "average_price": sum(prices) / len(prices),
            "price_range": highest_price - lowest_price,
            "price_difference_percent": round(price_diff, 1),
            "fastest_timeline_vendor": fastest_vendor,
            "fastest_timeline_days": min_timeline if min_timeline != float('inf') else None,
            "best_warranty_vendor": best_warranty_vendor,
            "best_warranty_months": max_warranty if max_warranty > 0 else None
        }

    def _generate_recommendation(
        self,
        scored: List[tuple]
    ) -> Dict[str, Any]:
        """Generate recommendation based on scores."""
        if not scored or scored[0][1] == float('inf'):
            return {
                "recommended_vendor_id": None,
                "recommended_vendor_name": None,
                "reason": "Unable to determine recommendation - no valid prices extracted",
                "confidence": 0.0
            }

        best = scored[0][0]  # VendorQuotation
        best_data = best.extracted_data

        # Build reason
        reasons = []
        reasons.append(f"Lowest price at ${best_data.total_price:.2f}")

        if best_data.timeline_days:
            reasons.append(f"{best_data.timeline_days} days timeline")
        if best_data.warranty_months:
            reasons.append(f"{best_data.warranty_months} months warranty")

        return {
            "recommended_vendor_id": best.vendor_id,
            "recommended_vendor_name": best.vendor_name,
            "total_price": best_data.total_price,
            "reason": " | ".join(reasons),
            "confidence": best_data.confidence
        }

    def _identify_red_flags(
        self,
        quotations: List[VendorQuotation]
    ) -> List[str]:
        """Identify potential red flags in quotations."""
        red_flags = []

        prices = []
        for q in quotations:
            data = q.extracted_data
            if data and data.total_price:
                prices.append(data.total_price)

                # Check for missing important info
                if not data.warranty_months and not data.warranty_description:
                    red_flags.append(f"{q.vendor_name}: No warranty information")

                if not data.timeline_days and not data.timeline_description:
                    red_flags.append(f"{q.vendor_name}: No timeline specified")

                # Check extraction errors
                if data.errors:
                    red_flags.append(f"{q.vendor_name}: Extraction issues - {', '.join(data.errors[:2])}")

            else:
                red_flags.append(f"{q.vendor_name}: Could not extract price")

        # Check for suspiciously low prices (more than 40% below average)
        if len(prices) >= 2:
            avg = sum(prices) / len(prices)
            for q in quotations:
                data = q.extracted_data
                if data and data.total_price:
                    if data.total_price < avg * 0.6:
                        red_flags.append(
                            f"{q.vendor_name}: Price significantly below average (${data.total_price:.2f} vs avg ${avg:.2f})"
                        )

        return red_flags

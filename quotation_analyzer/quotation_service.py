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
    ExtractionMethod,
    TimeSlot
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
        quotations: List[Dict[str, Any]],
        user_available_slots: Optional[List[Dict[str, str]]] = None
    ) -> ComparisonResult:
        """
        Analyze and compare 3 vendor quotations.

        Args:
            quotations: List of 3 quotation dicts, each containing:
                - vendor_id: Unique vendor ID
                - vendor_name: Company name
                - image: Image data (path, base64, or bytes)
                - available_slots: Optional list of 3 time slots (vendor availability)
            user_available_slots: Optional list of user's available time slots

        Returns:
            ComparisonResult with ranked vendors and recommendation
        """
        if len(quotations) != 3:
            raise ValueError("Exactly 3 quotations are required")

        # Parse user time slots
        user_slots = []
        if user_available_slots:
            for slot_data in user_available_slots:
                if slot_data.get("date") and slot_data.get("start_time") and slot_data.get("end_time"):
                    user_slots.append(TimeSlot.from_dict(slot_data))

        # Analyze each quotation
        analyzed = []
        for q in quotations:
            vendor_quotation = await self.analyze_single(
                image=q["image"],
                vendor_id=q["vendor_id"],
                vendor_name=q["vendor_name"]
            )
            
            # Parse vendor available time slots
            vendor_slots_data = q.get("available_slots", [])
            vendor_slots = []
            for slot_data in vendor_slots_data:
                if slot_data.get("date") and slot_data.get("start_time") and slot_data.get("end_time"):
                    vendor_slots.append(TimeSlot.from_dict(slot_data))
            vendor_quotation.available_slots = vendor_slots
            
            # Calculate matching slots with user
            if user_slots and vendor_slots:
                matching = self._find_matching_slots(user_slots, vendor_slots)
                vendor_quotation.matching_slots = matching
                vendor_quotation.schedule_score = len(matching) / max(len(user_slots), 1)
            
            analyzed.append(vendor_quotation)

        # Compare and rank
        comparison = self._compare_quotations(analyzed, user_slots)

        return comparison
    
    def _find_matching_slots(
        self,
        user_slots: List[TimeSlot],
        vendor_slots: List[TimeSlot]
    ) -> List[TimeSlot]:
        """Find time slots where user and vendor availability overlap."""
        matching = []
        for user_slot in user_slots:
            for vendor_slot in vendor_slots:
                if user_slot.overlaps_with(vendor_slot):
                    # Return the vendor slot that matches
                    matching.append(vendor_slot)
                    break  # Count each vendor slot only once
        return matching

    def _compare_quotations(
        self,
        quotations: List[VendorQuotation],
        user_slots: Optional[List[TimeSlot]] = None
    ) -> ComparisonResult:
        """Compare quotations and generate recommendation."""
        has_schedule_data = user_slots and any(q.available_slots for q in quotations)
        
        # Calculate scores for ranking
        scored = []
        for q in quotations:
            data = q.extracted_data
            if data and data.total_price:
                score = self._calculate_score(data, q.schedule_score, has_schedule_data)
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
                "confidence": data.confidence if data else 0.0,
                "schedule_score": q.schedule_score,
                "matching_slots_count": len(q.matching_slots),
                "available_slots": [s.to_dict() for s in q.available_slots],
                "matching_slots": [s.to_dict() for s in q.matching_slots]
            })

        # Generate summary
        prices = [q.extracted_data.total_price for q in quotations
                  if q.extracted_data and q.extracted_data.total_price]

        summary = self._generate_summary(quotations, prices)

        # Generate recommendation (now includes schedule info)
        recommendation = self._generate_recommendation(scored, has_schedule_data)

        # Identify red flags (now includes schedule issues)
        red_flags = self._identify_red_flags(quotations, user_slots)

        # Calculate overall confidence
        confidences = [q.extracted_data.confidence for q in quotations
                       if q.extracted_data]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Generate schedule summary
        schedule_summary = self._generate_schedule_summary(quotations, user_slots)

        return ComparisonResult(
            quotations=quotations,
            ranked_vendors=ranked_vendors,
            recommendation=recommendation,
            summary=summary,
            red_flags=red_flags,
            extraction_method=ExtractionMethod.LLM if self.use_llm else ExtractionMethod.OCR,
            overall_confidence=overall_confidence,
            user_available_slots=user_slots or [],
            schedule_summary=schedule_summary
        )

    def _calculate_score(
        self,
        data: QuotationResult,
        schedule_score: float = 0.0,
        has_schedule_data: bool = False
    ) -> float:
        """
        Calculate comparison score (lower is better).

        If schedule data present:
            - Price: 60%
            - Schedule Match: 20%
            - Timeline: 10%
            - Warranty: 10%
        
        Without schedule data:
            - Price: 80%
            - Timeline: 10%
            - Warranty: 10%
        """
        if not data.total_price:
            return float('inf')

        if has_schedule_data:
            # With schedule data: Price (60%), Schedule (20%), Timeline (10%), Warranty (10%)
            score = data.total_price * 0.6
            
            # Better schedule match = lower score (invert: 1 - schedule_score)
            # schedule_score ranges from 0 to 1
            schedule_penalty = (1.0 - schedule_score) * data.total_price * 0.2
            score += schedule_penalty
            
            # Faster timeline is better
            if data.timeline_days:
                timeline_factor = data.timeline_days / 30.0
                score += (data.total_price * 0.1 * timeline_factor)
            
            # Longer warranty is better
            if data.warranty_months:
                warranty_factor = 12.0 / max(data.warranty_months, 1)
                score += (data.total_price * 0.1 * warranty_factor)
        else:
            # Without schedule data: original scoring
            score = data.total_price * 0.8

            # Faster timeline is better (10%)
            if data.timeline_days:
                timeline_factor = data.timeline_days / 30.0
                score += (data.total_price * 0.1 * timeline_factor)

            # Longer warranty is better (10%)
            if data.warranty_months:
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
        scored: List[tuple],
        has_schedule_data: bool = False
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
        reasons.append(f"Best price at ${best_data.total_price:.2f}")

        if has_schedule_data and best.matching_slots:
            reasons.append(f"{len(best.matching_slots)} matching time slot(s)")
        
        if best_data.timeline_days:
            reasons.append(f"{best_data.timeline_days} days timeline")
        if best_data.warranty_months:
            reasons.append(f"{best_data.warranty_months} months warranty")

        return {
            "recommended_vendor_id": best.vendor_id,
            "recommended_vendor_name": best.vendor_name,
            "total_price": best_data.total_price,
            "reason": " | ".join(reasons),
            "confidence": best_data.confidence,
            "schedule_score": best.schedule_score,
            "matching_slots": [s.to_dict() for s in best.matching_slots]
        }

    def _identify_red_flags(
        self,
        quotations: List[VendorQuotation],
        user_slots: Optional[List[TimeSlot]] = None
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
            
            # Check schedule compatibility
            if user_slots and q.available_slots:
                if not q.matching_slots:
                    red_flags.append(f"{q.vendor_name}: No matching time slots with your availability")
                elif len(q.matching_slots) == 1:
                    red_flags.append(f"{q.vendor_name}: Only 1 matching time slot (limited flexibility)")

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

    def _generate_schedule_summary(
        self,
        quotations: List[VendorQuotation],
        user_slots: Optional[List[TimeSlot]] = None
    ) -> Dict[str, Any]:
        """Generate schedule matching summary."""
        if not user_slots:
            return {
                "schedule_considered": False,
                "message": "No user availability provided"
            }
        
        has_any_vendor_slots = any(q.available_slots for q in quotations)
        if not has_any_vendor_slots:
            return {
                "schedule_considered": False,
                "message": "No vendor availability provided"
            }
        
        # Find best schedule match
        best_schedule_vendor = None
        best_match_count = 0
        perfect_match_vendors = []
        no_match_vendors = []
        
        for q in quotations:
            match_count = len(q.matching_slots)
            if match_count > best_match_count:
                best_match_count = match_count
                best_schedule_vendor = q.vendor_name
            
            if match_count == len(user_slots):
                perfect_match_vendors.append(q.vendor_name)
            elif match_count == 0 and q.available_slots:
                no_match_vendors.append(q.vendor_name)
        
        return {
            "schedule_considered": True,
            "user_slots_count": len(user_slots),
            "best_schedule_match_vendor": best_schedule_vendor,
            "best_match_count": best_match_count,
            "perfect_match_vendors": perfect_match_vendors,
            "no_match_vendors": no_match_vendors,
            "message": f"Best schedule compatibility: {best_schedule_vendor} ({best_match_count} matching slots)"
        }

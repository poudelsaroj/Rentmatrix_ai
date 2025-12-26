"""
OCR Extractor using Tesseract
Extracts text from quotation images and parses structured data.
"""

import re
import base64
import io
from typing import Union, List, Dict, Any, Optional
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

from .base_extractor import BaseExtractor
from ..models import QuotationResult, ExtractionMethod


class OCRExtractor(BaseExtractor):
    """
    Tesseract OCR-based quotation extractor.

    Extracts text from images and uses regex patterns to parse
    structured quotation data like prices, items, dates, etc.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize the OCR extractor.

        Args:
            tesseract_cmd: Path to tesseract executable (optional).
                          On Windows: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        """
        if pytesseract is None:
            raise ImportError("pytesseract is not installed. Run: pip install pytesseract")

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def get_method_name(self) -> str:
        return "Tesseract OCR"

    async def extract(self, image: Union[str, bytes]) -> QuotationResult:
        """
        Extract quotation data from an image using Tesseract OCR.

        Args:
            image: File path, base64 string, or raw bytes

        Returns:
            QuotationResult with extracted and parsed data
        """
        try:
            # Load image
            pil_image = self._load_image(image)

            # Preprocess image for better OCR
            processed_image = self._preprocess_image(pil_image)

            # Extract text using Tesseract
            raw_text = pytesseract.image_to_string(processed_image, lang='eng')

            # Parse structured data from text
            result = self._parse_quotation_text(raw_text)
            result.raw_text = raw_text
            result.extraction_method = ExtractionMethod.OCR

            # Calculate confidence based on how much data was extracted
            result.confidence = self._calculate_confidence(result)

            return result

        except Exception as e:
            return QuotationResult(
                extraction_method=ExtractionMethod.OCR,
                confidence=0.0,
                errors=[f"OCR extraction failed: {str(e)}"]
            )

    def _load_image(self, image: Union[str, bytes]) -> Image.Image:
        """Load image from various sources."""
        if isinstance(image, bytes):
            return Image.open(io.BytesIO(image))

        if isinstance(image, str):
            # Check if base64
            if image.startswith("data:image"):
                # Extract base64 data from data URI
                base64_data = image.split(",")[1]
                image_bytes = base64.b64decode(base64_data)
                return Image.open(io.BytesIO(image_bytes))
            elif len(image) > 500 and not image.startswith("/") and not image.startswith("C:"):
                # Likely base64 without prefix
                image_bytes = base64.b64decode(image)
                return Image.open(io.BytesIO(image_bytes))
            else:
                # File path
                return Image.open(image)

        raise ValueError(f"Unsupported image type: {type(image)}")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to grayscale
        gray = image.convert('L')

        # Increase contrast (simple threshold)
        # This helps with scanned documents
        return gray

    def _parse_quotation_text(self, text: str) -> QuotationResult:
        """Parse structured data from OCR text."""
        result = QuotationResult()

        # Normalize text
        text_lower = text.lower()
        lines = text.split('\n')

        # Extract vendor name (usually at the top)
        result.vendor_name = self._extract_vendor_name(lines)

        # Extract prices
        prices = self._extract_prices(text)
        if prices:
            result.total_price = max(prices)  # Usually the largest is total
            if len(prices) > 1:
                result.subtotal = sorted(prices)[-2] if len(prices) > 1 else None

        # Extract currency
        result.currency = self._extract_currency(text)

        # Extract items/line items
        result.items = self._extract_line_items(text)

        # Extract tax
        tax_info = self._extract_tax(text)
        result.tax_amount = tax_info.get("amount")
        result.tax_rate = tax_info.get("rate")

        # Extract labor and materials
        result.labor_cost = self._extract_labeled_amount(text, ["labor", "labour", "service"])
        result.materials_cost = self._extract_labeled_amount(text, ["material", "parts", "supplies"])

        # Extract timeline
        timeline = self._extract_timeline(text)
        result.timeline_days = timeline.get("days")
        result.timeline_description = timeline.get("description")

        # Extract warranty
        warranty = self._extract_warranty(text)
        result.warranty_months = warranty.get("months")
        result.warranty_description = warranty.get("description")

        # Extract payment terms
        result.payment_terms = self._extract_payment_terms(text)

        # Extract validity
        result.validity_days = self._extract_validity(text)

        # Extract date
        result.date_issued = self._extract_date(text)

        # Extract contact info
        result.contact_info = self._extract_contact(text)

        # Extract special conditions
        result.special_conditions = self._extract_conditions(text)

        return result

    def _extract_vendor_name(self, lines: List[str]) -> Optional[str]:
        """Extract vendor/company name from first few lines."""
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 3 and not re.match(r'^[\d\$\.\,]+$', line):
                # Skip lines that are just numbers/prices
                if not any(kw in line.lower() for kw in ['date', 'invoice', 'quote', 'total', 'tax']):
                    return line
        return None

    def _extract_prices(self, text: str) -> List[float]:
        """Extract all price values from text."""
        prices = []

        # Pattern for prices: $1,234.56 or 1234.56 or $1234
        patterns = [
            r'\$\s*([\d,]+\.?\d*)',  # $1,234.56
            r'(?:total|amount|price|cost)[\s:]*\$?\s*([\d,]+\.?\d*)',  # Total: 1234.56
            r'([\d,]+\.\d{2})\s*(?:USD|usd|\$)',  # 1234.56 USD
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if price > 0:
                        prices.append(price)
                except ValueError:
                    continue

        return list(set(prices))

    def _extract_currency(self, text: str) -> str:
        """Extract currency from text."""
        if '$' in text or 'USD' in text.upper():
            return 'USD'
        if '€' in text or 'EUR' in text.upper():
            return 'EUR'
        if '£' in text or 'GBP' in text.upper():
            return 'GBP'
        return 'USD'  # Default

    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract itemized list from quotation."""
        items = []
        lines = text.split('\n')

        # Pattern: description followed by quantity and price
        item_pattern = r'(.+?)\s+(\d+)\s*[xX@]?\s*\$?([\d,]+\.?\d*)'

        for line in lines:
            match = re.search(item_pattern, line)
            if match:
                items.append({
                    "name": match.group(1).strip(),
                    "quantity": int(match.group(2)),
                    "unit_price": float(match.group(3).replace(',', '')),
                    "total": int(match.group(2)) * float(match.group(3).replace(',', ''))
                })

        return items

    def _extract_tax(self, text: str) -> Dict[str, Any]:
        """Extract tax information."""
        result = {"amount": None, "rate": None}

        # Tax amount: Tax: $123.45
        amount_match = re.search(r'tax[\s:]*\$?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
        if amount_match:
            try:
                result["amount"] = float(amount_match.group(1).replace(',', ''))
            except ValueError:
                pass

        # Tax rate: 8.5% tax
        rate_match = re.search(r'(\d+\.?\d*)\s*%\s*(?:tax|vat|gst)', text, re.IGNORECASE)
        if rate_match:
            try:
                result["rate"] = float(rate_match.group(1))
            except ValueError:
                pass

        return result

    def _extract_labeled_amount(self, text: str, labels: List[str]) -> Optional[float]:
        """Extract amount with specific label."""
        for label in labels:
            pattern = rf'{label}[\s:]*\$?\s*([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    continue
        return None

    def _extract_timeline(self, text: str) -> Dict[str, Any]:
        """Extract timeline/completion information."""
        result = {"days": None, "description": None}

        # Pattern: 3-5 days, 1 week, etc.
        patterns = [
            (r'(\d+)\s*(?:-\s*\d+)?\s*(?:business\s+)?days?', 'days'),
            (r'(\d+)\s*weeks?', 'weeks'),
            (r'completion[\s:]*(.+?)(?:\.|$)', 'description')
        ]

        for pattern, ptype in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if ptype == 'days':
                    result["days"] = int(match.group(1))
                elif ptype == 'weeks':
                    result["days"] = int(match.group(1)) * 7
                elif ptype == 'description':
                    result["description"] = match.group(1).strip()

        return result

    def _extract_warranty(self, text: str) -> Dict[str, Any]:
        """Extract warranty information."""
        result = {"months": None, "description": None}

        # Pattern: 12 month warranty, 1 year warranty
        patterns = [
            (r'(\d+)\s*(?:month|mo)s?\s*warranty', 'months'),
            (r'(\d+)\s*years?\s*warranty', 'years'),
            (r'warranty[\s:]*(.+?)(?:\.|$)', 'description')
        ]

        for pattern, ptype in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if ptype == 'months':
                    result["months"] = int(match.group(1))
                elif ptype == 'years':
                    result["months"] = int(match.group(1)) * 12
                elif ptype == 'description':
                    result["description"] = match.group(1).strip()

        return result

    def _extract_payment_terms(self, text: str) -> Optional[str]:
        """Extract payment terms."""
        patterns = [
            r'payment[\s:]*(.+?)(?:\.|$)',
            r'terms[\s:]*(.+?)(?:\.|$)',
            r'(\d+%\s*(?:upfront|deposit|down).+?)(?:\.|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_validity(self, text: str) -> Optional[int]:
        """Extract quote validity period."""
        patterns = [
            r'valid\s*(?:for)?\s*(\d+)\s*days?',
            r'expires?\s*(?:in)?\s*(\d+)\s*days?',
            r'(\d+)\s*days?\s*validity'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from quotation."""
        patterns = [
            r'date[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_contact(self, text: str) -> Optional[str]:
        """Extract contact information."""
        # Phone pattern
        phone_match = re.search(r'(?:phone|tel|call)[\s:]*([+\d\s\-()]+)', text, re.IGNORECASE)
        if phone_match:
            return phone_match.group(1).strip()

        # Email pattern
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            return email_match.group(0)

        return None

    def _extract_conditions(self, text: str) -> List[str]:
        """Extract special conditions or notes."""
        conditions = []

        keywords = ['note:', 'condition:', 'terms:', 'important:', '*', '-']
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if any(line.lower().startswith(kw) for kw in keywords):
                conditions.append(line)

        return conditions[:5]  # Limit to 5 conditions

    def _calculate_confidence(self, result: QuotationResult) -> float:
        """Calculate confidence score based on extracted data."""
        score = 0.0
        max_score = 10.0

        if result.total_price:
            score += 3.0
        if result.vendor_name:
            score += 1.5
        if result.items:
            score += 2.0
        if result.timeline_days or result.timeline_description:
            score += 1.0
        if result.warranty_months or result.warranty_description:
            score += 1.0
        if result.date_issued:
            score += 0.5
        if result.payment_terms:
            score += 0.5
        if result.contact_info:
            score += 0.5

        return min(score / max_score, 1.0)

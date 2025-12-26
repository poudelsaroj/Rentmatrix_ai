"""
Quotation Extractors
Provides OCR and LLM-based extraction methods.
"""

from .base_extractor import BaseExtractor
from .ocr_extractor import OCRExtractor
from .llm_extractor import LLMExtractor

__all__ = ["BaseExtractor", "OCRExtractor", "LLMExtractor"]

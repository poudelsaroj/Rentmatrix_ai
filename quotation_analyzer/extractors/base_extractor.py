"""
Base Extractor Class
Abstract base class for quotation extractors.
"""

from abc import ABC, abstractmethod
from typing import Union
from ..models import QuotationResult


class BaseExtractor(ABC):
    """Abstract base class for quotation extractors."""

    @abstractmethod
    async def extract(self, image: Union[str, bytes]) -> QuotationResult:
        """
        Extract quotation data from an image.

        Args:
            image: Either a file path, base64 string, or raw bytes

        Returns:
            QuotationResult with extracted data
        """
        pass

    @abstractmethod
    def get_method_name(self) -> str:
        """Return the name of the extraction method."""
        pass

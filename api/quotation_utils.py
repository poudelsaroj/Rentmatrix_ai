"""
Quotation Image Handling Utilities
Handles image validation, format conversion, and storage.
"""

import base64
import re
from typing import List, Tuple, Optional
from pathlib import Path
import uuid


def validate_image_format(image_data: str) -> Tuple[bool, Optional[str]]:
    """
    Validate image format from base64 string or data URI.
    
    Args:
        image_data: Base64 encoded image or data URI
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if it's a data URI
    if image_data.startswith("data:image"):
        # Extract the base64 part
        match = re.match(r"data:image/(\w+);base64,(.+)", image_data)
        if not match:
            return False, "Invalid data URI format"
        image_format = match.group(1).lower()
        base64_data = match.group(2)
    elif image_data.startswith("http://") or image_data.startswith("https://"):
        # URL - assume valid (will be handled by OpenAI API)
        return True, None
    else:
        # Assume base64 encoded
        base64_data = image_data
        image_format = None
    
    # Validate base64 encoding
    try:
        decoded = base64.b64decode(base64_data, validate=True)
        if len(decoded) == 0:
            return False, "Empty image data"
        
        # Check file size (max 20MB for OpenAI Vision API)
        if len(decoded) > 20 * 1024 * 1024:
            return False, "Image size exceeds 20MB limit"
        
        # Validate image format if we can determine it
        if image_format:
            valid_formats = ["png", "jpg", "jpeg", "gif", "webp"]
            if image_format not in valid_formats:
                return False, f"Unsupported image format: {image_format}"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid base64 encoding: {str(e)}"


def normalize_image_data(image_data: str) -> str:
    """
    Normalize image data to data URI format for OpenAI Vision API.
    
    Args:
        image_data: Base64 encoded image or data URI
    
    Returns:
        Normalized data URI string
    """
    # If already a data URI, return as-is
    if image_data.startswith("data:image"):
        return image_data
    
    # If it's a URL, return as-is
    if image_data.startswith("http://") or image_data.startswith("https://"):
        return image_data
    
    # Assume it's base64 encoded PNG
    return f"data:image/png;base64,{image_data}"


def validate_images(images: List[str]) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate a list of images.
    
    Args:
        images: List of image data strings
    
    Returns:
        Tuple of (all_valid, error_message, normalized_images)
    """
    if not images:
        return False, "No images provided", []
    
    if len(images) > 10:
        return False, "Maximum 10 images allowed per quotation", []
    
    normalized_images = []
    
    for i, img in enumerate(images):
        is_valid, error = validate_image_format(img)
        if not is_valid:
            return False, f"Image {i+1}: {error}", []
        
        normalized_images.append(normalize_image_data(img))
    
    return True, None, normalized_images


def generate_quotation_id() -> str:
    """Generate a unique quotation ID."""
    return f"QUO-{uuid.uuid4().hex[:8].upper()}"


def save_image_temporary(image_data: str, quotation_id: str, index: int) -> Optional[str]:
    """
    Save image to temporary storage (optional, for future use).
    
    Args:
        image_data: Base64 encoded image
        quotation_id: Quotation ID
        index: Image index
    
    Returns:
        File path if saved, None otherwise
    """
    # For MVP, we don't save images persistently
    # This can be implemented later if needed
    return None


"""
Quotation Analyzer FastAPI Application
Provides endpoints for analyzing and comparing vendor quotations.
Supports toggle between OCR (Tesseract) and LLM (gpt-5 Vision).
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from quotation_analyzer.quotation_service import QuotationService
from quotation_analyzer.models import ExtractionMethod


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    """Request to analyze a single quotation."""
    vendor_id: str = Field(..., description="Unique vendor ID")
    vendor_name: str = Field(..., description="Vendor company name")
    image: str = Field(..., description="Base64 encoded image or data URI")
    use_llm: bool = Field(False, description="Use LLM (True) or OCR (False)")


class AnalyzeResponse(BaseModel):
    """Response from single quotation analysis."""
    vendor_id: str
    vendor_name: str
    extraction_method: str
    extracted_data: dict
    confidence: float
    errors: List[str]


class CompareRequest(BaseModel):
    """Request to compare 3 vendor quotations."""
    use_llm: bool = Field(False, description="Use LLM (True) or OCR (False)")
    quotations: List[dict] = Field(
        ...,
        description="List of 3 quotations with vendor_id, vendor_name, and image",
        min_length=3,
        max_length=3
    )


class CompareResponse(BaseModel):
    """Response from quotation comparison."""
    extraction_method: str
    ranked_vendors: List[dict]
    recommendation: dict
    summary: dict
    red_flags: List[str]
    overall_confidence: float
    processed_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    ocr_available: bool
    llm_available: bool
    timestamp: str


# ==================== FastAPI Application ====================

app = FastAPI(
    title="Quotation Analyzer API",
    description=(
        "Analyze and compare vendor quotation images.\n\n"
        "**Features:**\n"
        "- Toggle between OCR (Tesseract) and LLM (gpt-5 Vision)\n"
        "- Analyze single quotation images\n"
        "- Compare 3 vendor quotations with ranking\n"
        "- Extract: price, items, timeline, warranty, payment terms, etc.\n\n"
        "**Toggle:** Set `use_llm=true` for LLM mode, `use_llm=false` for OCR mode"
    ),
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (for frontend)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize service (default to OCR)
quotation_service = QuotationService(use_llm=False)


# ==================== Endpoints ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML page."""
    html_path = static_dir / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content="<h1>Quotation Analyzer API</h1><p>Frontend not found. Use /docs for API.</p>")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and available extraction methods."""
    ocr_available = True
    llm_available = True

    # Check Tesseract
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        ocr_available = False

    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        llm_available = False

    return {
        "status": "ok",
        "ocr_available": ocr_available,
        "llm_available": llm_available,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_quotation(request: AnalyzeRequest):
    """
    Analyze a single vendor quotation image.

    **Parameters:**
    - `vendor_id`: Unique identifier for the vendor
    - `vendor_name`: Company/vendor name
    - `image`: Base64 encoded image or data URI
    - `use_llm`: Toggle - True for LLM (gpt-5), False for OCR (Tesseract)

    **Returns:**
    Extracted quotation data including price, items, timeline, warranty, etc.
    """
    try:
        # Set extraction method
        quotation_service.set_extraction_method(request.use_llm)

        # Analyze
        result = await quotation_service.analyze_single(
            image=request.image,
            vendor_id=request.vendor_id,
            vendor_name=request.vendor_name
        )

        data = result.extracted_data

        return {
            "vendor_id": result.vendor_id,
            "vendor_name": result.vendor_name,
            "extraction_method": data.extraction_method.value if data else "unknown",
            "extracted_data": data.to_dict() if data else {},
            "confidence": data.confidence if data else 0.0,
            "errors": data.errors if data else []
        }

    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.post("/compare", response_model=CompareResponse)
async def compare_quotations(request: CompareRequest):
    """
    Compare 3 vendor quotations and get recommendation.

    **Parameters:**
    - `use_llm`: Toggle - True for LLM (gpt-5), False for OCR (Tesseract)
    - `quotations`: List of exactly 3 quotations, each with:
        - `vendor_id`: Unique vendor ID
        - `vendor_name`: Company name
        - `image`: Base64 encoded image or data URI

    **Returns:**
    - Ranked vendors (1st = recommended)
    - Comparison summary (lowest price, fastest timeline, etc.)
    - Recommendation with reasoning
    - Red flags (if any)

    **Example Request:**
    ```json
    {
        "use_llm": false,
        "quotations": [
            {"vendor_id": "V1", "vendor_name": "Vendor A", "image": "data:image/png;base64,..."},
            {"vendor_id": "V2", "vendor_name": "Vendor B", "image": "data:image/png;base64,..."},
            {"vendor_id": "V3", "vendor_name": "Vendor C", "image": "data:image/png;base64,..."}
        ]
    }
    ```
    """
    try:
        # Set extraction method
        quotation_service.set_extraction_method(request.use_llm)

        # Compare
        result = await quotation_service.analyze_and_compare(request.quotations)

        return {
            "extraction_method": result.extraction_method.value,
            "ranked_vendors": result.ranked_vendors,
            "recommendation": result.recommendation,
            "summary": result.summary,
            "red_flags": result.red_flags,
            "overall_confidence": result.overall_confidence,
            "processed_at": result.processed_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Comparison failed: {str(e)}")


@app.post("/upload-and-compare")
async def upload_and_compare(
    use_llm: bool = Form(False),
    vendor1_name: str = Form(...),
    vendor2_name: str = Form(...),
    vendor3_name: str = Form(...),
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    image3: UploadFile = File(...)
):
    """
    Upload 3 quotation images and compare them.

    This endpoint accepts file uploads directly (for form-based submission).

    **Form Parameters:**
    - `use_llm`: Toggle - true for LLM, false for OCR
    - `vendor1_name`, `vendor2_name`, `vendor3_name`: Vendor names
    - `image1`, `image2`, `image3`: Quotation image files
    """
    import base64

    try:
        # Read and encode images
        quotations = []
        for i, (name, file) in enumerate([
            (vendor1_name, image1),
            (vendor2_name, image2),
            (vendor3_name, image3)
        ], 1):
            content = await file.read()
            b64 = base64.b64encode(content).decode('utf-8')

            # Determine mime type
            if file.filename.lower().endswith('.png'):
                mime = "image/png"
            elif file.filename.lower().endswith(('.jpg', '.jpeg')):
                mime = "image/jpeg"
            else:
                mime = "image/png"

            quotations.append({
                "vendor_id": f"V{i}",
                "vendor_name": name,
                "image": f"data:{mime};base64,{b64}"
            })

        # Set extraction method
        quotation_service.set_extraction_method(use_llm)

        # Compare
        result = await quotation_service.analyze_and_compare(quotations)

        return {
            "extraction_method": result.extraction_method.value,
            "ranked_vendors": result.ranked_vendors,
            "recommendation": result.recommendation,
            "summary": result.summary,
            "red_flags": result.red_flags,
            "overall_confidence": result.overall_confidence,
            "processed_at": result.processed_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Comparison failed: {str(e)}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("QUOTATION ANALYZER API")
    print("=" * 60)
    print("\nStarting server...")
    print("Frontend: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    print("\nToggle Options:")
    print("  - use_llm=false : Use Tesseract OCR (default)")
    print("  - use_llm=true  : Use gpt-5 Vision (LLM)")
    print("=" * 60 + "\n")

    uvicorn.run(
        "quotation_analyzer.app:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )

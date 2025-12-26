# Quotation Analyzer

A standalone module for analyzing and comparing 3 vendor quotation images.

## Features

- **Toggle Mode**: Switch between OCR (Tesseract) and LLM (gpt-5 Vision)
- **Image Analysis**: Extract structured data from quotation photos
- **Comparison**: Rank 3 vendors and get recommendations
- **Web UI**: Simple HTML/CSS frontend for easy use

## Extracted Data

- Vendor Name
- Total Price, Subtotal, Tax
- Line Items (name, quantity, unit price)
- Labor & Materials Cost
- Timeline (days)
- Warranty (months)
- Payment Terms
- Special Conditions
- Contact Info
- Date Issued

## Installation

```bash
# Install dependencies
pip install pytesseract pillow openai fastapi uvicorn python-multipart python-dotenv

# For OCR mode, install Tesseract:
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Mac: brew install tesseract
# Linux: apt install tesseract-ocr
```

## Usage

### Start the Server

```bash
cd quotation_analyzer
python app.py
```

Or from project root:
```bash
python -m quotation_analyzer.app
```

### Access

- **Frontend**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### Toggle Modes

| Mode | Setting | Description |
|------|---------|-------------|
| OCR | `use_llm=false` | Uses Tesseract OCR (free, offline) |
| LLM | `use_llm=true` | Uses gpt-5 Vision (better accuracy, requires API key) |

## API Endpoints

### POST /compare

Compare 3 vendor quotations.

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

### POST /analyze

Analyze single quotation.

```json
{
  "vendor_id": "V1",
  "vendor_name": "Vendor A",
  "image": "data:image/png;base64,...",
  "use_llm": false
}
```

### POST /upload-and-compare

Upload files directly via form (for file upload).

## Folder Structure

```
quotation_analyzer/
├── __init__.py
├── app.py                 # FastAPI application
├── models.py              # Data models
├── quotation_service.py   # Main service
├── extractors/
│   ├── __init__.py
│   ├── base_extractor.py  # Abstract base
│   ├── ocr_extractor.py   # Tesseract OCR
│   └── llm_extractor.py   # gpt-5 Vision
├── static/
│   └── index.html         # Web frontend
└── sample_images/         # Test images
```

## Environment Variables

Required in `.env`:
```
OPENAI_API_KEY=sk-...  # For LLM mode
```

## Comparison Logic

1. **Primary**: Price (80% weight)
2. **Secondary**: Timeline speed (10%)
3. **Secondary**: Warranty length (10%)

Lower score = better value.

## Red Flags Detection

- Missing price extraction
- No warranty specified
- No timeline specified
- Price significantly below average (>40% lower)

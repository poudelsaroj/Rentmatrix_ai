# RentMatrix AI Triage API

FastAPI backend exposing the complete 4-agent RentMatrix AI Triage System.

## Overview

The API provides a single endpoint that processes maintenance requests through all 4 specialized agents:

1. **Agent 1: Triage Classifier** - Classifies severity and trade category
2. **Agent 2: Priority Calculator** - Calculates numerical priority score (0-100)
3. **Agent 3: Explainer** - Generates PM and tenant-facing explanations
4. **Agent 4: Confidence Evaluator** ⭐ - Assesses confidence and recommends routing

## Quick Start

### 1. Start the API Server

```powershell
# Option 1: Run directly
python api/app.py

# Option 2: Use uvicorn
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 2. View API Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Test the API

```powershell
# Run the test script
python test_api.py
```

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Triage Maintenance Request

```http
POST /triage
Content-Type: application/json

{
  "description": "Strong gas smell in basement, evacuated"
}
```

**Response:**
```json
{
  "triage": {
    "severity": "EMERGENCY",
    "trade": "HVAC",
    "confidence": 1.0,
    "reasoning": "Gas leak with evacuation is life-safety emergency...",
    "key_factors": ["gas_leak", "health_symptoms", "evacuation"]
  },
  "priority": {
    "priority_score": 100,
    "base_score": 85,
    "total_modifiers": 15,
    "applied_modifiers": [...]
  },
  "explanation": {
    "pm_explanation": "EMERGENCY: Gas leak with evacuation...",
    "tenant_explanation": "Your request has been marked as an emergency..."
  },
  "confidence": {
    "confidence": 1.0,
    "routing": "AUTO_APPROVE",
    "confidence_factors": [...],
    "risk_flags": [],
    "recommendation": "Extremely high confidence. Auto-approve..."
  }
}
```

## Request Schema

### TriageRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Maintenance issue description (min 3 chars) |

**Example:**
```json
{
  "description": "Toilet overflowing, water spreading to bedroom"
}
```

## Response Schema

### TriageResponse

The response contains outputs from all 4 agents:

#### 1. Triage (Agent 1)

| Field | Type | Description |
|-------|------|-------------|
| `severity` | string | EMERGENCY, HIGH, MEDIUM, or LOW |
| `trade` | string | PLUMBING, ELECTRICAL, HVAC, APPLIANCE, GENERAL, STRUCTURAL |
| `confidence` | float | Triage confidence (0.0-1.0) |
| `reasoning` | string | Classification reasoning |
| `key_factors` | array | Key factors in decision |

#### 2. Priority (Agent 2)

| Field | Type | Description |
|-------|------|-------------|
| `priority_score` | integer | Priority score (0-100) |
| `base_score` | integer | Base score from severity |
| `total_modifiers` | integer | Sum of all modifiers |
| `applied_modifiers` | array | List of applied modifiers with reasons |

#### 3. Explanation (Agent 3)

| Field | Type | Description |
|-------|------|-------------|
| `pm_explanation` | string | Technical explanation for property manager |
| `tenant_explanation` | string | Clear explanation for tenant |

#### 4. Confidence (Agent 4) ⭐

| Field | Type | Description |
|-------|------|-------------|
| `confidence` | float | Overall confidence (0.30-1.0) |
| `routing` | string | AUTO_APPROVE, PM_REVIEW_QUEUE, or PM_IMMEDIATE_REVIEW |
| `confidence_factors` | array | Factors affecting confidence |
| `risk_flags` | array | Identified risk factors |
| `recommendation` | string | Routing recommendation explanation |

### Routing Decisions

Agent 4 provides routing recommendations based on confidence:

| Confidence | Routing | Percentage | Description |
|-----------|---------|------------|-------------|
| ≥ 0.90 | `AUTO_APPROVE` | 85% | High confidence - Auto-approve |
| 0.70-0.89 | `PM_REVIEW_QUEUE` | 12% | Moderate - Queue for review |
| < 0.70 | `PM_IMMEDIATE_REVIEW` | 3% | Low - Immediate attention |

## Example Usage

### Python (using requests)

```python
import requests

# Make request
response = requests.post(
    "http://localhost:8000/triage",
    json={
        "description": "Gas smell in basement, evacuated"
    }
)

result = response.json()

# Access Agent 4 output
confidence = result["confidence"]
print(f"Confidence: {confidence['confidence']}")
print(f"Routing: {confidence['routing']}")
```

### cURL

```bash
curl -X POST "http://localhost:8000/triage" \
  -H "Content-Type: application/json" \
  -d '{"description": "Toilet overflowing, water everywhere"}'
```

### JavaScript (fetch)

```javascript
fetch('http://localhost:8000/triage', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    description: 'Outlet sparking and making noise'
  })
})
.then(res => res.json())
.then(data => {
  console.log('Confidence:', data.confidence.confidence);
  console.log('Routing:', data.confidence.routing);
});
```

## Testing

### Run Comprehensive Tests

```powershell
python test_api.py
```

This will test:
1. Health endpoint
2. EMERGENCY case (Gas leak)
3. HIGH case (Water damage)
4. MEDIUM case (Ambiguous electrical)
5. LOW case (Cosmetic issue)

### Manual Testing via Swagger UI

1. Open http://localhost:8000/docs
2. Click on `/triage` endpoint
3. Click "Try it out"
4. Enter a description
5. Click "Execute"
6. View the complete 4-agent response

## Configuration

The API uses default configuration from `agent/config.py`:

```python
# Current configuration
triage_model = "gpt-5-mini"
priority_model = "gpt-5-mini"
explainer_model = "gpt-5-mini"
confidence_model = "gpt-5-mini"  # Agent 4
```

To modify, edit `api/app.py`:

```python
pipeline = TriagePipeline(
    triage_model="gpt-5-mini",
    priority_model="gpt-5-mini",
    confidence_model="gpt-5-mini",
    verbose=False
)
```

## Environment Variables

Required environment variables (in `.env` file):

```env
# OpenAI API Key
OPENAI_API_KEY=your_key_here

# Langfuse (optional - for tracing)
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Performance

### Expected Latency
- **Total Pipeline**: 3-5 seconds
  - Agent 1 (Triage): ~1.5s
  - Agent 2 (Priority): ~0.8s
  - Agent 3 (Explainer): ~0.6s
  - Agent 4 (Confidence): ~0.8s

### Cost per Request
- **Agent 1**: $0.015
- **Agent 2**: $0.003
- **Agent 3**: $0.007
- **Agent 4**: $0.008
- **Total**: ~$0.033 per request

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 422 | Validation Error (invalid input) |
| 500 | Internal Server Error (pipeline failure) |

### Error Response

```json
{
  "detail": "Pipeline execution failed"
}
```

## Production Deployment

### Recommended Setup

1. **Use production ASGI server**:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app:app
   ```

2. **Enable CORS** (if needed):
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Add authentication** (recommended for production)

4. **Set up monitoring** (Langfuse traces are already enabled)

## What's New in v1.0

### Agent 4: Confidence Evaluator ⭐

The API now includes Agent 4, which:
- Evaluates classification quality
- Provides confidence scores (0.30-1.0)
- Recommends routing decisions
- Identifies risk factors
- Reduces PM workload by 85%

### Updated Response Format

All responses now include the `confidence` field with Agent 4's assessment.

## Support

For issues or questions:
1. Check API documentation: http://localhost:8000/docs
2. Review test script: `test_api.py`
3. See complete docs: `AGENT4_IMPLEMENTATION.md`

## License

Copyright © 2024 RentMatrix AI

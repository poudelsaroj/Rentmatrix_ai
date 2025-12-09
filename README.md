 # RentMatrix AI - Maintenance Triage System

An intelligent property maintenance classification system that analyzes maintenance requests and provides precise severity classification, priority scoring, and trade assignment using OpenAI agents.

## Features

- **Intelligent Severity Classification**: Automatically categorizes requests as EMERGENCY, HIGH, MEDIUM, or LOW priority
- **Trade Assignment**: Assigns appropriate trade (Plumbing, Electrical, HVAC, Appliance, General, Structural)
- **Chain-of-Thought Reasoning**: Provides detailed analysis with confidence scores
- **Production Monitoring**: Integrated with Langfuse for tracing and observability

## Prerequisites

- Python 3.12+
- OpenAI API Key
- Langfuse Account (optional but recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/poudelsaroj/Rentmatrix_ai.git
   cd Rentmatrix_ai
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r Requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

## Usage

### Run the FastAPI Server (Swagger UI)

```bash
cd api
python app.py
```

Open **http://localhost:8000/docs** in your browser for Swagger UI.

### Run the demo

```bash
python agent/demo.py
```

### Input Format

Provide maintenance requests in JSON format:

```json
{
    "description": "Kitchen faucet is dripping again. This is the THIRD time I've reported this in 2 months."
}
```

### Example Output

```json
{
    "severity": "MEDIUM",
    "trade": "PLUMBING",
    "reasoning": "Recurring drip requires 24-48hr response. Active leak causing cabinet damage. No immediate safety risk but needs timely resolution.",
    "confidence": 0.92,
    "key_factors": [
        "Recurring issue (3rd report)",
        "Contained slow drip",
        "Cabinet water damage developing"
    ]
}
```


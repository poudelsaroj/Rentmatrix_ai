# RentMatrix AI - Backend Integration Guide

## API Overview

**Base URL:** `http://localhost:8000`
**Version:** 2.0.0

---

## Flow

```
1. POST /triage          -> AI analyzes issue, returns severity + trade + SLA
2. PM reviews result
3. POST /assign-vendors  -> Round-robin assigns 3 vendors (1 primary + 2 backups)
```

---

## Endpoints

### 1. POST `/triage` - AI Triage (Agents 1-5)

**Request:**
```json
{
  "description": "Water leaking from ceiling in bathroom",
  "location": {
    "query": "Boston, MA"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Issue description (min 3 chars) |
| `location.query` | string | No | City/address for weather |
| `location.latitude` | float | No | Lat coordinate |
| `location.longitude` | float | No | Lon coordinate |

**Response:**
```json
{
  "triage": {
    "severity": "HIGH",
    "trade": "PLUMBING",
    "reasoning": "Active water leak..."
  },
  "priority": {
    "priority_score": 78,
    "applied_modifiers": ["Active water damage"]
  },
  "explanation": {
    "pm_explanation": "High priority plumbing issue...",
    "tenant_explanation": "We've classified this as urgent..."
  },
  "confidence": {
    "confidence_score": 0.89,
    "routing_decision": "AUTO_APPROVE"
  },
  "sla": {
    "sla_tier": "HIGH",
    "response_deadline": "2024-12-23T12:00:00Z",
    "resolution_deadline": "2024-12-24T17:00:00Z"
  },
  "weather": { ... }
}
```

**Key fields for next step:**
- `triage.trade` -> Use this for vendor assignment

---

### 2. POST `/assign-vendors` - Vendor Assignment (No LLM)

**Request:**
```json
{
  "trade": "PLUMBING",
  "tenant_preferred_times": [
    "Monday 09:00-12:00",
    "Wednesday 14:00-17:00",
    "Friday 10:00-15:00"
  ],
  "vendors": [
    {
      "vendor_id": "V001",
      "company_name": "QuickFix Plumbing",
      "primary_trade": "PLUMBING",
      "phone": "555-0101",
      "availability": ["Monday 08:00-17:00", "Wednesday 08:00-17:00", "Friday 08:00-17:00"]
    },
    {
      "vendor_id": "V002",
      "company_name": "FastPipe Services",
      "primary_trade": "PLUMBING",
      "phone": "555-0102",
      "availability": ["Tuesday 09:00-18:00", "Thursday 09:00-18:00"]
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trade` | string | Yes | Trade from triage response |
| `tenant_preferred_times` | string[] | Yes | Tenant's 3 preferred time slots |
| `vendors` | array | Yes | Vendor list with availability |

**Vendor object:**
```json
{
  "vendor_id": "V001",
  "company_name": "QuickFix",
  "primary_trade": "PLUMBING",
  "availability": ["Monday 08:00-17:00", "Wednesday 08:00-17:00"]
}
```

**Time slot formats supported:**
- `"Monday 09:00-12:00"` - Day + time range
- `"Mon 09:00-12:00"` - Abbreviated day
- `"2024-12-23 14:00-17:00"` - Specific date

**Response:**
```json
{
  "success": true,
  "trade": "PLUMBING",
  "total_available": 2,
  "tenant_preferred_times": ["Monday 09:00-12:00", "Wednesday 14:00-17:00", "Friday 10:00-15:00"],
  "assigned_vendors": [
    {
      "vendor": { "vendor_id": "V001", "company_name": "QuickFix", ... },
      "role": "primary",
      "matched_times": ["Monday 09:00-12:00", "Wednesday 14:00-17:00", "Friday 10:00-15:00"]
    },
    {
      "vendor": { "vendor_id": "V002", "company_name": "FastPipe", ... },
      "role": "backup",
      "matched_times": []
    }
  ]
}
```

**Matching Logic:**
1. Filters vendors by matching trade
2. Scores vendors by how many tenant times they can match
3. Prioritizes vendors with more matching times
4. Round-robin within same match count
5. Returns 3 vendors (1 primary + 2 backups)

---

### 3. GET `/weather`

**Query:** `?location=Boston` or `?lat=42.36&lon=-71.05`

---

### 4. GET `/health`

Returns `{"status": "ok"}`

---

## Trade Categories

| Code | Description |
|------|-------------|
| `PLUMBING` | Pipes, drains, water heaters |
| `ELECTRICAL` | Wiring, outlets, panels |
| `HVAC` | Heating, AC, ventilation |
| `APPLIANCE` | Refrigerators, washers, stoves |
| `LOCKSMITH` | Locks, keys, security |
| `GENERAL` | Handyman, minor repairs |
| `CARPENTRY` | Wood, doors, cabinets |
| `ROOFING` | Roof repairs |
| `PEST_CONTROL` | Insects, rodents |

---

## Severity & SLA

| Severity | Priority Score | Response Time |
|----------|---------------|---------------|
| `EMERGENCY` | 80-100 | 4 hours |
| `HIGH` | 60-79 | 24 hours |
| `MEDIUM` | 25-59 | 48 hours |
| `LOW` | 0-24 | 72 hours |

---

## Database: Vendors Tables

**vendors table:**
```sql
CREATE TABLE vendors (
  vendor_id     VARCHAR(20) PRIMARY KEY,
  company_name  VARCHAR(100) NOT NULL,
  primary_trade VARCHAR(20) NOT NULL,  -- PLUMBING, ELECTRICAL, etc.
  phone         VARCHAR(20),
  email         VARCHAR(100),
  is_active     BOOLEAN DEFAULT TRUE
);
```

**vendor_availability table:**
```sql
CREATE TABLE vendor_availability (
  vendor_id   VARCHAR(20) REFERENCES vendors,
  day_of_week VARCHAR(10),  -- Monday, Tuesday, etc.
  start_time  TIME,         -- 09:00
  end_time    TIME,         -- 17:00
  PRIMARY KEY (vendor_id, day_of_week, start_time)
);
```

**Format availability for API:**
```python
# Convert DB rows to API format
vendor["availability"] = [
    f"{row.day_of_week} {row.start_time}-{row.end_time}"
    for row in vendor_availability_rows
]
# Result: ["Monday 09:00-17:00", "Wednesday 09:00-17:00"]
```

---

## Integration Example

```python
import requests

# Step 1: Triage
triage_resp = requests.post("http://localhost:8000/triage", json={
    "description": "No hot water in apartment"
})
triage = triage_resp.json()
trade = triage["triage"]["trade"]  # e.g., "PLUMBING"

# Step 2: Get vendors from your database
vendors = get_vendors_from_db(trade)  # Your function

# Step 3: Assign vendors
assign_resp = requests.post("http://localhost:8000/assign-vendors", json={
    "trade": trade,
    "vendors": vendors
})
assigned = assign_resp.json()

primary = assigned["assigned_vendors"][0]["vendor"]
backups = [v["vendor"] for v in assigned["assigned_vendors"][1:]]
```

---

## Quick Test

```bash
# Start API
python api/app.py

# Test triage
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"description": "Toilet overflowing"}'

# Test vendor assignment with time matching
curl -X POST http://localhost:8000/assign-vendors \
  -H "Content-Type: application/json" \
  -d '{
    "trade": "PLUMBING",
    "tenant_preferred_times": ["Monday 09:00-12:00", "Wednesday 14:00-17:00"],
    "vendors": [
      {
        "vendor_id": "V1",
        "company_name": "PlumberA",
        "primary_trade": "PLUMBING",
        "availability": ["Monday 08:00-17:00", "Wednesday 08:00-17:00"]
      },
      {
        "vendor_id": "V2",
        "company_name": "PlumberB",
        "primary_trade": "PLUMBING",
        "availability": ["Tuesday 09:00-17:00"]
      }
    ]
  }'
```

---

## Environment

```env
OPENAI_API_KEY=sk-...   # Required for AI agents
```

Weather uses Open-Meteo (free, no API key needed).

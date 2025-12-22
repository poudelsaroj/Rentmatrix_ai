# RentMatrix AI - Backend Integration Guide

## API Overview

**Base URL:** `http://localhost:8000`
**Version:** 1.1.0

---

## Endpoints

### 1. POST `/triage` - Main Triage Endpoint

Runs the 7-agent AI pipeline for maintenance request analysis.

**Request:**
```json
{
  "description": "Water leaking from ceiling in bathroom",
  "location": {
    "query": "Boston, MA",
    "latitude": null,
    "longitude": null
  },
  "tenant_preferred_times": [
    "Monday 09:00-12:00",
    "Wednesday 14:00-17:00",
    "Friday 10:00-15:00"
  ],
  "include_vendor_matching": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Maintenance issue description (min 3 chars) |
| `location.query` | string | No | City name, address, or zipcode |
| `location.latitude` | float | No | Latitude (-90 to 90) |
| `location.longitude` | float | No | Longitude (-180 to 180) |
| `tenant_preferred_times` | string[] | No | 3 preferred time slots for vendor visit |
| `include_vendor_matching` | bool | No | Enable vendor matching (default: false) |

**Response:**
```json
{
  "triage": {
    "severity": "HIGH",
    "trade": "PLUMBING",
    "reasoning": "Active water leak from ceiling indicates...",
    "triage_confidence": 0.92
  },
  "priority": {
    "priority_score": 78,
    "applied_modifiers": ["Active water damage", "Potential structural risk"]
  },
  "explanation": {
    "pm_explanation": "High priority plumbing issue requiring immediate attention...",
    "tenant_explanation": "We've classified this as urgent. A plumber will contact you within 24 hours..."
  },
  "confidence": {
    "confidence_score": 0.89,
    "routing_decision": "AUTO_APPROVE",
    "risk_flags": []
  },
  "sla": {
    "sla_tier": "HIGH",
    "response_deadline": "2024-12-23T12:00:00Z",
    "resolution_deadline": "2024-12-24T17:00:00Z",
    "vendor_tier": "PREMIUM"
  },
  "weather": {
    "temperature": 28.5,
    "condition": "Clear sky",
    "forecast": "High 32F, Low 25F. Clear",
    "alerts": []
  },
  "vendors": {
    "matched_vendors": [...],
    "recommendation_summary": "..."
  },
  "vendor_explanation": {
    "comparison": [...],
    "final_recommendation": "..."
  }
}
```

---

### 2. GET `/weather` - Weather Data

**Query Params:** `location=Boston` OR `lat=42.36&lon=-71.05`

---

### 3. GET `/health` - Health Check

Returns `{"status": "ok"}`

---

## Database Requirements

### Tables Needed from Backend

#### 1. `vendors` Table (Currently Mock Data)

```sql
CREATE TABLE vendors (
  vendor_id        VARCHAR(20) PRIMARY KEY,  -- "VND-PL-001"
  company_name     VARCHAR(100) NOT NULL,
  contact_name     VARCHAR(100),
  phone            VARCHAR(20),
  email            VARCHAR(100),
  tier             ENUM('EMERGENCY','PREMIUM','STANDARD','BUDGET'),
  is_active        BOOLEAN DEFAULT TRUE,
  is_verified      BOOLEAN DEFAULT TRUE,
  insurance_verified BOOLEAN DEFAULT TRUE,
  license_number   VARCHAR(50),
  preferred_vendor BOOLEAN DEFAULT FALSE
);
```

#### 2. `vendor_locations` Table

```sql
CREATE TABLE vendor_locations (
  vendor_id            VARCHAR(20) REFERENCES vendors,
  address              VARCHAR(200),
  city                 VARCHAR(100),
  state                VARCHAR(10),
  zip_code             VARCHAR(10),
  latitude             DECIMAL(10,7),
  longitude            DECIMAL(10,7),
  service_radius_miles INT DEFAULT 20
);
```

#### 3. `vendor_expertise` Table

```sql
CREATE TABLE vendor_expertise (
  vendor_id         VARCHAR(20) REFERENCES vendors,
  primary_trade     ENUM('PLUMBING','ELECTRICAL','HVAC','APPLIANCE','CARPENTRY',
                         'PAINTING','FLOORING','ROOFING','LOCKSMITH','GENERAL',...),
  secondary_trades  JSON,           -- ["GENERAL", "CARPENTRY"]
  specializations   JSON,           -- ["Emergency Repairs", "Gas Lines"]
  certifications    JSON,           -- ["Master Plumber", "EPA Certified"]
  years_experience  INT,
  handles_emergency BOOLEAN DEFAULT FALSE
);
```

#### 4. `vendor_ratings` Table

```sql
CREATE TABLE vendor_ratings (
  vendor_id                 VARCHAR(20) REFERENCES vendors,
  overall_rating            DECIMAL(2,1),  -- 4.8
  total_jobs                INT,
  completed_jobs            INT,
  response_time_avg_minutes INT,
  quality_score             DECIMAL(2,1),
  reliability_score         DECIMAL(2,1),
  communication_score       DECIMAL(2,1)
);
```

#### 5. `vendor_pricing` Table

```sql
CREATE TABLE vendor_pricing (
  vendor_id             VARCHAR(20) REFERENCES vendors,
  hourly_rate           DECIMAL(10,2),  -- 125.00
  emergency_multiplier  DECIMAL(3,2) DEFAULT 1.50,
  weekend_multiplier    DECIMAL(3,2) DEFAULT 1.25,
  after_hours_multiplier DECIMAL(3,2) DEFAULT 1.30,
  trip_fee              DECIMAL(10,2) DEFAULT 0.00
);
```

#### 6. `vendor_availability` Table

```sql
CREATE TABLE vendor_availability (
  vendor_id    VARCHAR(20) REFERENCES vendors,
  day_of_week  VARCHAR(10),  -- "Monday"
  start_time   TIME,         -- "09:00"
  end_time     TIME,         -- "17:00"
  is_emergency BOOLEAN DEFAULT FALSE
);
```

---

## API for Vendor Data

The AI system expects vendor data in this format:

```json
{
  "vendor_id": "VND-PL-001",
  "company_name": "QuickFix Plumbing 24/7",
  "contact_name": "Mike Johnson",
  "phone": "555-0101",
  "email": "mike@quickfixplumbing.com",
  "tier": "EMERGENCY",
  "location": {
    "city": "Boston",
    "state": "MA",
    "zip_code": "02101",
    "service_radius_miles": 25
  },
  "expertise": {
    "primary_trade": "PLUMBING",
    "secondary_trades": ["GENERAL"],
    "specializations": ["Emergency Repairs", "Gas Lines", "Water Heaters"],
    "certifications": ["Master Plumber", "Gas Fitting License"],
    "years_experience": 15,
    "handles_emergency": true
  },
  "rating": {
    "overall_rating": 4.8,
    "total_jobs": 342,
    "completion_rate": 98.8,
    "response_time_avg_minutes": 25,
    "quality_score": 4.9,
    "reliability_score": 4.7,
    "communication_score": 4.8
  },
  "pricing": {
    "hourly_rate": 125.0,
    "emergency_multiplier": 1.5,
    "trip_fee": 50.0
  },
  "availability": [
    "Monday 00:00-23:59 (Emergency Available)",
    "Tuesday 00:00-23:59 (Emergency Available)"
  ],
  "preferred_vendor": true
}
```

---

## Integration Points

### Option A: Replace Mock Data

Create an API endpoint in your backend:

```
GET /api/vendors?trade=PLUMBING&city=Boston
```

Modify `agent/data/mock_vendors.py` to fetch from your API instead.

### Option B: Pass Vendors to API

Extend the `/triage` request to accept vendors:

```json
{
  "description": "...",
  "vendors": [...],
  "include_vendor_matching": true
}
```

---

## Trade Categories

| Code | Description |
|------|-------------|
| `PLUMBING` | Pipes, drains, water heaters, leaks |
| `ELECTRICAL` | Wiring, outlets, panels, circuits |
| `HVAC` | Heating, AC, ventilation, thermostats |
| `APPLIANCE` | Refrigerators, washers, stoves, dishwashers |
| `LOCKSMITH` | Locks, keys, security |
| `GENERAL` | Handyman, minor repairs |
| `CARPENTRY` | Wood, doors, cabinets |
| `PAINTING` | Interior/exterior painting |
| `ROOFING` | Roof repairs, leaks |
| `PEST_CONTROL` | Insects, rodents |

---

## Severity Levels

| Level | Priority Score | Response Time |
|-------|---------------|---------------|
| `EMERGENCY` | 80-100 | 4 hours |
| `HIGH` | 60-79 | 24 hours |
| `MEDIUM` | 25-59 | 48 hours |
| `LOW` | 0-24 | 72 hours |

---

## Quick Start

```bash
# Start the API
python api/app.py

# Test triage
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"description": "No hot water in apartment"}'
```

---

## Environment Variables

```env
OPENAI_API_KEY=sk-...      # Required for AI agents
```

Weather uses Open-Meteo (free, no key required).

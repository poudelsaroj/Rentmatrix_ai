# Triage System - Input/Output Specification

## API Endpoint

```
POST /triage
Content-Type: application/json
```

---

## Input Format

```json
{
  "request": {
    "request_id": "REQ-2024-001",
    "description": "Strong gas smell in basement, evacuated",
    "images": [],
    "reported_at": "2024-12-23T14:30:00Z",
    "channel": "MOBILE"
  },
  "location": {
    "query": "Boston, MA",
    "latitude": 42.36,
    "longitude": -71.05
  },
  "tenant": {
    "age": 35,
    "is_elderly": false,
    "has_infant": true,
    "has_medical_condition": false,
    "is_pregnant": false,
    "occupant_count": 4,
    "tenure_months": 18
  },
  "property": {
    "type": "Apartment",
    "age": 22,
    "floor": 2,
    "total_units": 12,
    "has_elevator": true
  },
  "timing": {
    "day_of_week": "Monday",
    "hour": 14,
    "is_after_hours": false,
    "is_weekend": false,
    "is_holiday": false,
    "is_late_night": false
  },
  "history": {
    "recent_issues_count": 0,
    "last_repair_date": null,
    "recurring_category": null,
    "previous_repair_failed": false,
    "avg_resolution_time_hours": null
  },
  "similar_cases": []
}
```

### Input Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **request** | | | |
| `request.request_id` | string | Yes | Unique request identifier |
| `request.description` | string | Yes | Maintenance request description (min 3 chars) |
| `request.images` | array | No | List of image URLs |
| `request.reported_at` | string | Yes | ISO 8601 timestamp |
| `request.channel` | string | Yes | `API`, `MOBILE`, `WEB` |
| **location** | | | |
| `location.query` | string | No | City/address for weather lookup |
| `location.latitude` | float | No | Latitude (-90 to 90) |
| `location.longitude` | float | No | Longitude (-180 to 180) |
| **tenant** | | | |
| `tenant.age` | int | No | Tenant age |
| `tenant.is_elderly` | bool | No | Age >= 65 |
| `tenant.has_infant` | bool | No | Has child under 2 years |
| `tenant.has_medical_condition` | bool | No | Has medical condition |
| `tenant.is_pregnant` | bool | No | Pregnant occupant |
| `tenant.occupant_count` | int | No | Number of occupants |
| `tenant.tenure_months` | int | No | Months as tenant |
| **property** | | | |
| `property.type` | string | No | `Apartment`, `Single Family Home`, `Condo`, `Townhouse` |
| `property.age` | int | No | Building age in years |
| `property.floor` | int | No | Floor number |
| `property.total_units` | int | No | Total units in building |
| `property.has_elevator` | bool | No | Building has elevator |
| **timing** | | | |
| `timing.day_of_week` | string | No | Day name |
| `timing.hour` | int | No | Hour (0-23) |
| `timing.is_after_hours` | bool | No | Outside 8am-6pm |
| `timing.is_weekend` | bool | No | Saturday or Sunday |
| `timing.is_holiday` | bool | No | Is a holiday |
| `timing.is_late_night` | bool | No | Between 10pm-6am |
| **history** | | | |
| `history.recent_issues_count` | int | No | Issues in last 90 days |
| `history.last_repair_date` | string | No | ISO date of last repair |
| `history.recurring_category` | string | No | If same issue repeated |
| `history.previous_repair_failed` | bool | No | Last repair failed |
| `history.avg_resolution_time_hours` | float | No | Average resolution time |
| **similar_cases** | array | No | Historical similar cases |

> **Note:** Weather data is fetched automatically via API using the `location` field. All other context data is provided by the backend.

---

## Output Format

```json
{
  "triage": {
    "severity": "EMERGENCY",
    "trade": "PLUMBING",
    "reasoning": "Gas leak with evacuation indicates immediate life-safety risk requiring emergency response.",
    "confidence": 0.95,
    "key_factors": [
      "gas_smell_detected",
      "evacuation_required",
      "basement_location"
    ]
  },

  "priority": {
    "priority_score": 98.3,
    "severity": "EMERGENCY",
    "base_hazard": 5.667,
    "combined_hazard": 57.379,
    "applied_factors": [
      {
        "factor": "Gas leak",
        "hr": 4.0,
        "reason": "Immediate life-safety risk"
      }
    ],
    "applied_interactions": [
      {
        "interaction": "Late Night x Emergency",
        "ir": 1.25,
        "trigger": "EMERGENCY severity + late night submission"
      }
    ],
    "calculation_trace": "h0=5.667 x HR(gas)=4.0 x IR(timing)=1.25 = 57.379",
    "confidence": 0.95
  },

  "explanation": {
    "pm_explanation": "EMERGENCY: Gas leak with evacuation requires immediate dispatch of certified gas technician.",
    "tenant_explanation": "Your request has been marked as an emergency. A technician will contact you within 4 hours."
  },

  "confidence": {
    "confidence": 0.95,
    "routing": "AUTO_APPROVE",
    "confidence_factors": [
      {
        "factor": "clear_safety_indicators",
        "impact": "POSITIVE",
        "points": 0.15,
        "reason": "Gas leak with evacuation is unambiguous"
      }
    ],
    "risk_flags": [],
    "recommendation": "Auto-approve: High confidence emergency classification"
  },

  "sla": {
    "tier": "EMERGENCY",
    "response_deadline": "2024-12-23T16:00:00Z",
    "resolution_deadline": "2024-12-24T12:00:00Z",
    "response_hours": 4,
    "resolution_hours": 24,
    "business_hours_only": false,
    "vendor_tier": "Premium only"
  },

  "weather": {
    "temperature": 28,
    "temperature_c": -2,
    "feelslike_f": 20,
    "feelslike_c": -7,
    "condition": "clear",
    "humidity": 50,
    "wind_mph": 10,
    "forecast": "Clear overnight",
    "alerts": ["Winter Weather Advisory"],
    "is_extreme_cold": false,
    "is_extreme_heat": false,
    "freeze_risk": true
  }
}
```

---

## Field Descriptions

### Triage Object

| Field | Type | Values |
|-------|------|--------|
| `severity` | string | `LOW`, `MEDIUM`, `HIGH`, `EMERGENCY` |
| `trade` | string | `PLUMBING`, `ELECTRICAL`, `HVAC`, `APPLIANCE`, `CARPENTRY`, `PAINTING`, `FLOORING`, `ROOFING`, `MASONRY`, `PEST_CONTROL`, `LOCKSMITH`, `LANDSCAPING`, `WINDOWS_GLASS`, `DOORS`, `DRYWALL`, `STRUCTURAL`, `GENERAL` |
| `reasoning` | string | 2-4 sentence explanation |
| `confidence` | float | 0.0 - 1.0 |
| `key_factors` | array | List of factors influencing classification |

### Priority Object

| Field | Type | Description |
|-------|------|-------------|
| `priority_score` | float | 0-100 score |
| `base_hazard` | float | Initial hazard value |
| `combined_hazard` | float | After applying all factors |
| `applied_factors` | array | Hazard ratios applied |
| `applied_interactions` | array | Interaction ratios applied |

### Confidence Object

| Field | Type | Values |
|-------|------|--------|
| `confidence` | float | 0.0 - 1.0 |
| `routing` | string | `AUTO_APPROVE` (>=0.90), `PM_REVIEW_QUEUE` (0.70-0.89), `PM_IMMEDIATE_REVIEW` (<0.70) |
| `risk_flags` | array | Any flags requiring attention |

### SLA Object

| Field | Type | Description |
|-------|------|-------------|
| `tier` | string | `EMERGENCY`, `HIGH`, `MEDIUM`, `LOW` |
| `response_hours` | int | Hours to first response |
| `resolution_hours` | int | Hours to resolution |
| `business_hours_only` | bool | If SLA counts only business hours |

---

## SLA Tiers

| Tier | Response | Resolution | 24/7 |
|------|----------|------------|------|
| EMERGENCY | 4 hours | 24 hours | Yes |
| HIGH | 24 hours | 48 hours | No |
| MEDIUM | 48 hours | 120 hours | No |
| LOW | 72 hours | 168 hours | No |

---

## Error Response

```json
{
  "detail": "Error message here"
}
```

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 422 | Validation error |
| 500 | Server error |

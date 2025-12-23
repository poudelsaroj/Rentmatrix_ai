# Vendor Matching API Integration Guide

## Overview

The vendor matching system is now fully integrated into the RentMatrix AI Triage API and frontend UI. Users can optionally enable vendor matching to get intelligent vendor recommendations based on tenant time preferences, trade expertise, ratings, location, and cost.

---

## API Integration

### Endpoint: `POST /triage`

The existing triage endpoint now supports vendor matching with two new optional parameters.

### Request Body

```json
{
  "description": "Kitchen sink faucet is dripping...",
  "location": {
    "query": "Boston, MA"
  },
  "tenant_preferred_times": [
    "Monday 09:00-12:00",
    "Wednesday 14:00-17:00",
    "Friday 10:00-15:00"
  ],
  "include_vendor_matching": true
}
```

### New Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_preferred_times` | `array[string]` | No | 3 preferred time slots for vendor visit |
| `include_vendor_matching` | `boolean` | No | Enable vendor matching (default: `false`) |

**Time Slot Format:**
- `"Day HH:MM-HH:MM"` (e.g., `"Monday 09:00-12:00"`)
- Can be any day of the week
- 24-hour time format
- Or special values like `"ASAP"`, `"Any time today"`, `"Within 1 hour"` for emergencies

### Response

When `include_vendor_matching=true` and tenant times are provided, the response includes a new `vendors` field:

```json
{
  "triage": { ... },
  "priority": { ... },
  "explanation": { ... },
  "confidence": { ... },
  "sla": { ... },
  "weather": { ... },
  "vendors": {
    "matched_vendors": [
      {
        "rank": 1,
        "vendor_id": "VND-PL-001",
        "company_name": "QuickFix Plumbing 24/7",
        "contact": {
          "name": "Mike Johnson",
          "phone": "555-0101",
          "email": "mike@quickfixplumbing.com"
        },
        "match_score": 92,
        "score_breakdown": {
          "expertise": 30,
          "availability": 25,
          "ratings": 24,
          "location": 15,
          "cost": 4,
          "special_factors": 10
        },
        "availability_match": "Excellent",
        "matching_time_slots": [
          "Monday 09:00-12:00",
          "Wednesday 14:00-17:00",
          "Friday 10:00-15:00"
        ],
        "estimated_cost": {
          "hourly_rate": 125.0,
          "estimated_hours": 2.0,
          "trip_fee": 50.0,
          "multipliers": "None",
          "estimated_total_min": 300.0,
          "estimated_total_max": 400.0
        },
        "strengths": [
          "24/7 emergency availability",
          "Matches all tenant time preferences",
          "Excellent ratings (4.8/5.0)"
        ],
        "considerations": [
          "Higher cost due to emergency tier"
        ],
        "recommendation_reason": "Best overall match with excellent ratings..."
      }
    ],
    "summary": {
      "total_vendors_evaluated": 10,
      "vendors_recommended": 3,
      "best_value_vendor_id": "VND-PL-002",
      "fastest_response_vendor_id": "VND-PL-001",
      "highest_rated_vendor_id": "VND-PL-001"
    },
    "recommendations": {
      "primary_choice": "VND-PL-001",
      "primary_reason": "Best overall match...",
      "backup_choice": "VND-PL-002",
      "backup_reason": "High quality and better value..."
    },
    "confidence": 0.96
  }
}
```

---

## Frontend UI Integration

### Location

Open `frontend/index.html` in your browser to access the UI.

### New UI Features

#### 1. **Vendor Matching Checkbox**

Below the description field, you'll find:
- ☐ **Include Vendor Matching (Agent 6)**

Check this box to enable vendor matching.

#### 2. **Tenant Time Slots Input**

When enabled, three input fields appear:
- **Slot 1:** e.g., `Monday 09:00-12:00`
- **Slot 2:** e.g., `Wednesday 14:00-17:00`
- **Slot 3:** e.g., `Friday 10:00-15:00`

Default values are auto-populated when you enable the checkbox.

#### 3. **Vendor Recommendations Card**

After running triage with vendor matching enabled, a new card appears showing:

**Top Section:**
- Confidence score
- Number of vendors evaluated
- Primary recommendation highlight

**For Each Vendor:**
- 🥇 Rank and company name
- Match score (0-100)
- Contact information
- Availability match rating (Excellent/Good/Fair/Poor)
- Estimated cost range
- Matching time slots (highlighted)
- Score breakdown (6 categories)
- ✓ Strengths (green)
- ! Considerations (orange)
- Recommendation reason (blue box)

### Screenshot Flow

```
┌────────────────────────────────────────────────┐
│  Maintenance description                       │
│  [Text area with description]                  │
├────────────────────────────────────────────────┤
│  ☑ Include Vendor Matching (Agent 6)          │
│                                                │
│  Tenant Preferred Time Slots (3 slots)        │
│  Format: "Day HH:MM-HH:MM"                     │
│  [Monday 09:00-12:00        ]                  │
│  [Wednesday 14:00-17:00     ]                  │
│  [Friday 10:00-15:00        ]                  │
└────────────────────────────────────────────────┘
     ↓
[Run triage]
     ↓
┌────────────────────────────────────────────────┐
│  Vendor Recommendations 🔧  Confidence: 96%    │
│  Evaluated 10 vendors, recommending top 3      │
│                                                │
│  ⭐ Primary: QuickFix Plumbing 24/7            │
│     Best overall match with all times available│
│                                                │
│  🥇 #1 QuickFix Plumbing 24/7      92         │
│     Mike Johnson | 555-0101         Match     │
│                                     Score      │
│  Availability: Excellent                       │
│  Cost: $300.00 - $400.00                       │
│                                                │
│  Matching Slots: [Mon 9-12] [Wed 14-17]...    │
│  Score: Expertise 30/30 | Availability 25/25...│
│                                                │
│  ✓ Strengths:                                  │
│  • 24/7 emergency availability                 │
│  • Matches all tenant time preferences         │
│  • Excellent ratings (4.8/5.0)                 │
│                                                │
│  ! Considerations:                             │
│  • Higher cost due to emergency tier           │
│                                                │
│  [Recommendation reason box]                   │
└────────────────────────────────────────────────┘
```

---

## Testing

### 1. Start the API Server

```bash
python api/app.py
```

Server starts at: `http://localhost:8000`

### 2. Test via Swagger UI

Navigate to: `http://localhost:8000/docs`

**Steps:**
1. Find `POST /triage` endpoint
2. Click "Try it out"
3. Enter request body:
```json
{
  "description": "Kitchen faucet dripping. Small puddle under sink.",
  "location": {
    "query": "Boston, MA"
  },
  "tenant_preferred_times": [
    "Monday 09:00-12:00",
    "Wednesday 14:00-17:00",
    "Friday 10:00-15:00"
  ],
  "include_vendor_matching": true
}
```
4. Click "Execute"
5. View response with vendor recommendations

### 3. Test via Frontend UI

1. Open `frontend/index.html` in browser
2. Enter maintenance description
3. Add location (optional)
4. ☑ Check "Include Vendor Matching"
5. Review/edit tenant time slots
6. Click "Run triage"
7. Scroll down to see "Vendor Recommendations" card

### 4. Test via Python Script

```bash
python test_api_vendor_integration.py
```

This runs automated tests for:
- Triage with vendor matching enabled
- Triage without vendor matching (baseline)

---

## Example Use Cases

### Use Case 1: Routine Maintenance

**Input:**
```json
{
  "description": "Faucet dripping, not urgent",
  "tenant_preferred_times": [
    "Monday 09:00-12:00",
    "Wednesday 14:00-17:00",
    "Friday 10:00-15:00"
  ],
  "include_vendor_matching": true
}
```

**Result:**
- Severity: MEDIUM
- Priority: ~35/100
- Vendors: 3 recommendations
  - Mix of Budget and Standard tier
  - Prioritizes scheduling match
  - Shows cost comparisons

### Use Case 2: Emergency

**Input:**
```json
{
  "description": "Gas smell in basement, evacuated!",
  "tenant_preferred_times": [
    "ASAP",
    "Within 1 hour",
    "Any time tonight"
  ],
  "include_vendor_matching": true
}
```

**Result:**
- Severity: EMERGENCY
- Priority: ~98/100
- Vendors: Emergency-only vendors
  - 24/7 availability confirmed
  - Gas line specialists prioritized
  - Cost secondary to speed

### Use Case 3: Without Location

**Input:**
```json
{
  "description": "AC not cooling well",
  "tenant_preferred_times": [
    "Tuesday 10:00-13:00",
    "Thursday 15:00-18:00",
    "Saturday 09:00-12:00"
  ],
  "include_vendor_matching": true
}
```

**Result:**
- Uses default location (Boston, MA)
- Severity: MEDIUM
- HVAC vendors recommended
- Saturday availability highlighted

---

## Configuration

### Mock Vendor Database

Currently using mock vendors from `agent/data/mock_vendors.py`:
- 10 realistic vendors
- Across 6 trade categories
- Various tiers (Emergency, Premium, Standard, Budget)

**To customize vendors:**
1. Edit `agent/data/mock_vendors.py`
2. Add/modify vendor entries
3. Restart API server

**To use real database:**
1. Create vendor table in database
2. Update `agent/core_agents/vendor_matching_agent.py`
3. Replace `MOCK_VENDORS` with database query

### Vendor Matching Model

**LLM Model:** `gpt-5-mini` (configurable)

**To change model:**
```python
# In api/app.py
vendor_agent = VendorMatchingAgent(
    model="gpt-5-mini",  # Change to "gpt-4" for better quality
    vendors=MOCK_VENDORS
)
```

---

## Troubleshooting

### Issue: Vendor matching not working

**Check:**
1. ✓ `include_vendor_matching=true` in request
2. ✓ `tenant_preferred_times` array provided (at least 1 slot)
3. ✓ API server running with latest code
4. ✓ No errors in server logs

### Issue: No vendors returned

**Possible causes:**
- No vendors match the trade category
- Location outside all vendor service areas
- Emergency request but no emergency vendors available

**Solution:**
- Check `vendors.error` field in response
- Review mock vendor data
- Verify trade classification is correct

### Issue: Frontend not showing vendor card

**Check:**
1. ✓ Vendor matching checkbox is checked
2. ✓ At least one time slot is filled
3. ✓ API returned `vendors` object
4. ✓ Browser console for JavaScript errors
5. ✓ Open dev tools → Network tab → Check API response

---

## API Response Time

**Expected latency:**
- Triage only: 3-8 seconds
- Triage + Vendor matching: 8-15 seconds

**Factors affecting speed:**
- LLM model (gpt-5-mini is faster than gpt-4)
- Number of eligible vendors
- Weather API call (if location provided)
- Network latency

---

## Future Enhancements

### Planned Features
- [ ] Real-time vendor availability API
- [ ] Automated vendor communication
- [ ] Multi-language support
- [ ] Vendor rating updates based on completed jobs
- [ ] Smart scheduling optimization
- [ ] Cost negotiation features
- [ ] Vendor workload balancing

### Database Schema (Coming Soon)

```sql
CREATE TABLE vendors (
  vendor_id VARCHAR PRIMARY KEY,
  company_name VARCHAR NOT NULL,
  contact_name VARCHAR,
  phone VARCHAR,
  email VARCHAR,
  tier VARCHAR,
  location_lat FLOAT,
  location_lon FLOAT,
  service_radius_miles INT,
  primary_trade VARCHAR,
  handles_emergency BOOLEAN,
  ...
);

CREATE TABLE vendor_availability (
  vendor_id VARCHAR REFERENCES vendors,
  day_of_week VARCHAR,
  start_time TIME,
  end_time TIME,
  is_emergency BOOLEAN
);
```

---

## Support

For issues or questions:
1. Check server logs: Look for errors in terminal running `python api/app.py`
2. Test with Swagger UI: `http://localhost:8000/docs`
3. Review documentation: `VENDOR_MATCHING_README.md`
4. Run test script: `python test_api_vendor_integration.py`

---

## Summary

The vendor matching system is now fully integrated:

✅ **API:** New parameters `tenant_preferred_times` and `include_vendor_matching`  
✅ **Frontend:** Checkbox, time slot inputs, and vendor display card  
✅ **Agent 6:** LLM-based intelligent matching with 100-point scoring  
✅ **Testing:** Automated test script and manual testing via UI/Swagger  
✅ **Documentation:** Complete guides and examples  

**Ready to use!** 🎉








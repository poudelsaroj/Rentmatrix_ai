## # RentMatrix AI - Vendor Matching Algorithm

## Overview

The **Vendor Matching Algorithm** is an intelligent LLM-based system that automatically matches the best vendors to maintenance requests based on multiple factors including expertise, location, availability, ratings, and cost.

## Key Features

### 🎯 **Multi-Factor Intelligent Matching**
- **Trade Expertise** (0-30 points): Matches vendor specializations to job requirements
- **Availability & Scheduling** (0-25 points): Aligns vendor availability with tenant time preferences
- **Ratings & Track Record** (0-25 points): Considers performance history and reliability
- **Location & Service Area** (0-15 points): Evaluates distance and coverage
- **Cost Considerations** (0-10 points): Balances value with quality
- **Special Factors** (0-10 points): Preferred vendors, certifications, emergency capability

### 📅 **Tenant Time Preference Matching**
- Tenants provide **3 preferred time slots**
- System matches vendor availability against preferences
- Provides availability rating: Excellent, Good, Fair, or Poor
- Shows specific matching time slots

### 🚨 **Emergency Prioritization**
- Emergency requests automatically matched to 24/7 vendors
- Prioritizes response time over cost
- Filters out non-emergency vendors for EMERGENCY severity

### 💰 **Cost Transparency**
- Provides estimated cost ranges for each vendor
- Considers hourly rates, trip fees, and multipliers
- Shows best value option
- Highlights trade-offs between cost and quality

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              VENDOR MATCHING WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Triage Output (Severity, Trade, Key Factors)            │
│              ↓                                               │
│  2. Priority Score (0-100 with context)                      │
│              ↓                                               │
│  3. Tenant Time Preferences (3 slots)                        │
│              ↓                                               │
│  4. Property Location                                        │
│              ↓                                               │
│  5. LLM Vendor Matching Agent                                │
│              ↓                                               │
│  6. Ranked Vendor Recommendations (3-5 vendors)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### Vendor Profile

```python
@dataclass
class Vendor:
    vendor_id: str
    company_name: str
    contact_name: str
    tier: VendorTier  # EMERGENCY, PREMIUM, STANDARD, BUDGET
    
    location: VendorLocation
    expertise: VendorExpertise
    rating: VendorRating
    pricing: VendorPricing
    availability: List[TimeSlot]
    
    is_active: bool
    preferred_vendor: bool
    license_number: str
```

### Key Components

**VendorExpertise:**
- Primary trade (PLUMBING, ELECTRICAL, HVAC, etc.)
- Secondary trades
- Specializations (e.g., "Gas Lines", "Emergency Repairs")
- Certifications
- Years of experience
- Emergency capability

**VendorRating:**
- Overall rating (1.0-5.0)
- Total jobs & completion rate
- Response time average
- Quality, reliability, communication scores

**VendorPricing:**
- Hourly rate
- Emergency multiplier (typically 1.5x)
- Weekend multiplier (typically 1.25x)
- After-hours multiplier (typically 1.3x)
- Trip fee

**TimeSlot:**
- Day of week
- Start time / End time
- Emergency available flag

## Scoring Algorithm

### Total Match Score Calculation

```
Total Score = Expertise (30) + Availability (25) + Ratings (25) + 
              Location (15) + Cost (10) + Special Factors (10)

Max Score: 100 points
```

### Scoring Breakdown

#### 1. Expertise Match (0-30 points)
- **Primary trade match**: 30 points
- **Secondary trade match**: 20 points
- **General contractor**: 15 points
- **Specialization bonus**: +5 points
- **Certification bonus**: +5 points
- **Emergency capability bonus** (for emergency requests): +10 points

#### 2. Availability & Scheduling (0-25 points)
- **3/3 tenant time slots match**: 25 points
- **2/3 slots match**: 20 points
- **1/3 slot match**: 15 points
- **Flexible availability**: 10 points
- **Response time bonus** (<30 min): +5 points
- **24/7 emergency available**: +10 points

#### 3. Ratings & Track Record (0-25 points)
- **Overall rating**:
  - 4.8-5.0: 15 points
  - 4.5-4.7: 12 points
  - 4.0-4.4: 8 points
- **Completion rate**:
  - 98-100%: 5 points
  - 95-97%: 4 points
- **Experience**:
  - 300+ jobs: 5 points
  - 200-299 jobs: 4 points

#### 4. Location & Service Area (0-15 points)
- **Same city, within radius**: 15 points
- **Adjacent city**: 12 points
- **Edge of radius**: 8 points
- **Trip fee bonus** (<$30): +2 points

#### 5. Cost Considerations (0-10 points)
- **Budget tier**: 10 points
- **Standard tier**: 8 points
- **Premium tier**: 6 points
- **Emergency tier**: 4 points

#### 6. Special Factors (0-10 points)
- **Preferred vendor**: +5 points
- **Insurance & licensing verified**: +3 points
- **Tier match to severity**: +2 points

## Usage Examples

### Example 1: Routine Plumbing Repair

```python
from agent.core_agents import VendorMatchingAgent
from agent.data import MOCK_VENDORS

# Initialize agent
agent = VendorMatchingAgent(model="gpt-5-mini", vendors=MOCK_VENDORS)

# Build prompt
prompt = agent.build_prompt(
    triage_output={
        "severity": "MEDIUM",
        "trade": "PLUMBING",
        "key_factors": ["Slow leak", "Contained", "Not urgent"]
    },
    priority_output={
        "priority_score": 35.2
    },
    request_data=request,
    tenant_preferred_times=[
        "Monday 09:00-12:00",
        "Wednesday 14:00-17:00",
        "Friday 10:00-15:00"
    ],
    property_location={
        "city": "Boston",
        "state": "MA",
        "zip_code": "02115"
    }
)

# Run matching
result = await agent.run(prompt)
```

**Expected Output:**
- 3-5 ranked plumbers
- Best value option highlighted
- Availability matches shown
- Cost estimates provided
- Clear reasoning for each recommendation

### Example 2: Emergency Gas Leak

```python
prompt = agent.build_prompt(
    triage_output={
        "severity": "EMERGENCY",
        "trade": "PLUMBING",
        "key_factors": ["Gas smell", "Evacuated", "Immediate danger"]
    },
    priority_output={
        "priority_score": 98.3
    },
    request_data=request,
    tenant_preferred_times=[
        "ASAP - Emergency",
        "Within 1 hour",
        "Any time tonight"
    ],
    property_location={"city": "Boston", "state": "MA", "zip_code": "02101"}
)

result = await agent.run(prompt)
```

**Expected Output:**
- Only 24/7 emergency vendors recommended
- Response time prioritized
- Cost secondary to speed and safety
- Gas line specialists ranked higher
- Immediate availability confirmed

## Output Format

```json
{
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
        "multipliers": "Emergency (1.5x)",
        "estimated_total_min": 425.00,
        "estimated_total_max": 500.00
      },
      "strengths": [
        "24/7 emergency availability",
        "Gas line specialist with certifications",
        "Excellent response time (25 min avg)"
      ],
      "considerations": [
        "Higher cost due to emergency tier",
        "Trip fee applies"
      ],
      "recommendation_reason": "Best choice for emergency gas leak. Has gas fitting license, 24/7 availability, and fastest response time. Cost is higher but justified for immediate life-safety response."
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
    "primary_reason": "Emergency capability and gas specialization",
    "backup_choice": "VND-PL-002",
    "backup_reason": "High quality and better value if timing flexible"
  },
  "confidence": 0.96
}
```

## Mock Vendor Database

The system includes 10 realistic mock vendors across different trades:

### Plumbing
- **QuickFix Plumbing 24/7** (Emergency, 4.8★, $125/hr)
- **Reliable Plumbing Services** (Premium, 4.6★, $95/hr)
- **Budget Plumbing Co** (Budget, 4.2★, $75/hr)

### Electrical
- **Elite Electric 24/7** (Emergency, 4.9★, $145/hr)
- **Bright Spark Electrical** (Standard, 4.5★, $110/hr)

### HVAC
- **CoolBreeze HVAC Emergency** (Emergency, 4.7★, $135/hr)
- **ComfortZone HVAC** (Premium, 4.6★, $115/hr)

### Others
- **ApplianceFix Pro** (Appliance, Premium, 4.7★)
- **Jack of All Trades Handyman** (General, Standard, 4.4★)
- **24/7 Secure Locksmith** (Locksmith, Emergency, 4.8★)

## Testing

Run the test suite to see the vendor matching in action:

```bash
python test_vendor_matching.py
```

This will demonstrate:
1. Emergency gas leak → 24/7 emergency vendors
2. Routine faucet repair → cost-effective options with scheduling
3. Electrical outlet → balanced recommendations

## Complete Demo

Run the full workflow demo:

```bash
python demo_vendor_matching_complete.py
```

This demonstrates the complete flow:
1. Triage classification
2. Priority scoring
3. Vendor matching
4. Final recommendations

## Integration with Pipeline

The vendor matching agent can be added to the existing triage pipeline as an optional step:

```python
from agent.pipeline.triage_pipeline import TriagePipeline
from agent.core_agents import VendorMatchingAgent

# Run triage pipeline
pipeline = TriagePipeline()
result = await pipeline.run(request_prompt, request_data)

# Add vendor matching
vendor_agent = VendorMatchingAgent()
vendor_result = await vendor_agent.run(
    vendor_agent.build_prompt(
        triage_output=result.triage_parsed,
        priority_output=result.priority_parsed,
        request_data=request_data,
        tenant_preferred_times=["Monday 9-12", "Wed 14-17", "Fri 10-15"],
        property_location={"city": "Boston", "state": "MA", "zip_code": "02101"}
    )
)
```

## Future Enhancements

### Planned Features
- [ ] Real-time vendor availability API integration
- [ ] Historical performance tracking
- [ ] Vendor blacklisting/favoriting
- [ ] Multi-property routing optimization
- [ ] Automated vendor communication
- [ ] Dynamic pricing negotiation
- [ ] Vendor workload balancing
- [ ] Seasonal availability patterns
- [ ] Customer satisfaction feedback loop
- [ ] Smart scheduling optimization

### Database Integration
When ready to move from mock data to production:
1. Create `vendors` table in database
2. Replace `MOCK_VENDORS` with database queries
3. Add vendor management API endpoints
4. Implement vendor profile updates
5. Track historical job assignments

## API Endpoints (Future)

```
POST /api/vendor-match
Request:
{
  "request_id": "req-001",
  "triage_result": {...},
  "priority_result": {...},
  "tenant_preferred_times": [...],
  "property_location": {...}
}

Response:
{
  "matched_vendors": [...],
  "recommendations": {...},
  "confidence": 0.95
}
```

## License

Part of RentMatrix AI Maintenance Triage System







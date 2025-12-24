"""
Agent 2: Priority Calculator Agent (Deterministic)
Calculates numerical priority score using hazard-based multiplicative model.
No LLM required - pure mathematical calculation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class PriorityFactor:
    """A factor that affects priority score."""
    name: str
    hazard_ratio: float
    reason: str
    category: str  # LIFE_SAFETY, ACTIVE_DAMAGE, VULNERABILITY, etc.


@dataclass
class InteractionEffect:
    """An interaction effect between multiple factors."""
    name: str
    interaction_ratio: float
    trigger: str


@dataclass
class PriorityResult:
    """Result from priority calculation."""
    priority_score: float
    severity: str
    base_hazard: float
    combined_hazard: float
    applied_factors: List[PriorityFactor]
    applied_interactions: List[InteractionEffect]
    calculation_trace: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "priority_score": round(self.priority_score, 1),
            "severity": self.severity,
            "base_hazard": round(self.base_hazard, 3),
            "combined_hazard": round(self.combined_hazard, 3),
            "applied_factors": [
                {
                    "factor": f.name,
                    "hr": f.hazard_ratio,
                    "reason": f.reason
                }
                for f in self.applied_factors
            ],
            "applied_interactions": [
                {
                    "interaction": i.name,
                    "ir": i.interaction_ratio,
                    "trigger": i.trigger
                }
                for i in self.applied_interactions
            ],
            "calculation_trace": self.calculation_trace,
            "confidence": round(self.confidence, 2)
        }


class PriorityCalculatorAgent:
    """
    Deterministic Priority Calculator Agent
    
    Calculates priority score (0-100) using:
    - Base hazard from severity
    - Hazard ratios (HR) for applicable factors
    - Interaction ratios (IR) for compound effects
    
    Formula: Priority Score = (100 × h) / (h + 1)
    Where: h = base_hazard × ∏(HR) × ∏(IR)
    """
    
    # Base hazard values for each severity level
    BASE_HAZARDS = {
        "LOW": 0.111,
        "MEDIUM": 0.429,
        "HIGH": 1.500,
        "EMERGENCY": 5.667
    }
    
    # Keyword patterns for detecting factors from description
    KEYWORD_PATTERNS = {
        "gas_leak": [r'\bgas\b', r'gas\s*leak', r'gas\s*smell', r'natural\s*gas'],
        "fire_smoke": [r'\bfire\b', r'\bflames?\b', r'\bsmoke\b', r'\bburning\b'],
        "carbon_monoxide": [r'\bco\s*alarm\b', r'carbon\s*monoxide', r'\bco\s*detector\b'],
        "electrical_shock": [r'\bshock(ed)?\b', r'electrocuted', r'\bsparking\b', r'\barcing\b', r'exposed\s*wires?'],
        "sewage": [r'\bsewage\b', r'raw\s*sewage', r'sewage\s*backup'],
        "water_spreading": [r'\bspreading\b', r'water\s*everywhere', r'\bflooding\b', r'flood(ed)?'],
        "ceiling_drip": [r'ceiling\s*drip', r'dripping\s*from\s*ceiling', r'water.*through\s*ceiling'],
        "getting_worse": [r'getting\s*worse', r"can'?t\s*stop", r'out\s*of\s*control', r'won\'?t\s*stop'],
        "evacuated": [r'\bevacuated?\b', r'left\s*the\s*(house|home|building|unit)', r'staying\s*(elsewhere|somewhere)'],
        "no_heat": [r'no\s*heat', r'heat(er|ing)?\s*(not|isn\'?t|won\'?t)\s*work', r'furnace\s*(broken|not|dead)'],
        "no_ac": [r'no\s*(ac|air\s*condition)', r'ac\s*(not|isn\'?t|won\'?t)\s*work', r'no\s*cool'],
        "no_water": [r'no\s*(running\s*)?water', r'water\s*(shut|turned)\s*off'],
        "no_power": [r'no\s*(power|electricity)', r'power\s*(out|off|gone)', r'lost\s*power'],
        "no_toilet": [r'toilet\s*(won\'?t|not|can\'?t)\s*flush', r'no\s*working\s*toilet'],
        "locked_out": [r'locked?\s*out', r"can'?t\s*get\s*in", r'door\s*(broken|won\'?t)'],
        "structural": [r'\bfoundation\b', r'\bstructural\b', r'load[\s-]*bearing', r'ceiling\s*sag'],
        "third_time": [r'third\s*time', r'3rd\s*time', r'keeps\s*happening', r'happened\s*(again|before)'],
        "repair_failed": [r'still\s*not\s*fixed', r"didn'?t\s*work", r'repair.*failed', r'came\s*back'],
    }
    
    def __init__(self):
        """Initialize the Priority Calculator."""
        pass
    
    def calculate_priority(
        self,
        triage_output: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> PriorityResult:
        """
        Calculate priority score from triage output and request data.
        
        Args:
            triage_output: Parsed JSON from Triage Agent (severity, trade, key_factors)
            request_data: Original request JSON with context
            
        Returns:
            PriorityResult with score and calculation details
        """
        # Extract core info
        severity = triage_output.get("severity", "MEDIUM").upper()
        trade = triage_output.get("trade", "GENERAL").upper()
        key_factors = triage_output.get("key_factors", [])
        
        # Get description
        description = ""
        if "request" in request_data:
            description = request_data["request"].get("description", "").lower()
        
        # Get context
        context = request_data.get("context", {})
        weather = context.get("weather", {})
        tenant = context.get("tenant", {})
        property_info = context.get("property", {})
        timing = context.get("timing", {})
        history = context.get("history", {})
        
        # Initialize tracking
        applied_factors: List[PriorityFactor] = []
        applied_interactions: List[InteractionEffect] = []
        trace_steps: List[str] = []
        
        # Step 1: Get base hazard
        base_hazard = self.BASE_HAZARDS.get(severity, 0.429)
        h = base_hazard
        trace_steps.append(f"Base hazard ({severity}): h = {base_hazard:.3f}")
        
        # Step 2: Apply Life Safety factors
        h, factors = self._apply_life_safety_factors(h, description, key_factors, trace_steps)
        applied_factors.extend(factors)
        
        # Step 3: Apply Active Damage factors
        h, factors = self._apply_active_damage_factors(h, description, key_factors, trace_steps)
        applied_factors.extend(factors)
        
        # Step 4: Apply Vulnerability factors
        h, factors = self._apply_vulnerability_factors(h, tenant, description, trace_steps)
        applied_factors.extend(factors)
        
        # Step 5: Apply Environmental factors
        h, factors = self._apply_environmental_factors(h, weather, trade, description, trace_steps)
        applied_factors.extend(factors)
        
        # Step 6: Apply Timing factors
        h, factors = self._apply_timing_factors(h, timing, trace_steps)
        applied_factors.extend(factors)
        
        # Step 7: Apply Recurrence factors
        h, factors = self._apply_recurrence_factors(h, history, description, trace_steps)
        applied_factors.extend(factors)
        
        # Step 8: Apply Property Risk factors
        h, factors = self._apply_property_factors(h, property_info, trade, description, trace_steps)
        applied_factors.extend(factors)
        
        # Step 9: Apply Essential Service factors
        h, factors = self._apply_essential_service_factors(h, description, trace_steps)
        applied_factors.extend(factors)
        
        # Step 10: Apply Interaction effects
        h, interactions = self._apply_interactions(
            h, severity, applied_factors, tenant, weather, trade, 
            property_info, timing, description, trace_steps
        )
        applied_interactions.extend(interactions)
        
        # Step 11: Calculate final score
        combined_hazard = h
        priority_score = (100 * h) / (h + 1)
        trace_steps.append(f"Final: Score = (100 × {h:.3f}) / ({h:.3f} + 1) = {priority_score:.1f}")
        
        # Calculate confidence based on factor clarity
        confidence = self._calculate_confidence(applied_factors, severity, description)
        
        return PriorityResult(
            priority_score=priority_score,
            severity=severity,
            base_hazard=base_hazard,
            combined_hazard=combined_hazard,
            applied_factors=applied_factors,
            applied_interactions=applied_interactions,
            calculation_trace=" → ".join(trace_steps),
            confidence=confidence
        )
    
    def _check_keywords(self, text: str, pattern_key: str) -> bool:
        """Check if any keyword pattern matches the text."""
        patterns = self.KEYWORD_PATTERNS.get(pattern_key, [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _check_key_factors(self, key_factors: List[str], keywords: List[str]) -> bool:
        """Check if any keyword appears in key_factors from triage."""
        key_factors_lower = [kf.lower() for kf in key_factors]
        for keyword in keywords:
            for kf in key_factors_lower:
                if keyword.lower() in kf:
                    return True
        return False
    
    def _apply_life_safety_factors(
        self, h: float, description: str, key_factors: List[str], trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply life safety hazard ratios."""
        factors = []
        
        # Gas leak (HR: 4.0)
        if self._check_keywords(description, "gas_leak") or \
           self._check_key_factors(key_factors, ["gas"]):
            h *= 4.0
            factors.append(PriorityFactor(
                name="Gas leak/smell",
                hazard_ratio=4.0,
                reason="Gas mentioned - immediate life safety risk",
                category="LIFE_SAFETY"
            ))
            trace.append(f"× Gas (4.0) = {h:.3f}")
        
        # Fire/smoke (HR: 4.0)
        if self._check_keywords(description, "fire_smoke") or \
           self._check_key_factors(key_factors, ["fire", "smoke", "flames"]):
            h *= 4.0
            factors.append(PriorityFactor(
                name="Fire/flames/smoke",
                hazard_ratio=4.0,
                reason="Fire hazard - immediate danger",
                category="LIFE_SAFETY"
            ))
            trace.append(f"× Fire (4.0) = {h:.3f}")
        
        # Carbon monoxide (HR: 4.0)
        if self._check_keywords(description, "carbon_monoxide") or \
           self._check_key_factors(key_factors, ["carbon monoxide", "co alarm"]):
            h *= 4.0
            factors.append(PriorityFactor(
                name="Carbon monoxide alarm",
                hazard_ratio=4.0,
                reason="CO detected - life threatening",
                category="LIFE_SAFETY"
            ))
            trace.append(f"× CO (4.0) = {h:.3f}")
        
        # Electrical shock hazard (HR: 3.0)
        if self._check_keywords(description, "electrical_shock") or \
           self._check_key_factors(key_factors, ["spark", "shock", "arcing", "exposed wire"]):
            h *= 3.0
            factors.append(PriorityFactor(
                name="Electrical shock hazard",
                hazard_ratio=3.0,
                reason="Active electrical danger present",
                category="LIFE_SAFETY"
            ))
            trace.append(f"× Electrical (3.0) = {h:.3f}")
        
        # Sewage (HR: 2.5)
        if self._check_keywords(description, "sewage") or \
           self._check_key_factors(key_factors, ["sewage"]):
            h *= 2.5
            factors.append(PriorityFactor(
                name="Sewage in living area",
                hazard_ratio=2.5,
                reason="Health hazard from sewage exposure",
                category="LIFE_SAFETY"
            ))
            trace.append(f"× Sewage (2.5) = {h:.3f}")
        
        return h, factors
    
    def _apply_active_damage_factors(
        self, h: float, description: str, key_factors: List[str], trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply active damage hazard ratios."""
        factors = []
        
        # Water spreading (HR: 2.2)
        if self._check_keywords(description, "water_spreading") or \
           self._check_key_factors(key_factors, ["spreading", "flooding", "water everywhere"]):
            h *= 2.2
            factors.append(PriorityFactor(
                name="Water actively spreading",
                hazard_ratio=2.2,
                reason="Active water damage occurring",
                category="ACTIVE_DAMAGE"
            ))
            trace.append(f"× Water spreading (2.2) = {h:.3f}")
        
        # Ceiling dripping (HR: 1.8)
        if self._check_keywords(description, "ceiling_drip") or \
           self._check_key_factors(key_factors, ["ceiling", "dripping"]):
            h *= 1.8
            factors.append(PriorityFactor(
                name="Ceiling dripping",
                hazard_ratio=1.8,
                reason="Water penetrating from above",
                category="ACTIVE_DAMAGE"
            ))
            trace.append(f"× Ceiling drip (1.8) = {h:.3f}")
        
        # Getting worse (HR: 1.6)
        if self._check_keywords(description, "getting_worse") or \
           self._check_key_factors(key_factors, ["worse", "spreading", "can't stop"]):
            h *= 1.6
            factors.append(PriorityFactor(
                name="Situation escalating",
                hazard_ratio=1.6,
                reason="Problem actively getting worse",
                category="ACTIVE_DAMAGE"
            ))
            trace.append(f"× Getting worse (1.6) = {h:.3f}")
        
        # Evacuated (HR: 2.0)
        if self._check_keywords(description, "evacuated") or \
           self._check_key_factors(key_factors, ["evacuated", "evacuation"]):
            h *= 2.0
            factors.append(PriorityFactor(
                name="Tenant evacuated",
                hazard_ratio=2.0,
                reason="Tenant forced to leave unit",
                category="ACTIVE_DAMAGE"
            ))
            trace.append(f"× Evacuated (2.0) = {h:.3f}")
        
        return h, factors
    
    def _apply_vulnerability_factors(
        self, h: float, tenant: Dict[str, Any], description: str, trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply tenant vulnerability hazard ratios."""
        factors = []
        
        # Medical condition (HR: 1.8)
        if tenant.get("has_medical_condition", False):
            h *= 1.8
            factors.append(PriorityFactor(
                name="Medical condition",
                hazard_ratio=1.8,
                reason="Tenant has medical condition requiring consideration",
                category="VULNERABILITY"
            ))
            trace.append(f"× Medical (1.8) = {h:.3f}")
        
        # Infant (HR: 1.6)
        if tenant.get("has_infant", False):
            h *= 1.6
            factors.append(PriorityFactor(
                name="Infant present",
                hazard_ratio=1.6,
                reason="Infant in household requires priority",
                category="VULNERABILITY"
            ))
            trace.append(f"× Infant (1.6) = {h:.3f}")
        
        # Elderly (HR: 1.5)
        is_elderly = tenant.get("is_elderly", False)
        age = tenant.get("age", 0)
        if is_elderly or age >= 75:
            h *= 1.5
            factors.append(PriorityFactor(
                name="Elderly tenant",
                hazard_ratio=1.5,
                reason="Elderly occupant (75+) requires consideration",
                category="VULNERABILITY"
            ))
            trace.append(f"× Elderly (1.5) = {h:.3f}")
        
        # Pregnant (HR: 1.4)
        if tenant.get("is_pregnant", False):
            h *= 1.4
            factors.append(PriorityFactor(
                name="Pregnant occupant",
                hazard_ratio=1.4,
                reason="Pregnant occupant requires consideration",
                category="VULNERABILITY"
            ))
            trace.append(f"× Pregnant (1.4) = {h:.3f}")
        
        return h, factors
    
    def _apply_environmental_factors(
        self, h: float, weather: Dict[str, Any], trade: str, description: str, trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply environmental stress hazard ratios."""
        factors = []
        temp = weather.get("temperature", 70)
        
        is_heating_issue = trade in ["HVAC"] or self._check_keywords(description, "no_heat")
        is_cooling_issue = trade in ["HVAC"] or self._check_keywords(description, "no_ac")
        is_water_issue = trade in ["PLUMBING"]
        
        # Extreme cold + no heat (HR: 2.2)
        if temp < 40 and is_heating_issue:
            h *= 2.2
            factors.append(PriorityFactor(
                name="No heat + extreme cold",
                hazard_ratio=2.2,
                reason=f"HVAC issue with outdoor temp {temp}°F (extreme cold)",
                category="ENVIRONMENTAL"
            ))
            trace.append(f"× Extreme cold (2.2) = {h:.3f}")
        # Cold + no heat (HR: 1.6)
        elif temp < 50 and is_heating_issue:
            h *= 1.6
            factors.append(PriorityFactor(
                name="No heat + cold",
                hazard_ratio=1.6,
                reason=f"HVAC issue with outdoor temp {temp}°F (cold)",
                category="ENVIRONMENTAL"
            ))
            trace.append(f"× Cold weather (1.6) = {h:.3f}")
        
        # Extreme heat + no AC (HR: 1.8)
        if temp > 95 and is_cooling_issue:
            h *= 1.8
            factors.append(PriorityFactor(
                name="No AC + extreme heat",
                hazard_ratio=1.8,
                reason=f"AC issue with outdoor temp {temp}°F (extreme heat)",
                category="ENVIRONMENTAL"
            ))
            trace.append(f"× Extreme heat (1.8) = {h:.3f}")
        
        # Freeze risk (HR: 1.7)
        if temp < 32 and is_water_issue:
            h *= 1.7
            factors.append(PriorityFactor(
                name="Freeze risk",
                hazard_ratio=1.7,
                reason=f"Water/pipe issue with temp {temp}°F (freeze risk)",
                category="ENVIRONMENTAL"
            ))
            trace.append(f"× Freeze risk (1.7) = {h:.3f}")
        
        return h, factors
    
    def _apply_timing_factors(
        self, h: float, timing: Dict[str, Any], trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply timing hazard ratios. Only one timing factor applies (most specific)."""
        factors = []
        
        # Late night takes precedence (HR: 1.35)
        if timing.get("is_late_night", False):
            h *= 1.35
            factors.append(PriorityFactor(
                name="Late night",
                hazard_ratio=1.35,
                reason="Request submitted during late night hours (10pm-6am)",
                category="TIMING"
            ))
            trace.append(f"× Late night (1.35) = {h:.3f}")
        # Holiday (HR: 1.30)
        elif timing.get("is_holiday", False):
            h *= 1.30
            factors.append(PriorityFactor(
                name="Holiday",
                hazard_ratio=1.30,
                reason="Request submitted on holiday",
                category="TIMING"
            ))
            trace.append(f"× Holiday (1.30) = {h:.3f}")
        # After hours (HR: 1.25)
        elif timing.get("is_after_hours", False):
            h *= 1.25
            factors.append(PriorityFactor(
                name="After hours",
                hazard_ratio=1.25,
                reason="Request submitted outside business hours",
                category="TIMING"
            ))
            trace.append(f"× After hours (1.25) = {h:.3f}")
        # Weekend (HR: 1.15)
        elif timing.get("is_weekend", False):
            h *= 1.15
            factors.append(PriorityFactor(
                name="Weekend",
                hazard_ratio=1.15,
                reason="Request submitted on weekend",
                category="TIMING"
            ))
            trace.append(f"× Weekend (1.15) = {h:.3f}")
        
        return h, factors
    
    def _apply_recurrence_factors(
        self, h: float, history: Dict[str, Any], description: str, trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply recurrence hazard ratios."""
        factors = []
        
        # Third+ occurrence (HR: 2.0)
        recent_count = history.get("recent_issues_count", 0)
        if recent_count >= 3 or self._check_keywords(description, "third_time"):
            h *= 2.0
            factors.append(PriorityFactor(
                name="Third+ occurrence",
                hazard_ratio=2.0,
                reason=f"Issue reported {recent_count}+ times - recurring problem",
                category="RECURRENCE"
            ))
            trace.append(f"× Third+ time (2.0) = {h:.3f}")
        # Previous repair failed (HR: 1.7)
        elif history.get("previous_repair_failed", False) or \
             self._check_keywords(description, "repair_failed"):
            h *= 1.7
            factors.append(PriorityFactor(
                name="Previous repair failed",
                hazard_ratio=1.7,
                reason="Prior repair attempt did not resolve issue",
                category="RECURRENCE"
            ))
            trace.append(f"× Repair failed (1.7) = {h:.3f}")
        # Same issue within 60 days (HR: 1.5)
        elif recent_count >= 1:
            h *= 1.5
            factors.append(PriorityFactor(
                name="Recent similar issue",
                hazard_ratio=1.5,
                reason="Similar issue reported recently",
                category="RECURRENCE"
            ))
            trace.append(f"× Recent issue (1.5) = {h:.3f}")
        
        return h, factors
    
    def _apply_property_factors(
        self, h: float, property_info: Dict[str, Any], trade: str, 
        description: str, trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply property risk hazard ratios."""
        factors = []
        
        # Structural concern (HR: 1.6)
        if self._check_keywords(description, "structural"):
            h *= 1.6
            factors.append(PriorityFactor(
                name="Structural concern",
                hazard_ratio=1.6,
                reason="Potential structural integrity issue",
                category="PROPERTY_RISK"
            ))
            trace.append(f"× Structural (1.6) = {h:.3f}")
        
        # Upper floor water leak (HR: 1.5)
        floor = property_info.get("floor")
        if floor and floor > 1 and trade == "PLUMBING":
            h *= 1.5
            factors.append(PriorityFactor(
                name="Upper floor water leak",
                hazard_ratio=1.5,
                reason=f"Water issue on floor {floor} - affects units below",
                category="PROPERTY_RISK"
            ))
            trace.append(f"× Upper floor (1.5) = {h:.3f}")
        
        # Multi-unit cascade risk (HR: 1.4)
        total_units = property_info.get("total_units", 1)
        if total_units > 1:
            h *= 1.4
            factors.append(PriorityFactor(
                name="Multi-unit building",
                hazard_ratio=1.4,
                reason=f"Issue in {total_units}-unit building - cascade risk",
                category="PROPERTY_RISK"
            ))
            trace.append(f"× Multi-unit (1.4) = {h:.3f}")
        
        return h, factors
    
    def _apply_essential_service_factors(
        self, h: float, description: str, trace: List[str]
    ) -> Tuple[float, List[PriorityFactor]]:
        """Apply essential service loss hazard ratios."""
        factors = []
        
        # Cannot access unit (HR: 2.0)
        if self._check_keywords(description, "locked_out"):
            h *= 2.0
            factors.append(PriorityFactor(
                name="Cannot access unit",
                hazard_ratio=2.0,
                reason="Tenant unable to safely access unit",
                category="ESSENTIAL_SERVICE"
            ))
            trace.append(f"× Locked out (2.0) = {h:.3f}")
        
        # No electricity (HR: 1.9)
        if self._check_keywords(description, "no_power"):
            h *= 1.9
            factors.append(PriorityFactor(
                name="No electricity",
                hazard_ratio=1.9,
                reason="Complete power loss to unit",
                category="ESSENTIAL_SERVICE"
            ))
            trace.append(f"× No power (1.9) = {h:.3f}")
        
        # No running water (HR: 1.8)
        if self._check_keywords(description, "no_water"):
            h *= 1.8
            factors.append(PriorityFactor(
                name="No running water",
                hazard_ratio=1.8,
                reason="Complete water loss",
                category="ESSENTIAL_SERVICE"
            ))
            trace.append(f"× No water (1.8) = {h:.3f}")
        
        # No toilet (HR: 1.7)
        if self._check_keywords(description, "no_toilet"):
            h *= 1.7
            factors.append(PriorityFactor(
                name="No toilet function",
                hazard_ratio=1.7,
                reason="No working toilet in unit",
                category="ESSENTIAL_SERVICE"
            ))
            trace.append(f"× No toilet (1.7) = {h:.3f}")
        
        return h, factors
    
    def _apply_interactions(
        self, h: float, severity: str, applied_factors: List[PriorityFactor],
        tenant: Dict[str, Any], weather: Dict[str, Any], trade: str,
        property_info: Dict[str, Any], timing: Dict[str, Any],
        description: str, trace: List[str]
    ) -> Tuple[float, List[InteractionEffect]]:
        """Apply interaction effects for compound risks."""
        interactions = []
        
        # Get factor categories present
        categories = {f.category for f in applied_factors}
        factor_names = {f.name.lower() for f in applied_factors}
        
        # Vulnerability × Environmental (IR: 1.5)
        has_vulnerability = "VULNERABILITY" in categories
        has_environmental = "ENVIRONMENTAL" in categories
        if has_vulnerability and has_environmental:
            h *= 1.5
            interactions.append(InteractionEffect(
                name="Vulnerability × Environmental",
                interaction_ratio=1.5,
                trigger="Vulnerable tenant + extreme weather condition"
            ))
            trace.append(f"× Vuln×Env (1.5) = {h:.3f}")
        
        # Water × Electrical (IR: 1.6)
        has_water = any(f for f in applied_factors if "water" in f.name.lower())
        has_electrical = trade == "ELECTRICAL" or any(
            f for f in applied_factors if "electrical" in f.name.lower()
        )
        if has_water and has_electrical:
            h *= 1.6
            interactions.append(InteractionEffect(
                name="Water × Electrical",
                interaction_ratio=1.6,
                trigger="Water issue near electrical systems"
            ))
            trace.append(f"× Water×Elec (1.6) = {h:.3f}")
        
        # Recurrence × High Severity (IR: 1.4)
        has_recurrence = "RECURRENCE" in categories
        is_high_severity = severity in ["HIGH", "EMERGENCY"]
        if has_recurrence and is_high_severity:
            h *= 1.4
            interactions.append(InteractionEffect(
                name="Recurrence × High Severity",
                interaction_ratio=1.4,
                trigger=f"Recurring issue with {severity} severity"
            ))
            trace.append(f"× Recur×Sev (1.4) = {h:.3f}")
        
        # Multi-unit × Spreading (IR: 1.5)
        total_units = property_info.get("total_units", 1)
        has_spreading = any(f for f in applied_factors if "spreading" in f.name.lower() or "worse" in f.name.lower())
        if total_units > 1 and has_spreading:
            h *= 1.5
            interactions.append(InteractionEffect(
                name="Multi-unit × Spreading",
                interaction_ratio=1.5,
                trigger="Spreading issue in multi-unit building"
            ))
            trace.append(f"× Multi×Spread (1.5) = {h:.3f}")
        
        # Late Night × Emergency (IR: 1.25)
        is_late_night = timing.get("is_late_night", False)
        is_emergency = severity == "EMERGENCY"
        if is_late_night and is_emergency:
            h *= 1.25
            interactions.append(InteractionEffect(
                name="Late Night × Emergency",
                interaction_ratio=1.25,
                trigger="Emergency during late night hours"
            ))
            trace.append(f"× Night×Emer (1.25) = {h:.3f}")
        
        # Multiple Vulnerabilities (IR: 1.3)
        vulnerability_count = len([f for f in applied_factors if f.category == "VULNERABILITY"])
        if vulnerability_count >= 2:
            h *= 1.3
            interactions.append(InteractionEffect(
                name="Multiple Vulnerabilities",
                interaction_ratio=1.3,
                trigger=f"{vulnerability_count} vulnerability factors present"
            ))
            trace.append(f"× Multi-vuln (1.3) = {h:.3f}")
        
        return h, interactions
    
    def _calculate_confidence(
        self, applied_factors: List[PriorityFactor], severity: str, description: str
    ) -> float:
        """Calculate confidence score based on factor clarity."""
        confidence = 0.85  # Base confidence for deterministic calculation
        
        # More factors = more confidence (clear signals)
        if len(applied_factors) >= 3:
            confidence += 0.05
        elif len(applied_factors) == 0:
            confidence -= 0.10
        
        # Clear severity indicators
        if severity in ["EMERGENCY", "LOW"]:
            confidence += 0.05  # Clear extremes
        
        # Description length affects confidence
        if len(description) > 100:
            confidence += 0.05  # Detailed description
        elif len(description) < 20:
            confidence -= 0.10  # Too short
        
        return max(0.5, min(1.0, confidence))
    
    def run(
        self,
        triage_output: Dict[str, Any],
        request_data: Dict[str, Any]
    ) -> PriorityResult:
        """
        Execute priority calculation (alias for calculate_priority).
        
        Args:
            triage_output: Parsed JSON from Triage Agent
            request_data: Original request JSON
            
        Returns:
            PriorityResult with score and details
        """
        return self.calculate_priority(triage_output, request_data)
    
    def __repr__(self) -> str:
        return "PriorityCalculatorAgent(deterministic=True)"













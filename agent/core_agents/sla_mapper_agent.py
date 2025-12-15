"""
Agent 5: SLA Mapper Agent
Maps priority scores to response and resolution deadlines (deterministic, no LLM).
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SLAResult:
    """Result from SLA calculation."""
    tier: str
    response_deadline: datetime
    resolution_deadline: datetime
    response_hours: int
    resolution_hours: int
    business_hours_only: bool
    vendor_tier: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tier": self.tier,
            "response_deadline": self.response_deadline.isoformat(),
            "resolution_deadline": self.resolution_deadline.isoformat(),
            "response_hours": self.response_hours,
            "resolution_hours": self.resolution_hours,
            "business_hours_only": self.business_hours_only,
            "vendor_tier": self.vendor_tier
        }


class SLAMapperAgent:
    """
    SLA Mapper Agent (Deterministic)
    
    Maps priority scores to SLA tiers and calculates deadlines:
    - EMERGENCY (80-100): 1-4 hours response, 24 hours resolution, 24/7
    - HIGH (60-79): 24 hours response, 48 hours resolution, business hours
    - MEDIUM (25-59): 48 hours response, 5 days resolution, business hours
    - LOW (0-24): 72 hours response, 7 days resolution, business hours
    
    This agent does NOT use LLM - it's a pure deterministic calculation.
    """
    
    def __init__(
        self,
        business_hours_start: int = 9,
        business_hours_end: int = 17,
        business_days: Optional[list] = None
    ):
        """
        Initialize SLA Mapper.
        
        Args:
            business_hours_start: Start of business day (hour, 0-23)
            business_hours_end: End of business day (hour, 0-23)
            business_days: List of business weekdays (0=Monday, 6=Sunday)
        """
        self.business_hours_start = business_hours_start
        self.business_hours_end = business_hours_end
        self.business_days = business_days or [0, 1, 2, 3, 4]  # Mon-Fri
    
    def calculate_sla(
        self,
        priority_score: int,
        submission_time: datetime
    ) -> SLAResult:
        """
        Calculate SLA deadlines based on priority score.
        
        Args:
            priority_score: Priority score (0-100) from Priority Agent
            submission_time: Request submission time (required)
            
        Returns:
            SLAResult with tier and deadlines
        """
        
        # Map score to tier and parameters
        if priority_score >= 80:
            tier = "EMERGENCY"
            response_hours = 4
            resolution_hours = 24
            business_hours_only = False  # 24/7 countdown for emergencies
            vendor_tier = "Premium only"
        elif priority_score >= 60:
            tier = "HIGH"
            response_hours = 24
            resolution_hours = 48
            business_hours_only = True
            vendor_tier = "Preferred + Premium"
        elif priority_score >= 25:
            tier = "MEDIUM"
            response_hours = 48
            resolution_hours = 120  # 5 days
            business_hours_only = True
            vendor_tier = "All qualified"
        else:
            tier = "LOW"
            response_hours = 72
            resolution_hours = 168  # 7 days
            business_hours_only = True
            vendor_tier = "Any available"
        
        # Calculate deadlines
        if business_hours_only:
            response_deadline = self._calculate_business_hours_deadline(
                submission_time, response_hours
            )
            resolution_deadline = self._calculate_business_hours_deadline(
                submission_time, resolution_hours
            )
        else:
            # 24/7 countdown for emergencies
            response_deadline = submission_time + timedelta(hours=response_hours)
            resolution_deadline = submission_time + timedelta(hours=resolution_hours)
        
        return SLAResult(
            tier=tier,
            response_deadline=response_deadline,
            resolution_deadline=resolution_deadline,
            response_hours=response_hours,
            resolution_hours=resolution_hours,
            business_hours_only=business_hours_only,
            vendor_tier=vendor_tier
        )
    
    def _calculate_business_hours_deadline(
        self,
        start_time: datetime,
        hours_needed: int
    ) -> datetime:
        """
        Calculate deadline counting only business hours.
        
        Args:
            start_time: Starting timestamp
            hours_needed: Number of business hours needed
            
        Returns:
            Deadline datetime
        """
        current = start_time
        hours_remaining = hours_needed
        
        # If starting outside business hours, move to next business period
        current = self._move_to_next_business_period(current)
        
        while hours_remaining > 0:
            # Check if current time is within business hours
            if self._is_business_time(current):
                # Calculate hours available in current business day
                day_end = current.replace(
                    hour=self.business_hours_end,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                hours_available = (day_end - current).total_seconds() / 3600
                
                if hours_remaining <= hours_available:
                    # Can finish within current business day
                    return current + timedelta(hours=hours_remaining)
                else:
                    # Use remaining hours in current day
                    hours_remaining -= hours_available
                    # Move to next business day
                    current = day_end
                    current = self._move_to_next_business_period(current)
            else:
                # Move to next business period
                current = self._move_to_next_business_period(current)
        
        return current
    
    def _is_business_time(self, dt: datetime) -> bool:
        """Check if datetime is within business hours."""
        is_business_day = dt.weekday() in self.business_days
        is_business_hour = self.business_hours_start <= dt.hour < self.business_hours_end
        return is_business_day and is_business_hour
    
    def _move_to_next_business_period(self, dt: datetime) -> datetime:
        """Move datetime to the start of the next business period."""
        # If before business hours today, move to start of business hours
        if dt.hour < self.business_hours_start and dt.weekday() in self.business_days:
            return dt.replace(
                hour=self.business_hours_start,
                minute=0,
                second=0,
                microsecond=0
            )
        
        # Otherwise, move to next business day
        next_day = dt + timedelta(days=1)
        next_day = next_day.replace(
            hour=self.business_hours_start,
            minute=0,
            second=0,
            microsecond=0
        )
        
        # Skip weekends/non-business days
        while next_day.weekday() not in self.business_days:
            next_day += timedelta(days=1)
        
        return next_day
    
    def run(
        self,
        priority_score: int,
        submission_time: datetime
    ) -> SLAResult:
        """
        Execute the SLA mapping (alias for calculate_sla).
        
        Args:
            priority_score: Priority score (0-100)
            submission_time: Request submission time (required)
            
        Returns:
            SLAResult with tier and deadlines
        """
        return self.calculate_sla(priority_score, submission_time)
    
    def __repr__(self) -> str:
        return (
            f"SLAMapperAgent(business_hours={self.business_hours_start}-"
            f"{self.business_hours_end}, business_days={self.business_days})"
        )


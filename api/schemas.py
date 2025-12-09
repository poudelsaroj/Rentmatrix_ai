"""
RentMatrix AI - API Schemas
Request and Response Pydantic models
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class TriageRequest(BaseModel):
    """Request model - only description is required as input"""
    description: str = Field(
        ..., 
        description="The maintenance request description from tenant",
        example="Strong gas smell in the basement near the water heater. Started about 20 minutes ago."
    )


class TriageResponse(BaseModel):
    """Response model matching the agent output"""
    severity: str = Field(..., description="LOW|MEDIUM|HIGH|EMERGENCY")
    trade: str = Field(..., description="PLUMBING|ELECTRICAL|HVAC|APPLIANCE|GENERAL|STRUCTURAL")
    reasoning: str = Field(..., description="Chain-of-thought analysis")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    key_factors: List[str] = Field(..., description="Key factors for classification")
    
    # Include the full request context in response
    test_id: Optional[str] = None
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str

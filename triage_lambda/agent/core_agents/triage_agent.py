"""
Agent 1: Triage Classifier Agent
Classifies maintenance requests by severity and trade category.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from ..prompts import SYSTEM_PROMPT_TRIAGE


class TriageAgent(BaseAgent):
    """
    Triage Classifier Agent
    
    Classifies maintenance requests into:
    - Severity: EMERGENCY, HIGH, MEDIUM, LOW
    - Trade: PLUMBING, ELECTRICAL, HVAC, APPLIANCE, CARPENTRY, PAINTING, FLOORING, 
             ROOFING, MASONRY, PEST_CONTROL, LOCKSMITH, LANDSCAPING, WINDOWS_GLASS, 
             DOORS, DRYWALL, STRUCTURAL, GENERAL
    
    Also provides reasoning and confidence score.
    """
    
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(
            name="Triage Classifier Agent",
            model=model,
            temperature=0.2
        )
    
    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_TRIAGE
    
    def build_prompt(self, request_data: Dict[str, Any]) -> str:
        """
        Build the user prompt for triage classification.
        
        Args:
            request_data: Dictionary containing the maintenance request and context.
            
        Returns:
            Formatted prompt string.
        """
        import json
        request_json = json.dumps(request_data, indent=2)
        return f"this is the description of the request: {request_json}"

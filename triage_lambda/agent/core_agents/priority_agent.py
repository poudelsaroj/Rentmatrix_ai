"""
Agent 2: Priority Calculator Agent
Calculates numerical priority score based on severity and context.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from ..prompts import SYSTEM_PROMPT_PRIORITY


class PriorityAgent(BaseAgent):
    """
    Priority Calculator Agent
    
    Calculates a numerical priority score (0-100) based on:
    - Base severity from Agent 1 (Triage)
    - Contextual modifiers (weather, tenant, property, timing, etc.)
    
    Output includes:
    - priority_score: Integer 0-100
    - applied_modifiers: List of modifiers applied
    - base_score: Starting score from severity
    - total_modifiers: Sum of modifier points
    """
    
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(
            name="Priority Calculator Agent",
            model=model,
            temperature=0.1  # Very low for mathematical consistency
        )
    
    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_PRIORITY
    
    def build_prompt(
        self,
        triage_output: str,
        original_request: str
    ) -> str:
        """
        Build the user prompt for priority calculation.
        
        Args:
            triage_output: JSON output from the Triage Agent.
            original_request: The original maintenance request with context.
            
        Returns:
            Formatted prompt string.
        """
        return f"""
Based on the triage classification from Agent 1, calculate the priority score.

## TRIAGE CLASSIFICATION (from Agent 1):
{triage_output}

## ORIGINAL REQUEST CONTEXT:
{original_request}

Calculate the priority score now using the base severity from the triage classification and apply all relevant modifiers based on the context provided.
"""

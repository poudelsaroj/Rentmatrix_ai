"""
Agent 4: Confidence Evaluator Agent
Evaluates confidence in the triage and priority classification decisions.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from ..prompts import SYSTEM_PROMPT_CONFIDENCE


class ConfidenceAgent(BaseAgent):
    """
    Confidence Evaluator Agent
    
    Assesses the quality and reliability of the classification by analyzing:
    - Input quality (description clarity, images, context)
    - Classification consistency (agreement between agents)
    - Risk factors (ambiguity, conflicting signals)
    
    Outputs:
    - confidence: Float 0.30-1.0
    - routing: AUTO_APPROVE | PM_REVIEW_QUEUE | PM_IMMEDIATE_REVIEW
    - confidence_factors: List of factors affecting confidence
    - risk_flags: List of identified risk factors
    """
    
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(
            name="Confidence Evaluator Agent",
            model=model,
            temperature=0.3  # Moderate temperature for balanced assessment
        )
    
    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_CONFIDENCE
    
    def build_prompt(
        self,
        triage_output: str,
        priority_output: str,
        explainer_output: str,
        original_request: str,
    ) -> str:
        """
        Build the user prompt for confidence evaluation.
        
        Args:
            triage_output: JSON output from the Triage Agent.
            priority_output: JSON output from the Priority Agent.
            explainer_output: JSON output from the Explainer Agent.
            original_request: The original maintenance request with context.
            
        Returns:
            Formatted prompt string.
        """
        return f"""
Evaluate the confidence of the AI classification based on the following:

## ORIGINAL REQUEST (Input Quality):
{original_request}

## AGENT 1 OUTPUT (Triage Classification):
{triage_output}

## AGENT 2 OUTPUT (Priority Calculation):
{priority_output}

## AGENT 3 OUTPUT (Explanation):
{explainer_output}

---

Analyze the input quality, classification consistency, and potential risk factors.
Calculate the confidence score (0.30-1.0) and provide routing recommendation.

Respond with the JSON schema defined in the system prompt.
"""

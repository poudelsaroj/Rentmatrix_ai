"""
Agent 3: Explainer Agent
Generates explanations for PMs and tenants based on prior agent outputs.
"""

from typing import Any, Dict
from .base_agent import BaseAgent
from ..prompts import SYSTEM_PROMPT_EXPLAINER


class ExplainerAgent(BaseAgent):
    """Explainer Agent to produce PM and tenant-facing explanations."""

    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(
            name="Explainer Agent",
            model=model,
            temperature=0.3,  # moderate for natural language clarity
        )

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_EXPLAINER

    def build_prompt(
        self,
        triage_output: str,
        priority_output: str,
        original_request: str,
    ) -> str:
        """
        Build the user prompt for the explainer agent.

        Args:
            triage_output: JSON output from Triage Agent.
            priority_output: JSON output from Priority Agent.
            original_request: The original maintenance request prompt text.
        """
        return f"""
Generate explanations for PM and tenant based on the following:

## TRIAGE_RESULT (from Agent 1)
{triage_output}

## PRIORITY_RESULT (from Agent 2)
{priority_output}

## ORIGINAL_REQUEST
{original_request}

Respond with the JSON schema defined in the system prompt.
"""


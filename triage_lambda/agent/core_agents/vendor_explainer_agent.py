"""
Agent 7: Vendor Explainer Agent
Generates comparative explanations for vendor recommendations.
"""

import json
from typing import Any, Dict, List, Union

from .base_agent import BaseAgent
from ..prompts.vendor_explainer_prompt import SYSTEM_PROMPT_VENDOR_EXPLAINER


JsonLike = Union[str, Dict[str, Any], List[Any]]


class VendorExplainerAgent(BaseAgent):
    """Creates pros/cons and comparison views for vendor recommendations."""

    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(
            name="Vendor Explainer Agent",
            model=model,
            temperature=0.25,  # balanced for crisp explanations
        )

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_VENDOR_EXPLAINER

    def _to_json_str(self, payload: JsonLike) -> str:
        """Safely convert dict/list payloads to formatted JSON strings."""
        if isinstance(payload, str):
            return payload
        try:
            return json.dumps(payload, indent=2)
        except (TypeError, ValueError):
            return str(payload)

    def build_prompt(
        self,
        triage_output: JsonLike,
        priority_output: JsonLike,
        vendor_match_output: JsonLike,
        request_data: Dict[str, Any],
        tenant_preferred_times: List[str],
    ) -> str:
        """
        Build the user prompt for the vendor explainer.

        Args:
            triage_output: JSON/dict or raw text from the Triage Agent.
            priority_output: JSON/dict or raw text from the Priority Agent.
            vendor_match_output: JSON/dict or raw text from the Vendor Matching Agent.
            request_data: Original maintenance request context.
            tenant_preferred_times: Tenant's preferred time slots.
        """
        triage_json = self._to_json_str(triage_output)
        priority_json = self._to_json_str(priority_output)
        vendor_json = self._to_json_str(vendor_match_output)
        request_json = self._to_json_str(request_data)
        tenant_times = "\n".join([f"- {slot}" for slot in tenant_preferred_times]) or "None provided"

        return f"""
Create a comparative explanation for the vendor recommendations.

## TRIAGE_RESULT
{triage_json}

## PRIORITY_RESULT
{priority_json}

## VENDOR_MATCHING_RESULT
{vendor_json}

## REQUEST_CONTEXT
{request_json}

## TENANT_PREFERRED_TIMES
{tenant_times}

Follow the JSON response schema and rules from the system prompt.
"""


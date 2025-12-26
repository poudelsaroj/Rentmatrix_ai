# Prompts module
from .triage_prompt import SYSTEM_PROMPT_TRIAGE
from .priority_prompt import SYSTEM_PROMPT_PRIORITY
from .explainer_prompt import SYSTEM_PROMPT_EXPLAINER
from .confidence_prompt import SYSTEM_PROMPT_CONFIDENCE
from .vendor_matching_prompt import SYSTEM_PROMPT_VENDOR_MATCHING
from .vendor_explainer_prompt import SYSTEM_PROMPT_VENDOR_EXPLAINER
from .quotation_analysis_prompt import SYSTEM_PROMPT_QUOTATION_ANALYSIS
from .quotation_comparison_prompt import SYSTEM_PROMPT_QUOTATION_COMPARISON

__all__ = [
    "SYSTEM_PROMPT_TRIAGE",
    "SYSTEM_PROMPT_PRIORITY",
    "SYSTEM_PROMPT_EXPLAINER",
    "SYSTEM_PROMPT_CONFIDENCE",
    "SYSTEM_PROMPT_VENDOR_MATCHING",
    "SYSTEM_PROMPT_VENDOR_EXPLAINER",
    "SYSTEM_PROMPT_QUOTATION_ANALYSIS",
    "SYSTEM_PROMPT_QUOTATION_COMPARISON"
]

"""
RentMatrix AI Agent Package

This package provides AI agents for maintenance request triage and prioritization.

Modules:
    - core_agents: Individual agent implementations
    - prompts: System prompts for each agent
    - pipeline: Pipeline orchestration
    - config: Configuration settings

Usage:
    from agent import TriagePipeline
    
    pipeline = TriagePipeline()
    result = await pipeline.run(request_prompt)
"""

from .core_agents import TriageAgent, PriorityAgent, SLAMapperAgent, SLAResult
from .pipeline import TriagePipeline
from .config import AgentConfig, LangfuseConfig, DEFAULT_AGENT_CONFIG

__all__ = [
    "TriageAgent",
    "PriorityAgent",
    "SLAMapperAgent",
    "SLAResult",
    "TriagePipeline",
    "AgentConfig",
    "LangfuseConfig",
    "DEFAULT_AGENT_CONFIG"
]

__version__ = "1.0.0"

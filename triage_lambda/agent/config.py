"""
Configuration settings for the RentMatrix AI agents.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for AI agents."""
    
    # Model settings
    triage_model: str = "gpt-5-mini"
    priority_model: str = "gpt-5-mini"
    
    # Temperature settings
    triage_temperature: float = 0.2
    priority_temperature: float = 0.1
    
    # Token limits
    triage_max_tokens: int = 1500
    priority_max_tokens: int = 300


@dataclass
class LangfuseConfig:
    """Configuration for Langfuse tracing."""
    
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    host: str = "https://cloud.langfuse.com"
    enabled: bool = True
    
    @classmethod
    def from_env(cls) -> "LangfuseConfig":
        """Load configuration from environment variables."""
        return cls(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            enabled=os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"
        )


# Default configurations
DEFAULT_AGENT_CONFIG = AgentConfig()
DEFAULT_LANGFUSE_CONFIG = LangfuseConfig.from_env()

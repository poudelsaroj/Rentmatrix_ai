"""
Base Agent Class
Provides common functionality for all agents in the pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from agents import Agent, Runner


class BaseAgent(ABC):
    """Abstract base class for all RentMatrix agents."""
    
    def __init__(
        self,
        name: str,
        model: str = "gpt-5-mini",
        temperature: float = 0.2
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self._agent: Optional[Agent] = None
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @property
    def agent(self) -> Agent:
        """Lazy initialization of the Agent instance."""
        if self._agent is None:
            self._agent = Agent(
                name=self.name,
                model=self.model,
                instructions=self.system_prompt,
            )
        return self._agent
    
    async def run(self, input_prompt: str) -> Any:
        """
        Execute the agent with the given input.
        
        Args:
            input_prompt: The input prompt for the agent.
            
        Returns:
            The agent's response.
        """
        result = await Runner.run(self.agent, input=input_prompt)
        return result
    
    def build_prompt(self, **kwargs) -> str:
        """
        Build the user prompt for this agent.
        Override in subclasses for custom prompt building.
        
        Args:
            **kwargs: Arguments to build the prompt.
            
        Returns:
            The formatted user prompt string.
        """
        raise NotImplementedError("Subclasses must implement build_prompt()")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', model='{self.model}')"

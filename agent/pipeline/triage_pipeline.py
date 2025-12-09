"""
Triage Pipeline
Orchestrates the flow of data through multiple agents.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..core_agents import TriageAgent, PriorityAgent


@dataclass
class PipelineResult:
    """Result from the triage pipeline."""
    triage_output: str
    priority_output: str
    triage_parsed: Optional[Dict[str, Any]] = None
    priority_parsed: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "triage": self.triage_parsed or self.triage_output,
            "priority": self.priority_parsed or self.priority_output
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class TriagePipeline:
    """
    Orchestrates the triage pipeline flow:
    
    Agent 1 (Triage) → Agent 2 (Priority Calculator) → Final Result
    
    Usage:
        pipeline = TriagePipeline()
        result = await pipeline.run(request_data)
    """
    
    def __init__(
        self,
        triage_model: str = "gpt-5-mini",
        priority_model: str = "gpt-5-mini",
        verbose: bool = True
    ):
        """
        Initialize the pipeline with agents.
        
        Args:
            triage_model: Model to use for triage agent.
            priority_model: Model to use for priority agent.
            verbose: Whether to print progress messages.
        """
        self.triage_agent = TriageAgent(model=triage_model)
        self.priority_agent = PriorityAgent(model=priority_model)
        self.verbose = verbose
    
    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _parse_json_safe(self, text: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from agent output."""
        try:
            # Try to extract JSON from the response
            # Handle cases where there might be extra text
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return None
    
    async def run(self, request_prompt: str) -> PipelineResult:
        """
        Run the full triage pipeline.
        
        Args:
            request_prompt: The formatted maintenance request prompt.
            
        Returns:
            PipelineResult containing outputs from all agents.
        """
        self._log("=" * 60)
        self._log("RENTMATRIX AI TRIAGE PIPELINE")
        self._log("=" * 60)
        
        # Step 1: Run Triage Agent
        self._log("\n[STEP 1] Running Triage Classifier Agent...")
        self._log("-" * 40)
        
        triage_result = await self.triage_agent.run(request_prompt)
        triage_output = triage_result.final_output
        
        self._log("\n✅ Agent 1 (Triage Classifier) Output:")
        self._log(triage_output)
        
        # Step 2: Build prompt for Priority Agent
        priority_prompt = self.priority_agent.build_prompt(
            triage_output=triage_output,
            original_request=request_prompt
        )
        
        # Step 3: Run Priority Agent
        self._log("\n[STEP 2] Running Priority Calculator Agent...")
        self._log("-" * 40)
        
        priority_result = await self.priority_agent.run(priority_prompt)
        priority_output = priority_result.final_output
        
        self._log("\n✅ Agent 2 (Priority Calculator) Output:")
        self._log(priority_output)
        
        # Parse outputs
        triage_parsed = self._parse_json_safe(triage_output)
        priority_parsed = self._parse_json_safe(priority_output)
        
        # Create result
        result = PipelineResult(
            triage_output=triage_output,
            priority_output=priority_output,
            triage_parsed=triage_parsed,
            priority_parsed=priority_parsed
        )
        
        # Print summary
        self._log("\n" + "=" * 60)
        self._log("PIPELINE COMPLETE - FINAL SUMMARY")
        self._log("=" * 60)
        
        if triage_parsed:
            self._log(f"\n📋 Severity: {triage_parsed.get('severity', 'N/A')}")
            self._log(f"📋 Trade: {triage_parsed.get('trade', 'N/A')}")
            self._log(f"📋 Confidence: {triage_parsed.get('confidence', 'N/A')}")
        
        if priority_parsed:
            self._log(f"\n📊 Priority Score: {priority_parsed.get('priority_score', 'N/A')}/100")
            self._log(f"📊 Base Score: {priority_parsed.get('base_score', 'N/A')}")
            self._log(f"📊 Total Modifiers: +{priority_parsed.get('total_modifiers', 0)}")
        
        return result
    
    async def run_with_data(self, request_data: Dict[str, Any]) -> PipelineResult:
        """
        Run the pipeline with structured request data.
        
        Args:
            request_data: Dictionary containing the maintenance request and context.
            
        Returns:
            PipelineResult containing outputs from all agents.
        """
        prompt = self.triage_agent.build_prompt(request_data)
        return await self.run(prompt)

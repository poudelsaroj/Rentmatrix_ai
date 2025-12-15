"""
Triage Pipeline
Orchestrates the flow of data through multiple agents.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from ..core_agents import (
    TriageAgent, 
    PriorityAgent, 
    ExplainerAgent, 
    ConfidenceAgent, 
    SLAMapperAgent, 
    SLAResult,
    PriorityCalculatorAgent,
    PriorityResult
)


@dataclass
class PipelineResult:
    """Result from the triage pipeline."""
    triage_output: str
    priority_output: str
    explainer_output: str
    confidence_output: str
    sla_result: Optional[SLAResult] = None
    triage_parsed: Optional[Dict[str, Any]] = None
    priority_parsed: Optional[Dict[str, Any]] = None
    explainer_parsed: Optional[Dict[str, Any]] = None
    confidence_parsed: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            "triage": self.triage_parsed or self.triage_output,
            "priority": self.priority_parsed or self.priority_output,
            "explanation": self.explainer_parsed or self.explainer_output,
            "confidence": self.confidence_parsed or self.confidence_output
        }
        if self.sla_result:
            result["sla"] = self.sla_result.to_dict()
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class TriagePipeline:
    """
    Orchestrates the triage pipeline flow:
    
    Agent 1 (Triage/LLM) → Agent 2 (Priority/Deterministic) → Agent 3 (Explainer/LLM) → Agent 4 (Confidence/LLM) → Agent 5 (SLA/Deterministic) → Final Result
    
    Usage:
        pipeline = TriagePipeline()
        result = await pipeline.run(request_data)
    """
    
    def __init__(
        self,
        triage_model: str = "gpt-5-mini",
        explainer_model: str = "gpt-5-mini",
        confidence_model: str = "gpt-5-mini",
        use_deterministic_priority: bool = True,
        verbose: bool = True
    ):
        """
        Initialize the pipeline with agents.
        
        Args:
            triage_model: Model to use for triage agent.
            explainer_model: Model to use for explainer agent.
            confidence_model: Model to use for confidence agent.
            use_deterministic_priority: Use deterministic priority calculator (faster).
            verbose: Whether to print progress messages.
        """
        self.triage_agent = TriageAgent(model=triage_model)
        self.use_deterministic_priority = use_deterministic_priority
        if use_deterministic_priority:
            self.priority_calculator = PriorityCalculatorAgent()
        else:
            self.priority_agent = PriorityAgent(model="gpt-5-mini")
        self.explainer_agent = ExplainerAgent(model=explainer_model)
        self.confidence_agent = ConfidenceAgent(model=confidence_model)
        self.sla_mapper = SLAMapperAgent()
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
    
    async def run(
        self, 
        request_prompt: str, 
        submission_time: Optional[datetime] = None,
        request_data: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Run the full triage pipeline.
        
        Args:
            request_prompt: The formatted maintenance request prompt.
            submission_time: Optional submission time for SLA calculation.
            request_data: Original request data (required for deterministic priority).
            
        Returns:
            PipelineResult containing outputs from all agents.
        """
        self._log("=" * 60)
        self._log("RENTMATRIX AI TRIAGE PIPELINE")
        self._log("=" * 60)
        
        # Step 1: Run Triage Agent (LLM)
        self._log("\n[STEP 1] Running Triage Classifier Agent (LLM)...")
        self._log("-" * 40)
        
        triage_result = await self.triage_agent.run(request_prompt)
        triage_output = triage_result.final_output
        
        self._log("\n✅ Agent 1 (Triage Classifier) Output:")
        self._log(triage_output)
        
        # Parse triage output for priority calculation
        triage_parsed = self._parse_json_safe(triage_output)
        
        # Step 2: Run Priority Calculator
        self._log("\n[STEP 2] Running Priority Calculator Agent...")
        self._log("-" * 40)
        
        if self.use_deterministic_priority and triage_parsed and request_data:
            # Deterministic calculation (instant)
            self._log("(Using deterministic calculator - instant)")
            priority_calc_result = self.priority_calculator.run(
                triage_output=triage_parsed,
                request_data=request_data
            )
            priority_output = json.dumps(priority_calc_result.to_dict(), indent=2)
            priority_parsed = priority_calc_result.to_dict()
        else:
            # Fallback to LLM-based priority agent
            self._log("(Using LLM-based calculator)")
            priority_prompt = self.priority_agent.build_prompt(
                triage_output=triage_output,
                original_request=request_prompt
            )
            priority_result = await self.priority_agent.run(priority_prompt)
            priority_output = priority_result.final_output
            priority_parsed = self._parse_json_safe(priority_output)
        
        self._log("\n✅ Agent 2 (Priority Calculator) Output:")
        self._log(priority_output)

        # Step 3: Build prompt for Explainer Agent
        explainer_prompt = self.explainer_agent.build_prompt(
            triage_output=triage_output,
            priority_output=priority_output,
            original_request=request_prompt,
        )

        # Step 4: Run Explainer Agent (LLM)
        self._log("\n[STEP 3] Running Explainer Agent (LLM)...")
        self._log("-" * 40)

        explainer_result = await self.explainer_agent.run(explainer_prompt)
        explainer_output = explainer_result.final_output

        self._log("\n✅ Agent 3 (Explainer) Output:")
        self._log(explainer_output)

        # Step 5: Build prompt for Confidence Agent
        confidence_prompt = self.confidence_agent.build_prompt(
            triage_output=triage_output,
            priority_output=priority_output,
            explainer_output=explainer_output,
            original_request=request_prompt,
        )

        # Step 6: Run Confidence Agent (LLM)
        self._log("\n[STEP 4] Running Confidence Evaluator Agent (LLM)...")
        self._log("-" * 40)

        confidence_result = await self.confidence_agent.run(confidence_prompt)
        confidence_output = confidence_result.final_output

        self._log("\n✅ Agent 4 (Confidence Evaluator) Output:")
        self._log(confidence_output)
        
        # Parse remaining outputs
        explainer_parsed = self._parse_json_safe(explainer_output)
        confidence_parsed = self._parse_json_safe(confidence_output)
        
        # Step 8: Run SLA Mapper (deterministic, no LLM)
        self._log("\n[STEP 5] Running SLA Mapper Agent...")
        self._log("-" * 40)
        
        sla_result = None
        if priority_parsed and "priority_score" in priority_parsed and submission_time:
            priority_score = priority_parsed["priority_score"]
            sla_result = self.sla_mapper.run(
                priority_score=priority_score,
                submission_time=submission_time
            )
            
            self._log("\n✅ Agent 5 (SLA Mapper) Output:")
            self._log(f"  Tier: {sla_result.tier}")
            self._log(f"  Response Deadline: {sla_result.response_deadline.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log(f"  Resolution Deadline: {sla_result.resolution_deadline.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self._log("\n⚠️  Agent 5 (SLA Mapper) skipped - priority score or submission time not available")
        
        # Create result
        result = PipelineResult(
            triage_output=triage_output,
            priority_output=priority_output,
            explainer_output=explainer_output,
            confidence_output=confidence_output,
            sla_result=sla_result,
            triage_parsed=triage_parsed,
            priority_parsed=priority_parsed,
            explainer_parsed=explainer_parsed,
            confidence_parsed=confidence_parsed,
        )
        
        # Print summary
        self._log("\n" + "=" * 60)
        self._log("PIPELINE COMPLETE - FINAL SUMMARY")
        self._log("=" * 60)
        
        if triage_parsed:
            self._log(f"\n📋 Severity: {triage_parsed.get('severity', 'N/A')}")
            self._log(f"📋 Trade: {triage_parsed.get('trade', 'N/A')}")
            self._log(f"📋 Triage Confidence: {triage_parsed.get('confidence', 'N/A')}")
        
        if priority_parsed:
            self._log(f"\n📊 Priority Score: {priority_parsed.get('priority_score', 'N/A')}/100")
            self._log(f"📊 Base Score: {priority_parsed.get('base_score', 'N/A')}")
            self._log(f"📊 Total Modifiers: +{priority_parsed.get('total_modifiers', 0)}")

        if explainer_parsed:
            self._log("\n📝 Explanations ready.")

        if confidence_parsed:
            self._log(f"\n🎯 Overall Confidence: {confidence_parsed.get('confidence', 'N/A')}")
            self._log(f"🎯 Routing Decision: {confidence_parsed.get('routing', 'N/A')}")
            risk_flags = confidence_parsed.get('risk_flags', [])
            if risk_flags:
                self._log(f"⚠️  Risk Flags: {', '.join(risk_flags)}")
        
        if sla_result:
            self._log(f"\n⏰ SLA Tier: {sla_result.tier}")
            self._log(f"⏰ Response Deadline: {sla_result.response_deadline.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log(f"⏰ Resolution Deadline: {sla_result.resolution_deadline.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log(f"⏰ Vendor Tier: {sla_result.vendor_tier}")
        
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
        
        # Extract submission time from request data
        submission_time = None
        if "request" in request_data and "reported_at" in request_data["request"]:
            reported_at = request_data["request"]["reported_at"]
            try:
                # Parse ISO format timestamp
                submission_time = datetime.fromisoformat(reported_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        return await self.run(
            prompt, 
            submission_time=submission_time,
            request_data=request_data  # Pass for deterministic priority calculator
        )

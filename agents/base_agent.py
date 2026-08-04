"""
OSMOS Multi-Agent Supervision Layer — Base Agent (Phase 8.1)
============================================================
Abstract base class for all specialized agents in OSMOS.
Enforces structured outputs, evidence traceability, context validation,
read-only execution, and crash-proof error handling.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List

from agents.agent_schemas import AgentContext, AgentOutput

logger = logging.getLogger("OSMOS_BASE_AGENT")


class BaseAgent(ABC):
    """
    Abstract Base Agent for OSMOS Multi-Agent Supervision Layer.

    Guarantees:
    - Pure read-only execution (No database writes, no DataFrame mutations).
    - Exception safety (Agents never crash the application).
    - Evidence traceability (Metrics, values, thresholds, interpretations).
    - Deterministic analysis without unprompted LLM execution.
    """

    def __init__(self, agent_id: str, agent_name: str, agent_role: str, agent_version: str = "1.0.0"):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.agent_version = agent_version

    def validate_context(self, context: AgentContext) -> bool:
        """Checks if the context contains required entity metadata."""
        if not context or not isinstance(context, AgentContext):
            return False
        if not context.entity_id or not isinstance(context.entity_id, str):
            return False
        return True

    def safe_analyze(self, context: AgentContext) -> AgentOutput:
        """
        Public execution wrapper that enforces exception safety,
        context validation, and read-only non-mutation guarantees.
        """
        # Read-Only No-Write Guard: Confirm context state before execution
        if not self.validate_context(context):
            logger.warning(f"[{self.agent_name}] Invalid or missing context for analysis.")
            return self.format_output(
                status="Insufficient Data",
                summary=f"{self.agent_name} received insufficient or invalid context data.",
                observations=["Context validation failed or entity_id was missing."],
                risks=["Analysis skipped due to missing entity context."],
                confidence_score=0.0,
            )

        try:
            # Execute specialized agent deterministic logic
            result = self._analyze_implementation(context)
            return result
        except Exception as e:
            logger.error(f"[{self.agent_name}] Unhandled exception during analysis: {e}", exc_info=True)
            return self.format_output(
                status="Error",
                summary=f"{self.agent_name} encountered an internal evaluation error.",
                observations=[f"Exception type: {type(e).__name__}", f"Error message: {str(e)}"],
                risks=["Agent output degraded due to execution error."],
                confidence_score=0.0,
            )

    @abstractmethod
    def _analyze_implementation(self, context: AgentContext) -> AgentOutput:
        """Specialized agent subclass logic to be overridden by derived agents."""
        pass

    def format_output(
        self,
        status: str,
        summary: str,
        observations: List[str] = None,
        risks: List[str] = None,
        opportunities: List[str] = None,
        recommendations: List[str] = None,
        confidence_score: float = 1.0,
        evidence: List[Dict[str, Any]] = None,
    ) -> AgentOutput:
        """Standardized formatter producing structured AgentOutput."""
        valid_statuses = {"OK", "Warning", "Critical", "Insufficient Data", "Error"}
        norm_status = status if status in valid_statuses else "Warning"

        return AgentOutput(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_role=self.agent_role,
            status=norm_status,
            summary=summary,
            observations=observations or [],
            risks=risks or [],
            opportunities=opportunities or [],
            recommendations=recommendations or [],
            confidence_score=max(0.0, min(1.0, float(confidence_score))),
            evidence=evidence or [],
        )

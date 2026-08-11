"""
OSMOS A/B Testing Schemas (Phase 8.8)
=====================================
Dataclasses representing A/B test experiments, campaign variants, simulated responses,
and evaluation recommendations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ABVariant:
    variant_label: str  # 'A', 'B', 'C'
    variant_title: str
    message_text: str
    offer_type: str = "none"  # 'discount', 'service_recovery', 'vip_perk', 'onboarding', 'reactivation', 'none'
    incentive_value: float = 0.0
    channel: str = "email"  # 'email', 'sms', 'phone', 'web_notification', 'simulated_only'
    tone: str = "commercial"  # 'commercial', 'empathetic', 'informational', 'exclusive'
    call_to_action: str = ""
    expected_behavior: str = ""
    validation_status: str = "Valid"
    validation_warnings: List[str] = field(default_factory=list)
    variant_id: Optional[int] = None
    experiment_id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "experiment_id": self.experiment_id,
            "variant_label": self.variant_label,
            "variant_title": self.variant_title,
            "message_text": self.message_text,
            "offer_type": self.offer_type,
            "incentive_value": self.incentive_value,
            "channel": self.channel,
            "tone": self.tone,
            "call_to_action": self.call_to_action,
            "expected_behavior": self.expected_behavior,
            "validation_status": self.validation_status,
            "validation_warnings": self.validation_warnings,
            "created_at": self.created_at,
        }


@dataclass
class SimulatedResponse:
    variant_label: str
    predicted_open_probability: float
    predicted_click_probability: float
    predicted_conversion_probability: float
    predicted_complaint_probability: float
    predicted_churn_delta: float  # Negative indicates churn reduction (good)
    predicted_clv_delta: float  # Value lift in MAD
    predicted_rfm_es_delta: float
    predicted_satisfaction_delta: float
    simulated_response_type: str  # 'Opened', 'Clicked', 'Converted', 'Complained', 'Ignored'
    simulation_reason: str
    response_score: float  # 0.0 to 100.0
    variant_id: Optional[int] = None
    experiment_id: Optional[int] = None
    entity_id: Optional[str] = None
    response_id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "experiment_id": self.experiment_id,
            "variant_id": self.variant_id,
            "variant_label": self.variant_label,
            "entity_id": self.entity_id,
            "predicted_open_probability": self.predicted_open_probability,
            "predicted_click_probability": self.predicted_click_probability,
            "predicted_conversion_probability": self.predicted_conversion_probability,
            "predicted_complaint_probability": self.predicted_complaint_probability,
            "predicted_churn_delta": self.predicted_churn_delta,
            "predicted_clv_delta": self.predicted_clv_delta,
            "predicted_rfm_es_delta": self.predicted_rfm_es_delta,
            "predicted_satisfaction_delta": self.predicted_satisfaction_delta,
            "simulated_response_type": self.simulated_response_type,
            "simulation_reason": self.simulation_reason,
            "response_score": self.response_score,
            "created_at": self.created_at,
        }


@dataclass
class ABRecommendation:
    winning_variant_label: str
    confidence_score: float  # 0.0 to 1.0
    recommendation_summary: str
    decision_reason: str
    risk_notes: str
    winning_variant_id: Optional[int] = None
    experiment_id: Optional[int] = None
    recommendation_id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "experiment_id": self.experiment_id,
            "winning_variant_id": self.winning_variant_id,
            "winning_variant_label": self.winning_variant_label,
            "confidence_score": self.confidence_score,
            "recommendation_summary": self.recommendation_summary,
            "decision_reason": self.decision_reason,
            "risk_notes": self.risk_notes,
            "created_at": self.created_at,
        }


@dataclass
class ABExperiment:
    entity_id: str
    experiment_name: str
    admin_question: str
    objective: str  # 'retention', 'conversion', 'upsell', 'reactivation', 'complaint_recovery', 'engagement'
    target_segment: Optional[str] = None
    target_persona: Optional[str] = None
    status: str = "Draft"  # 'Draft', 'Simulated', 'Converted to Campaign', 'Archived'
    created_by: str = "admin"
    storage_mode: str = "postgres"
    llm_generated: bool = False
    notes: Optional[str] = None
    experiment_id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "entity_id": self.entity_id,
            "experiment_name": self.experiment_name,
            "admin_question": self.admin_question,
            "objective": self.objective,
            "target_segment": self.target_segment,
            "target_persona": self.target_persona,
            "status": self.status,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "storage_mode": self.storage_mode,
            "llm_generated": self.llm_generated,
            "notes": self.notes,
        }


@dataclass
class ABEvaluationResult:
    experiment: ABExperiment
    variants: List[ABVariant]
    responses: List[SimulatedResponse]
    recommendation: ABRecommendation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment": self.experiment.to_dict(),
            "variants": [v.to_dict() for v in self.variants],
            "responses": [r.to_dict() for r in self.responses],
            "recommendation": self.recommendation.to_dict(),
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
        }

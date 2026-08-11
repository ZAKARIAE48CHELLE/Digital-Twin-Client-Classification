"""
OSMOS A/B Test & Digital Twin Response Simulator Module (Phase 8.8)
===================================================================
Provides A/B experiment formulation, LLM variant generation, deterministic validation,
Digital Twin behavioral response simulation, multi-variant ranking, and human governance integration.
"""

from ab_testing.ab_test_schemas import (
    ABExperiment,
    ABVariant,
    SimulatedResponse,
    ABRecommendation,
    ABEvaluationResult,
)
from ab_testing.ab_test_repository import (
    save_ab_experiment,
    get_ab_experiments_for_entity,
    get_latest_ab_experiment_for_entity,
    get_ab_experiment_details,
    convert_variant_to_campaign_draft,
    apply_simulated_response_as_event,
)
from ab_testing.ab_test_variant_generator import generate_llm_ab_variants
from ab_testing.ab_test_validator import validate_ab_variants
from ab_testing.digital_twin_response_simulator import simulate_digital_twin_response
from ab_testing.ab_test_evaluator import evaluate_ab_experiment

__all__ = [
    "ABExperiment",
    "ABVariant",
    "SimulatedResponse",
    "ABRecommendation",
    "ABEvaluationResult",
    "save_ab_experiment",
    "get_ab_experiments_for_entity",
    "get_latest_ab_experiment_for_entity",
    "get_ab_experiment_details",
    "convert_variant_to_campaign_draft",
    "apply_simulated_response_as_event",
    "generate_llm_ab_variants",
    "validate_ab_variants",
    "simulate_digital_twin_response",
    "evaluate_ab_experiment",
]

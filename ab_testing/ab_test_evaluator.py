"""
OSMOS A/B Test Evaluator (Phase 8.8)
====================================
Orchestrates variant validation, Digital Twin response simulation, variant ranking,
winner selection, confidence scoring, and academic recommendation synthesis.
"""

import logging
from typing import Dict, Any, List
from ab_testing.ab_test_schemas import (
    ABExperiment,
    ABVariant,
    SimulatedResponse,
    ABRecommendation,
    ABEvaluationResult,
)
from ab_testing.ab_test_validator import validate_ab_variants
from ab_testing.digital_twin_response_simulator import simulate_digital_twin_response

logger = logging.getLogger("OSMOS_AB_EVALUATOR")


def evaluate_ab_experiment(
    experiment: ABExperiment,
    variants: List[ABVariant],
    entity_profile: Dict[str, Any]
) -> ABEvaluationResult:
    """
    Evaluates an A/B experiment across candidate variants for a target Digital Twin profile.
    Returns complete ABEvaluationResult with winning variant ranking and decision rationale.
    """
    # 1. Deterministic Rule Validation
    val_res = validate_ab_variants(variants, entity_profile, objective=experiment.objective)
    is_valid = val_res["is_valid"]
    val_errors = val_res["errors"]
    val_warnings = val_res["warnings"]
    norm_variants = val_res["normalized_variants"]

    if not is_valid and not norm_variants:
        # Emergency recovery
        norm_variants = variants

    # 2. Simulate Digital Twin Responses
    responses: List[SimulatedResponse] = []
    for var in norm_variants:
        resp = simulate_digital_twin_response(entity_profile, var)
        responses.append(resp)

    # 3. Rank Variants by Response Score
    responses_sorted = sorted(responses, key=lambda r: r.response_score, reverse=True)
    winner_resp = responses_sorted[0]
    runner_up_resp = responses_sorted[1] if len(responses_sorted) > 1 else None

    # 4. Calculate Confidence Score (0.50 to 0.99 based on score separation)
    if runner_up_resp:
        score_diff = winner_resp.response_score - runner_up_resp.response_score
        confidence = min(0.99, max(0.55, 0.60 + (score_diff / 50.0)))
    else:
        confidence = 0.85

    # 5. Synthesize Recommendation Rationale
    winning_label = winner_resp.variant_label
    winning_var = next((v for v in norm_variants if v.variant_label == winning_label), norm_variants[0])

    persona = entity_profile.get("customer_persona", "Regular Buyer")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    churn_risk = float(entity_profile.get("churn_risk_score", 0.30))

    summary = (
        f"Variant {winning_label} ('{winning_var.variant_title}') is recommended as the winning strategy "
        f"with an overall response score of {winner_resp.response_score:.1f}/100 and {confidence*100:.0f}% confidence."
    )

    reason_parts = [
        f"Entity [{experiment.entity_id}] belongs to segment '{segment}' and is mapped to persona '{persona}'."
    ]
    if winner_resp.predicted_churn_delta < 0:
        reason_parts.append(f"Variant {winning_label} achieves a churn risk reduction of {abs(winner_resp.predicted_churn_delta)*100:.1f}%.")
    if winner_resp.predicted_clv_delta > 0:
        reason_parts.append(f"Expected CLV value lift is +{winner_resp.predicted_clv_delta:.2f} MAD.")
    reason_parts.append(winner_resp.simulation_reason)

    decision_reason = " ".join(reason_parts)

    # Risk & Caveat Notes
    risk_parts = []
    if winner_resp.predicted_complaint_probability > 0.15:
        risk_parts.append(f"Elevated complaint risk ({winner_resp.predicted_complaint_probability*100:.1f}%) detected.")
    if winning_var.incentive_value > 15.0:
        risk_parts.append(f"Incentive value ({winning_var.incentive_value}) causes margin dilution.")
    if val_warnings:
        risk_parts.extend(val_warnings)

    risk_notes = " ".join(risk_parts) if risk_parts else "No significant operational risks identified for the winning variant."

    recommendation = ABRecommendation(
        winning_variant_label=winning_label,
        confidence_score=round(confidence, 4),
        recommendation_summary=summary,
        decision_reason=decision_reason,
        risk_notes=risk_notes,
    )

    return ABEvaluationResult(
        experiment=experiment,
        variants=norm_variants,
        responses=responses_sorted,
        recommendation=recommendation,
        is_valid=is_valid,
        validation_errors=val_errors,
        validation_warnings=val_warnings,
    )

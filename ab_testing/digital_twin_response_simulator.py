"""
OSMOS Digital Twin Response Simulator (Phase 8.8)
=================================================
Core behavioral simulator evaluating how a specific Digital Twin profile reacts
to candidate campaign variants based on state metrics, persona, churn risk, and spend tier.

Deterministic Guarantee:
Behavioral responses are calculated deterministically using rule-based domain logic.
Zero database mutations occur during response simulation.
"""

import logging
from typing import Dict, Any
from ab_testing.ab_test_schemas import ABVariant, SimulatedResponse

logger = logging.getLogger("OSMOS_DT_SIMULATOR")


def simulate_digital_twin_response(
    entity_profile: Dict[str, Any],
    variant: ABVariant,
    use_controlled_noise: bool = False
) -> SimulatedResponse:
    """
    Simulates how a specific customer Digital Twin profile reacts to an A/B campaign variant.
    Computes probabilities, metric deltas, simulated response type, reasoning, and composite response score (0-100).
    """
    entity_id = entity_profile.get("entity_id", "P_DEMO_001")
    entity_type = entity_profile.get("entity_type", "Client")
    dynamic_class = entity_profile.get("dynamic_class", "Active Client")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    persona = entity_profile.get("customer_persona", "Regular Buyer")
    churn_risk = float(entity_profile.get("churn_risk_score", 0.30))
    clv_amount = float(entity_profile.get("predicted_clv_amount_mad", 500.0))
    rfm_score = float(entity_profile.get("rfm_score", 0.50))
    review_score = float(entity_profile.get("review_score_avg", 4.0))
    complaint_count = float(entity_profile.get("complaint_count_90d", 0.0))

    offer_type = variant.offer_type.lower()
    tone = variant.tone.lower()
    channel = variant.channel.lower()
    incentive = float(variant.incentive_value)

    pers_lower = persona.lower()
    seg_lower = segment.lower()

    # Persona & State Classifications
    is_frustrated = ("frustrated" in pers_lower or "complaint" in seg_lower or complaint_count >= 2.0 or review_score < 3.0)
    is_vip = ("premium" in pers_lower or "vip" in pers_lower or "high-value" in seg_lower or clv_amount >= 1500.0)
    is_prospect = (entity_type == "Prospect" or "explorer" in pers_lower or dynamic_class in ["Cold Prospect", "Warm Prospect"])
    is_dormant = ("sleeping" in pers_lower or "dormant" in seg_lower or rfm_score < 0.35)

    # 1. Base Probabilities Initialization
    open_prob = 0.50
    click_prob = 0.30
    conv_prob = 0.20
    complaint_prob = 0.05

    churn_delta = 0.0
    clv_delta = 0.0
    rfm_es_delta = 0.05
    satisfaction_delta = 0.05

    reason_parts = []

    # 2. Channel Affinity Adjustments
    if channel == "email":
        open_prob += 0.05
    elif channel == "sms":
        open_prob += 0.15
        click_prob += 0.05
    elif channel == "phone":
        open_prob += 0.25
        if is_frustrated and tone == "empathetic":
            satisfaction_delta += 0.10

    # 3. Behavioral Reactions per Persona / State Segment

    # CASE A: Complaint-Driven / Frustrated Client
    if is_frustrated:
        reason_parts.append(f"Entity [{entity_id}] is mapped to 'Frustrated Client' / Complaint-Driven state.")
        if offer_type == "service_recovery" or tone == "empathetic":
            open_prob = 0.75
            click_prob = 0.55
            conv_prob = 0.35
            complaint_prob = 0.02
            churn_delta = -0.20  # Significant churn reduction (good)
            satisfaction_delta = +0.25
            rfm_es_delta = +0.15
            clv_delta = +150.0
            reason_parts.append("Empathetic service recovery resolves customer friction effectively, reducing churn risk by 20% and improving satisfaction.")
        elif offer_type == "discount":
            open_prob = 0.60
            click_prob = 0.45
            conv_prob = 0.30
            complaint_prob = 0.10
            churn_delta = -0.05
            satisfaction_delta = +0.05
            clv_delta = +80.0
            reason_parts.append("Commercial discount incentive yields moderate click engagement but fails to fully resolve underlying service friction.")
        elif offer_type == "vip_perk" or tone == "exclusive":
            open_prob = 0.40
            click_prob = 0.15
            conv_prob = 0.05
            complaint_prob = 0.40  # High complaint risk for pushy VIP pitch to frustrated customer
            churn_delta = +0.10  # Churn increases (bad)
            satisfaction_delta = -0.15
            reason_parts.append("Pushy VIP proposal to a frustrated customer triggers negative sentiment and elevated complaint risk.")

    # CASE B: High-Value Loyalist / Premium Loyalist
    elif is_vip:
        reason_parts.append(f"Entity [{entity_id}] is mapped to 'Premium Loyalist' (High CLV: {clv_amount:.0f} MAD).")
        if offer_type == "vip_perk" or tone == "exclusive":
            open_prob = 0.85
            click_prob = 0.65
            conv_prob = 0.55
            complaint_prob = 0.01
            churn_delta = -0.10
            satisfaction_delta = +0.20
            clv_delta = +350.0
            rfm_es_delta = +0.15
            reason_parts.append("Exclusive VIP concierge perk strongly aligns with high-value customer expectations, driving substantial CLV value lift.")
        elif offer_type == "discount":
            open_prob = 0.65
            click_prob = 0.40
            conv_prob = 0.35
            complaint_prob = 0.02
            clv_delta = +120.0
            reason_parts.append("Generic discount provides modest conversion but dilutes premium brand perception.")

    # CASE C: Prospect / New Explorer
    elif is_prospect:
        reason_parts.append(f"Entity [{entity_id}] is a 'New Explorer' Prospect.")
        if offer_type in ["onboarding", "discount"] or tone == "informational":
            open_prob = 0.65
            click_prob = 0.50
            conv_prob = 0.40
            complaint_prob = 0.02
            clv_delta = +200.0  # Conversion value
            rfm_es_delta = +0.20
            reason_parts.append("Onboarding & welcome trial offer effectively lowers first-purchase barriers for new prospects.")
        elif offer_type == "vip_perk":
            open_prob = 0.35
            click_prob = 0.15
            conv_prob = 0.05
            reason_parts.append("Premature VIP wording produces low conversion among un-converted prospects.")

    # CASE D: Dormant Client / Sleeping Client
    elif is_dormant:
        reason_parts.append(f"Entity [{entity_id}] is a 'Sleeping Client' (Low RFM score: {rfm_score:.2f}).")
        if offer_type in ["reactivation", "discount"]:
            open_prob = 0.45
            click_prob = 0.30
            conv_prob = 0.25
            complaint_prob = 0.03
            churn_delta = -0.12
            clv_delta = +150.0
            reason_parts.append("Reactivation offer successfully stimulates dormant account interest.")

    # DEFAULT ACTIVE CLIENT
    else:
        reason_parts.append(f"Entity [{entity_id}] is a 'Regular Buyer' Active Client.")
        if offer_type == "discount":
            open_prob = 0.60
            click_prob = 0.45
            conv_prob = 0.35
            clv_delta = +100.0
            reason_parts.append("Standard commercial discount drives routine repeat order placement.")

    # 4. Incentive Magnitude Adjustment
    if incentive > 0:
        click_prob = min(0.95, click_prob + (incentive * 0.005))
        conv_prob = min(0.90, conv_prob + (incentive * 0.008))

    # Clamp probabilities to [0.0, 1.0]
    open_prob = max(0.05, min(0.98, open_prob))
    click_prob = max(0.02, min(0.95, click_prob))
    conv_prob = max(0.01, min(0.90, conv_prob))
    complaint_prob = max(0.00, min(0.90, complaint_prob))

    # 5. Composite Response Score Calculation (0.0 to 100.0)
    # Formula: 0.25*click + 0.25*conv + 0.20*churn_reduction + 0.15*satisfaction + 0.15*clv_lift - risk_penalty
    churn_reduction_score = max(0.0, min(1.0, -churn_delta / 0.25))  # 0.25 reduction -> 1.0
    satisfaction_score = max(0.0, min(1.0, satisfaction_delta / 0.25))
    clv_lift_score = max(0.0, min(1.0, clv_delta / 350.0))
    risk_penalty = (complaint_prob * 40.0) + (15.0 if (churn_delta > 0) else 0.0)

    raw_score = (
        (0.25 * click_prob * 100.0) +
        (0.25 * conv_prob * 100.0) +
        (0.20 * churn_reduction_score * 100.0) +
        (0.15 * satisfaction_score * 100.0) +
        (0.15 * clv_lift_score * 100.0) -
        risk_penalty
    )

    response_score = max(0.0, min(100.0, raw_score))

    # 6. Simulated Response Type Outcome Selection
    if complaint_prob >= 0.35:
        simulated_response_type = "Complained"
    elif conv_prob >= 0.45:
        simulated_response_type = "Converted"
    elif click_prob >= 0.35:
        simulated_response_type = "Clicked"
    elif open_prob >= 0.30:
        simulated_response_type = "Opened"
    else:
        simulated_response_type = "Ignored"

    simulation_reason = " ".join(reason_parts)

    return SimulatedResponse(
        variant_label=variant.variant_label,
        predicted_open_probability=round(open_prob, 4),
        predicted_click_probability=round(click_prob, 4),
        predicted_conversion_probability=round(conv_prob, 4),
        predicted_complaint_probability=round(complaint_prob, 4),
        predicted_churn_delta=round(churn_delta, 4),
        predicted_clv_delta=round(clv_delta, 2),
        predicted_rfm_es_delta=round(rfm_es_delta, 4),
        predicted_satisfaction_delta=round(satisfaction_delta, 4),
        simulated_response_type=simulated_response_type,
        simulation_reason=simulation_reason,
        response_score=round(response_score, 2),
    )

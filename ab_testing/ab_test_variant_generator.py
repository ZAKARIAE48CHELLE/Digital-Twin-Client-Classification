"""
OSMOS A/B Test Variant Generator (Phase 8.8)
============================================
Generates A/B testing campaign variants using local LLMs or rule-based fallbacks.

Governance & Safety Rules:
- Button-triggered only. Zero calls on page load or inside data fetch.
- No direct database writes by LLM.
- Proposes variant ideas only; does NOT dispatch campaigns.
- No PII, no unrealistic promises, no aggressive manipulation.
- Adheres to persona & CLV value constraints.
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from llm.llm_client import generate_text, check_llm_available
from llm.json_utils import extract_and_parse_json
from ab_testing.ab_test_schemas import ABVariant

logger = logging.getLogger("OSMOS_AB_VARIANT_GEN")


def _build_fallback_variants(
    admin_question: str,
    objective: str,
    entity_id: str,
    segment: str,
    persona: str,
    channel: str = "email"
) -> List[ABVariant]:
    """Generates clean, rule-based fallback variants when local LLM is offline or unconfigured."""
    obj_lower = objective.lower()
    pers_lower = persona.lower() if persona else ""
    seg_lower = segment.lower() if segment else ""

    if "frustrated" in pers_lower or "complaint" in seg_lower or obj_lower in ["complaint_recovery", "retention"]:
        var_a = ABVariant(
            variant_label="A",
            variant_title="Empathetic Service Recovery & Priority Support",
            message_text=f"Dear Valued Customer, we sincerely apologize for any inconvenience experienced. Our dedicated support team is at your disposal with priority handling.",
            offer_type="service_recovery",
            incentive_value=0.0,
            channel=channel,
            tone="empathetic",
            call_to_action="Contact Dedicated Support",
            expected_behavior="Increases satisfaction and reduces churn risk without cost inefficiency."
        )
        var_b = ABVariant(
            variant_label="B",
            variant_title="Courtesy Goodwill Credit Offer",
            message_text=f"Dear Valued Customer, we appreciate your patience. Please enjoy a courtesy goodwill credit on your next order as a token of our commitment.",
            offer_type="discount",
            incentive_value=15.0,
            channel=channel,
            tone="commercial",
            call_to_action="Claim Goodwill Credit",
            expected_behavior="Encourages immediate purchase re-engagement."
        )
    elif "loyal" in pers_lower or "vip" in pers_lower or "premium" in seg_lower or obj_lower == "upsell":
        var_a = ABVariant(
            variant_label="A",
            variant_title="VIP Exclusive Concierge Invitation",
            message_text=f"As a valued VIP Loyalist, we invite you to explore exclusive private preview access to our premium tier collections.",
            offer_type="vip_perk",
            incentive_value=0.0,
            channel=channel,
            tone="exclusive",
            call_to_action="Explore VIP Collection",
            expected_behavior="Reinforces VIP brand affinity and high customer lifetime value."
        )
        var_b = ABVariant(
            variant_label="B",
            variant_title="Exclusive Loyalty Member Reward",
            message_text=f"Thank you for your loyalty. Enjoy an exclusive 10% member reward on your next order.",
            offer_type="discount",
            incentive_value=10.0,
            channel=channel,
            tone="commercial",
            call_to_action="Use Member Reward",
            expected_behavior="Drives incremental basket size increase."
        )
    elif "prospect" in seg_lower or "explorer" in pers_lower or obj_lower == "conversion":
        var_a = ABVariant(
            variant_label="A",
            variant_title="Educational Product Guide & Welcome Overview",
            message_text=f"Welcome to OSMOS! Discover how our solution helps streamline your workflow with our interactive introduction guide.",
            offer_type="onboarding",
            incentive_value=0.0,
            channel=channel,
            tone="informational",
            call_to_action="Read Guide",
            expected_behavior="Increases product familiarity and click engagement."
        )
        var_b = ABVariant(
            variant_label="B",
            variant_title="Welcome First-Order Trial Discount",
            message_text=f"Welcome! Take 15% off your very first order to experience the quality of our service.",
            offer_type="discount",
            incentive_value=15.0,
            channel=channel,
            tone="commercial",
            call_to_action="Claim 15% Discount",
            expected_behavior="Accelerates prospect-to-client initial purchase conversion."
        )
    else:  # Reactivation or General Engagement
        var_a = ABVariant(
            variant_label="A",
            variant_title="Low-Cost Re-engagement Check-In",
            message_text=f"We noticed it has been a while since your last visit. Explore our newest feature updates tailored for you.",
            offer_type="reactivation",
            incentive_value=0.0,
            channel=channel,
            tone="informational",
            call_to_action="View What's New",
            expected_behavior="Cost-efficient re-engagement without margin dilution."
        )
        var_b = ABVariant(
            variant_label="B",
            variant_title="Welcome Back Re-activation Incentive",
            message_text=f"We miss you! Here is a 10% welcome back discount on your next visit.",
            offer_type="discount",
            incentive_value=10.0,
            channel=channel,
            tone="commercial",
            call_to_action="Shop Now",
            expected_behavior="Stimulates dormant account activity."
        )

    return [var_a, var_b]


def generate_llm_ab_variants(
    admin_question: str,
    objective: str,
    entity_profile: Dict[str, Any],
    channel: str = "email",
    num_variants: int = 2
) -> Tuple[List[ABVariant], str, bool]:
    """
    Button-triggered LLM generator producing structured A/B campaign variants.
    Returns (variants_list, experiment_name, is_llm_generated).
    """
    entity_id = entity_profile.get("entity_id", "P_DEMO_001")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    persona = entity_profile.get("customer_persona", "Regular Buyer")
    churn_risk = float(entity_profile.get("churn_risk_score", 0.30))
    clv_amount = float(entity_profile.get("predicted_clv_amount_mad", 500.0))
    rfm_score = float(entity_profile.get("rfm_score", 0.50))
    dynamic_class = entity_profile.get("dynamic_class", "Active Client")

    # Check LLM availability
    avail, _ = check_llm_available()
    if not avail:
        logger.info("Local LLM offline or unconfigured. Using deterministic fallback variant generator.")
        variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
        exp_name = f"A/B Test ({objective.title()}): {entity_id}"
        return (variants[:num_variants], exp_name, False)

    prompt = f"""
SYSTEM GOVERNANCE INSTRUCTIONS:
You are an expert CRM Marketing Scientist for the OSMOS platform.
Your task is to generate {num_variants} distinct marketing campaign/action variants ('A', 'B') to answer the administrator's business question.

ADMINISTRATOR CONTEXT:
- Business Question: "{admin_question}"
- Objective: "{objective}"
- Target Channel: "{channel}"

CUSTOMER DIGITAL TWIN PROFILE:
- Entity ID: {entity_id}
- Dynamic Cohort Class: {dynamic_class}
- Customer Segment: {segment}
- Resolved Stable Persona: {persona}
- Churn Risk Score: {churn_risk:.2f}
- Predicted CLV Amount (MAD): {clv_amount:.2f}
- RFM-ES Score: {rfm_score:.2f}

STRATEGIC RULES:
1. If Persona is 'Frustrated Client' or Segment is 'Complaint-Driven Risk Clients', generate at least ONE empathetic 'service_recovery' variant (0 incentive).
2. If Persona is 'Premium Loyalist' or 'Silent VIP at Risk', allow 'vip_perk' or exclusive concierge offers.
3. If Churn Risk is High (>= 0.60), do NOT generate aggressive upsell-only variants.
4. Discounts must NOT exceed 25%. Low CLV customers must not receive expensive incentives (>15).
5. Output ONLY a raw valid JSON object. No Markdown code block delimiters, no conversational text.

REQUIRED STABLE JSON STRUCTURE:
{{
  "experiment_name": "A/B Experiment Title",
  "objective": "{objective}",
  "variants": [
    {{
      "variant_label": "A",
      "variant_title": "Descriptive Title A",
      "message_text": "Engaging customer communication message A...",
      "offer_type": "discount | service_recovery | vip_perk | onboarding | reactivation | none",
      "incentive_value": 15,
      "channel": "{channel}",
      "tone": "commercial | empathetic | informational | exclusive",
      "call_to_action": "Clear action button text A",
      "expected_behavior": "Predicted customer psychological reaction A"
    }},
    {{
      "variant_label": "B",
      "variant_title": "Descriptive Title B",
      "message_text": "Engaging customer communication message B...",
      "offer_type": "service_recovery | discount | vip_perk | onboarding | reactivation | none",
      "incentive_value": 0,
      "channel": "{channel}",
      "tone": "empathetic | commercial | informational | exclusive",
      "call_to_action": "Clear action button text B",
      "expected_behavior": "Predicted customer psychological reaction B"
    }}
  ]
}}
"""

    try:
        raw_output = generate_text(prompt)
        parsed = extract_and_parse_json(raw_output)

        if not parsed or "variants" not in parsed or not isinstance(parsed["variants"], list):
            logger.warning("Failed to parse valid JSON from LLM output. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            return (variants[:num_variants], f"A/B Test ({objective.title()}): {entity_id}", False)

        exp_name = parsed.get("experiment_name", f"A/B Test ({objective.title()}): {entity_id}")
        raw_vars = parsed["variants"]

        variants = []
        labels = ["A", "B", "C"]
        for idx, rvar in enumerate(raw_vars[:num_variants]):
            lbl = rvar.get("variant_label", labels[idx if idx < len(labels) else 0])
            var_obj = ABVariant(
                variant_label=lbl,
                variant_title=rvar.get("variant_title", f"Variant {lbl}"),
                message_text=rvar.get("message_text", "No message provided."),
                offer_type=rvar.get("offer_type", "none"),
                incentive_value=float(rvar.get("incentive_value", 0.0)),
                channel=rvar.get("channel", channel),
                tone=rvar.get("tone", "commercial"),
                call_to_action=rvar.get("call_to_action", "Click Here"),
                expected_behavior=rvar.get("expected_behavior", "Customer engagement")
            )
            variants.append(var_obj)

        if len(variants) < 2:
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)

        return (variants, exp_name, True)
    except Exception as e:
        logger.error(f"Error during LLM variant generation: {e}")
        variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
        return (variants[:num_variants], f"A/B Test ({objective.title()}): {entity_id}", False)

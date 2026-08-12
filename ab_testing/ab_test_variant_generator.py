"""
OSMOS A/B Test Variant Generator & LLM Scientist Integration (Phase 8.8)
===========================================================================
Generates candidate A/B testing campaign variants using local LLM inference or
deterministic domain rule fallbacks. Strictly enforces prompt boundaries,
schema validation, and human-in-the-loop governance.
"""

import logging
from typing import Dict, Any, List, Tuple
from ab_testing.ab_test_schemas import ABVariant
import ab_testing.ab_test_validator as ab_val
from llm.llm_client import generate_text, check_llm_available
from llm.json_utils import repair_and_parse_json, is_json_truncated

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
        var_c = ABVariant(
            variant_label="C",
            variant_title="Dedicated Specialist Review Check-In",
            message_text=f"Dear Valued Customer, an account specialist has been assigned to review your recent service history and ensure full resolution.",
            offer_type="reactivation",
            incentive_value=0.0,
            channel=channel,
            tone="informational",
            call_to_action="Schedule Specialist Call",
            expected_behavior="Provides direct human assurance and long-term trust restoration."
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
        var_c = ABVariant(
            variant_label="C",
            variant_title="Private Masterclass & Early Access Pass",
            message_text=f"Exclusive for VIP Members: Reserve your private early-access pass for upcoming product drops.",
            offer_type="vip_perk",
            incentive_value=0.0,
            channel=channel,
            tone="exclusive",
            call_to_action="Reserve Pass",
            expected_behavior="Elevates brand prestige and loyalty retention."
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
        var_c = ABVariant(
            variant_label="C",
            variant_title="Interactive Product Demo & Consultation",
            message_text=f"Welcome! Request a 1-on-1 walkthrough with a product specialist tailored for your team.",
            offer_type="onboarding",
            incentive_value=0.0,
            channel=channel,
            tone="informational",
            call_to_action="Book Demo",
            expected_behavior="Drives deep engagement for high-intent prospects."
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
        var_c = ABVariant(
            variant_label="C",
            variant_title="Account Summary & Feature Highlights",
            message_text=f"See what you missed! Check your personalized account summary and recommendations.",
            offer_type="reactivation",
            incentive_value=0.0,
            channel=channel,
            tone="informational",
            call_to_action="See Summary",
            expected_behavior="Re-establishes brand presence with zero cost."
        )

    return [var_a, var_b, var_c]


def generate_llm_ab_variants(
    admin_question: str,
    objective: str,
    entity_profile: Dict[str, Any],
    channel: str = "email",
    num_variants: int = 2
) -> Tuple[List[ABVariant], str, str]:
    """
    Button-triggered LLM generator producing structured A/B campaign variants.
    Returns (variants_list, experiment_name, status_code) where status_code is 'llm_success', 'timeout', or 'invalid_json'.
    """
    entity_id = entity_profile.get("entity_id", "P_DEMO_001")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    persona = entity_profile.get("customer_persona", "Regular Buyer")
    churn_risk = float(entity_profile.get("churn_risk_score", 0.30))
    clv_amount = float(entity_profile.get("predicted_clv_amount_mad", 500.0))

    # Check LLM availability
    avail, _ = check_llm_available()
    if not avail:
        logger.info("Local LLM offline or unconfigured. Using deterministic fallback variant generator.")
        variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
        exp_name = f"A/B Test ({objective.title()}): {entity_id}"
        return (variants[:num_variants], exp_name, "timeout")

    prompt = f"""Generate exactly {num_variants} marketing campaign variants as raw JSON only. No markdown, no explanation.

Question: "{admin_question}"
Objective: "{objective}", Channel: "{channel}"
Customer: ID {entity_id}, Segment: {segment}, Persona: {persona}, ChurnRisk: {churn_risk:.2f}, CLV: {clv_amount:.0f} MAD

JSON Output Format:
{{
  "experiment_name": "Short Title (max 80 chars)",
  "objective": "{objective}",
  "variants": [
    {{
      "variant_label": "A",
      "variant_title": "Title (max 80 chars)",
      "message_text": "Short message text (max 280 chars)",
      "offer_type": "discount | service_recovery | vip_perk | onboarding | reactivation | none",
      "incentive_value": 0,
      "channel": "{channel}",
      "tone": "commercial | empathetic | informational | exclusive",
      "call_to_action": "CTA text (max 60 chars)",
      "expected_behavior": "Reaction description (max 100 chars)"
    }}
  ]
}}
"""

    try:
        raw_output = generate_text(prompt, max_tokens=700)
        if raw_output == "__TIMEOUT__":
            logger.info("Local LLM request timed out. Using deterministic fallback variant generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            return (variants[:num_variants], f"A/B Test ({objective.title()}): {entity_id}", "timeout")

        if is_json_truncated(raw_output):
            logger.warning("LLM output is truncated or incomplete. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            return (variants[:num_variants], f"A/B Test ({objective.title()}): {entity_id}", "invalid_json")

        parsed = repair_and_parse_json(raw_output)

        if not parsed or "variants" not in parsed or not isinstance(parsed["variants"], list) or len(parsed["variants"]) == 0:
            logger.warning("Failed to parse valid JSON from LLM output. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            return (variants[:num_variants], f"A/B Test ({objective.title()}): {entity_id}", "invalid_json")

        exp_name = parsed.get("experiment_name", f"A/B Test ({objective.title()}): {entity_id}")
        raw_vars = parsed["variants"]

        variants = []
        labels = ["A", "B", "C"]
        for idx, rvar in enumerate(raw_vars[:num_variants]):
            lbl = rvar.get("variant_label", labels[idx if idx < len(labels) else 0])
            v_title = str(rvar.get("variant_title", "")).strip()[:80]
            v_msg = str(rvar.get("message_text", "")).strip()[:280]
            v_cta = str(rvar.get("call_to_action", "Click Here")).strip()[:60]
            v_offer = str(rvar.get("offer_type", "none")).strip().lower()
            if v_offer not in ab_val.ALLOWED_OFFER_TYPES:
                v_offer = "none"
            v_tone = str(rvar.get("tone", "commercial")).strip().lower()
            if v_tone not in ["commercial", "empathetic", "informational", "exclusive"]:
                v_tone = "commercial"

            if not v_title or not v_msg:
                logger.warning("LLM variant item missing required fields. Using fallback generator.")
                variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
                return (variants[:num_variants], f"A/B Test ({objective.title()}): {entity_id}", "invalid_json")

            var_obj = ABVariant(
                variant_label=lbl,
                variant_title=v_title,
                message_text=v_msg,
                offer_type=v_offer,
                incentive_value=float(rvar.get("incentive_value", 0.0)),
                channel=rvar.get("channel", channel),
                tone=v_tone,
                call_to_action=v_cta,
                expected_behavior=str(rvar.get("expected_behavior", "Customer engagement")).strip()[:100]
            )
            variants.append(var_obj)

        if len(variants) < num_variants:
            fb_vars = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            for idx in range(len(variants), num_variants):
                if idx < len(fb_vars):
                    variants.append(fb_vars[idx])

        return (variants[:num_variants], exp_name, "llm_success")
    except Exception as e:
        logger.error(f"Error during LLM variant generation: {e}")
        variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
        return (variants[:num_variants], f"A/B Test ({objective.title()}): {entity_id}", "invalid_json")

"""
OSMOS A/B Test Variant Generator & LLM Scientist Integration (Phase 8.8)
===========================================================================
Generates candidate A/B testing campaign variants using local LLM inference or
deterministic domain rule fallbacks. Uses blueprint-guided LLM synthesis to enforce
predetermined variant counts, offer types, and channels, seamlessly merging
LLM copy with fallback blueprints.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from ab_testing.ab_test_schemas import ABVariant
import ab_testing.ab_test_validator as ab_val
from llm.llm_client import generate_text, check_llm_available
from llm.json_utils import repair_and_parse_json, extract_and_parse_json_array, is_json_truncated

logger = logging.getLogger("OSMOS_AB_VARIANT_GEN")

CANDIDATE_LLM_LOG_PATH = os.path.join(os.path.dirname(__file__), "candidate_llm_output.log")


def _log_candidate_llm_output(
    admin_question: str,
    objective: str,
    entity_id: str,
    status_code: str,
    raw_output: str,
    extracted_variants: List[ABVariant] = None,
    failure_reason: str = None
) -> None:
    """
    Appends candidate LLM outputs to 'candidate_llm_output.log' inside the ab_testing directory.
    Includes timestamp, entity ID, question, status code, raw LLM text, and parsed variant summaries.
    """
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = [
            f"=" * 80,
            f"TIMESTAMP       : {timestamp}",
            f"ENTITY ID       : {entity_id}",
            f"OBJECTIVE       : {objective}",
            f"QUESTION        : {admin_question}",
            f"STATUS CODE     : {status_code}",
        ]
        if failure_reason:
            entry.append(f"REASON          : {failure_reason}")
        entry.extend([
            f"-" * 80,
            f"RAW LLM OUTPUT  :\n{raw_output}",
            f"-" * 80
        ])
        if extracted_variants:
            entry.append("EXTRACTED CANDIDATE VARIANTS:")
            for v in extracted_variants:
                entry.append(
                    f"  [{v.variant_label}] Title: {v.variant_title} | Offer: {v.offer_type} | Incentive: {v.incentive_value} | Tone: {v.tone} | CTA: {v.call_to_action}\n"
                    f"      Message: {v.message_text}"
                )
        entry.append(f"=" * 80 + "\n\n")

        log_text = "\n".join(entry)
        with open(CANDIDATE_LLM_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_text)
    except Exception as e:
        logger.error(f"Failed to write to candidate_llm_output.log: {e}")


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


def build_variant_blueprints(
    objective: str,
    admin_question: str,
    entity_profile: Dict[str, Any],
    number_of_variants: int = 2,
    channel: str = "email"
) -> List[ABVariant]:
    """
    Creates deterministic variant skeletons (blueprints) with predetermined labels ('A', 'B', 'C'),
    offer types, incentive values, channels, and default copy.
    """
    entity_id = entity_profile.get("entity_id", "P_DEMO_001")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    persona = entity_profile.get("customer_persona", "Regular Buyer")

    fallback_base = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
    
    blueprints = []
    labels = ["A", "B", "C"]
    
    for idx in range(min(number_of_variants, 3)):
        lbl = labels[idx]
        if idx < len(fallback_base):
            base_var = fallback_base[idx]
            bp = ABVariant(
                variant_label=lbl,
                variant_title=base_var.variant_title,
                message_text=base_var.message_text,
                offer_type=base_var.offer_type,
                incentive_value=base_var.incentive_value,
                channel=channel,
                tone=base_var.tone,
                call_to_action=base_var.call_to_action,
                expected_behavior=base_var.expected_behavior
            )
        else:
            bp = ABVariant(
                variant_label=lbl,
                variant_title=f"Variant {lbl} Recommendation",
                message_text=f"Explore our targeted offer tailored for your account.",
                offer_type="discount" if idx == 1 else "reactivation",
                incentive_value=10.0 if idx == 1 else 0.0,
                channel=channel,
                tone="commercial" if idx == 1 else "informational",
                call_to_action="Learn More",
                expected_behavior="Drives customer re-engagement."
            )
        blueprints.append(bp)
        
    return blueprints


def _validate_semantic_rules(
    variants: List[ABVariant],
    objective: str,
    entity_profile: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Validates candidate variants against semantic domain governance rules:
    - Rule 1 (CLV Guardrail): If CLV <= 0, block 'high CLV', 'top CLV', 'valuable CLV', 'high value client'.
    - Rule 2 (Frustrated/Complaint): For Complaint-Driven Risk Clients or Frustrated Client, prefer service_recovery (at least one).
    - Rule 3 (Safety/Scary Wording): Block scary wording ('account suspended', 'account blocked', 'terminated', 'legal action', 'permanently deleted').
    - Rule 4 (VIP Guardrail): Block VIP wording ('vip loyali', 'exclusive vip perk', 'vip concierge') if persona is not Premium Loyalist or segment is not Silent VIP at Risk / Premium.
    - Rule 5 (Retention Objective): For retention objective, require at least one service_recovery variant.
    """
    clv_amount = float(entity_profile.get("predicted_clv_amount_mad", 0.0))
    segment = str(entity_profile.get("customer_segment", "")).lower()
    persona = str(entity_profile.get("customer_persona", "")).lower()
    obj_lower = objective.lower()

    # Rule 3: Scary Wording check
    scary_words = ["account suspended", "account blocked", "terminated", "legal action", "permanently deleted", "account closed"]
    for v in variants:
        combined_text = f"{v.variant_title} {v.message_text} {v.call_to_action}".lower()
        for w in scary_words:
            if w in combined_text:
                return (False, f"Scary wording detected: '{w}'")

    # Rule 1: CLV Guardrail
    if clv_amount <= 0:
        clv_words = ["high clv", "top clv", "valuable clv", "high value client", "high value customer"]
        for v in variants:
            combined_text = f"{v.variant_title} {v.message_text}".lower()
            for w in clv_words:
                if w in combined_text:
                    return (False, f"Blocked high-CLV wording for zero/negative CLV: '{w}'")

    # Rule 2: Frustrated / Complaint-Driven Risk Client
    if "frustrated" in persona or "complaint" in segment:
        has_service_rec = any(v.offer_type == "service_recovery" for v in variants)
        if not has_service_rec:
            return (False, "Frustrated/Complaint profile requires at least one service_recovery variant")

    # Rule 4: VIP Wording Guardrail
    is_vip_profile = "vip" in persona or "loyalist" in persona or "vip" in segment or "premium" in segment
    if not is_vip_profile:
        vip_words = ["vip loyali", "exclusive vip perk", "vip concierge", "vip tier", "vip member"]
        for v in variants:
            combined_text = f"{v.variant_title} {v.message_text}".lower()
            for w in vip_words:
                if w in combined_text:
                    return (False, f"VIP wording used for non-VIP customer: '{w}'")

    # Rule 5: Retention Objective
    if obj_lower == "retention":
        has_service_rec = any(v.offer_type == "service_recovery" for v in variants)
        if not has_service_rec:
            return (False, "Retention objective requires at least one service_recovery variant")

    return (True, "OK")


def generate_llm_ab_variants(
    admin_question: str,
    objective: str,
    entity_profile: Dict[str, Any],
    channel: str = "email",
    num_variants: int = 2
) -> Tuple[List[ABVariant], str, str]:
    """
    Button-triggered LLM generator producing structured A/B campaign variants based on blueprints.
    Fills LLM generated titles, messages, tones, and CTAs into deterministic skeletons.
    If LLM returns fewer variants, merges LLM text into available blueprints and fills missing variants
    with deterministic fallback copy.
    """
    entity_id = entity_profile.get("entity_id", "P_DEMO_001")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    persona = entity_profile.get("customer_persona", "Regular Buyer")
    churn_risk = float(entity_profile.get("churn_risk_score", 0.30))
    clv_amount = float(entity_profile.get("predicted_clv_amount_mad", 500.0))

    default_exp_name = f"A/B Test ({objective.title()}): {entity_id}"
    blueprints = build_variant_blueprints(objective, admin_question, entity_profile, number_of_variants=num_variants, channel=channel)

    # Check LLM availability once
    avail, _ = check_llm_available()
    if not avail:
        logger.info("Local LLM offline or unconfigured. Immediately using deterministic blueprint variants.")
        _log_candidate_llm_output(admin_question, objective, entity_id, "fallback_used", "LLM Offline / Unconfigured")
        return (blueprints, default_exp_name, "timeout")

    bp_summary = []
    for bp in blueprints:
        bp_summary.append(f"- Variant {bp.variant_label}: offer_type='{bp.offer_type}', incentive_value={bp.incentive_value}")
    bp_text = "\n".join(bp_summary)

    prompt = f"""You are an expert CRM Marketing Scientist. Refine copy for these pre-configured A/B campaign blueprints.

Question: "{admin_question}"
Objective: "{objective}", Channel: "{channel}"
Target Customer: ID {entity_id}, Segment: {segment}, Persona: {persona}, ChurnRisk: {churn_risk:.2f}, CLV: {clv_amount:.0f} MAD

Blueprints to Refine:
{bp_text}

Return ONLY a raw JSON object with a "variants" array containing copy for each blueprint label ("A", "B", ...).
Do NOT change variant_label. Do NOT invent new offer_types.

Required JSON Output Format:
{{
  "variants": [
    {{
      "variant_label": "A",
      "variant_title": "Short Title (max 60 chars)",
      "message_text": "Customer message (max 180 chars)",
      "tone": "empathetic | commercial | informational | exclusive",
      "call_to_action": "CTA text (max 40 chars)"
    }}
  ]
}}
"""

    num_predict = 750 if num_variants >= 3 else 500

    try:
        raw_output = generate_text(prompt, temperature=0.1, max_tokens=num_predict)

        if raw_output == "__TIMEOUT__":
            logger.info("Local LLM request timed out. Using deterministic blueprint variants.")
            _log_candidate_llm_output(admin_question, objective, entity_id, "timeout", "__TIMEOUT__")
            return (blueprints, default_exp_name, "timeout")

        if not raw_output or not raw_output.strip():
            logger.warning("LLM returned empty output. Using deterministic blueprint variants.")
            _log_candidate_llm_output(admin_question, objective, entity_id, "empty_llm_output", "<empty>", failure_reason="LLM returned empty output")
            return (blueprints, default_exp_name, "empty_llm_output")

        # Parse JSON Payload
        parsed_payload = repair_and_parse_json(raw_output)

        raw_array = []
        if isinstance(parsed_payload, dict) and "variants" in parsed_payload and isinstance(parsed_payload["variants"], list):
            raw_array = parsed_payload["variants"]
        elif isinstance(parsed_payload, list):
            raw_array = parsed_payload
        else:
            raw_array = extract_and_parse_json_array(raw_output)

        if not raw_array or not isinstance(raw_array, list):
            logger.warning("LLM output is invalid JSON. Using deterministic blueprint variants.")
            _log_candidate_llm_output(admin_question, objective, entity_id, "invalid_json", raw_output, failure_reason="Unparseable JSON")
            return (blueprints, default_exp_name, "invalid_json")

        # Map LLM variants by label or index
        llm_by_label = {}
        labels = ["A", "B", "C"]
        for idx, rvar in enumerate(raw_array):
            if isinstance(rvar, dict):
                lbl = str(rvar.get("variant_label", "")).strip().upper()
                if lbl in labels:
                    llm_by_label[lbl] = rvar
                elif idx < len(labels):
                    llm_by_label[labels[idx]] = rvar

        final_variants = []
        llm_success_count = 0

        for bp in blueprints:
            rvar = llm_by_label.get(bp.variant_label)
            if rvar and isinstance(rvar, dict):
                v_title = str(rvar.get("variant_title", "")).strip()[:60]
                v_msg = str(rvar.get("message_text", "")).strip()[:180]
                v_cta = str(rvar.get("call_to_action", bp.call_to_action)).strip()[:40]
                v_tone = str(rvar.get("tone", bp.tone)).strip().lower()
                if v_tone not in ["commercial", "empathetic", "informational", "exclusive"]:
                    v_tone = bp.tone

                if v_title and v_msg:
                    merged_var = ABVariant(
                        variant_label=bp.variant_label,
                        variant_title=v_title,
                        message_text=v_msg,
                        offer_type=bp.offer_type,
                        incentive_value=bp.incentive_value,
                        channel=bp.channel,
                        tone=v_tone,
                        call_to_action=v_cta,
                        expected_behavior=bp.expected_behavior
                    )
                    final_variants.append(merged_var)
                    llm_success_count += 1
                else:
                    final_variants.append(bp)
            else:
                final_variants.append(bp)

        # Semantic Validation on final merged variants
        is_valid_semantic, semantic_reason = _validate_semantic_rules(final_variants, objective, entity_profile)
        if not is_valid_semantic:
            logger.warning(f"LLM merged variants failed semantic validation: {semantic_reason}. Using deterministic blueprints.")
            _log_candidate_llm_output(admin_question, objective, entity_id, "semantic_validation_failed", raw_output, extracted_variants=final_variants, failure_reason=semantic_reason)
            return (blueprints, default_exp_name, "semantic_validation_failed")

        exp_name = f"A/B ({objective.title()}): {final_variants[0].variant_title[:30]} vs {final_variants[1].variant_title[:30]}" if len(final_variants) >= 2 else default_exp_name

        if llm_success_count == num_variants:
            status_code = "llm_success_valid"
        elif llm_success_count > 0:
            status_code = f"llm_partial_merged:{llm_success_count}/{num_variants}"
        else:
            status_code = "fallback_used"

        _log_candidate_llm_output(admin_question, objective, entity_id, status_code, raw_output, extracted_variants=final_variants)
        return (final_variants, exp_name, status_code)

    except Exception as e:
        logger.error(f"Error during LLM variant generation: {e}")
        _log_candidate_llm_output(admin_question, objective, entity_id, "invalid_json", str(e), failure_reason=str(e))
        return (blueprints, default_exp_name, "invalid_json")

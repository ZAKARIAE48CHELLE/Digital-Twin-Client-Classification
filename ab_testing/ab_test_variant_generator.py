"""
OSMOS A/B Test Variant Generator & LLM Scientist Integration (Phase 8.8)
===========================================================================
Generates candidate A/B testing campaign variants using local LLM inference or
deterministic domain rule fallbacks. Strictly enforces prompt boundaries,
schema validation, character max limits, semantic governance rules, and
records candidate LLM outputs to 'candidate_llm_output.log' in ab_testing/.
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
    Button-triggered LLM generator producing structured A/B campaign variants as a JSON object containing a "variants" list.
    Returns (variants_list, experiment_name, status_code) where status_code is 'llm_success_valid', 'partial_json',
    'invalid_json', 'empty_variants', 'incomplete_variant_count', 'semantic_validation_failed', or 'timeout'.
    Logs candidate LLM output to 'ab_testing/candidate_llm_output.log'.
    """
    entity_id = entity_profile.get("entity_id", "P_DEMO_001")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    persona = entity_profile.get("customer_persona", "Regular Buyer")
    churn_risk = float(entity_profile.get("churn_risk_score", 0.30))
    clv_amount = float(entity_profile.get("predicted_clv_amount_mad", 500.0))

    default_exp_name = f"A/B Test ({objective.title()}): {entity_id}"

    # Check LLM availability
    avail, _ = check_llm_available()
    if not avail:
        logger.info("Local LLM offline or unconfigured. Using deterministic fallback variant generator.")
        variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
        _log_candidate_llm_output(admin_question, objective, entity_id, "fallback_used", "LLM Offline / Unconfigured")
        return (variants[:num_variants], default_exp_name, "timeout")

    # Prompt requesting a JSON object with a "variants" array
    prompt = f"""Return ONLY a raw JSON object containing a "variants" array of exactly {num_variants} variant objects. No markdown ```json, no extra text.

Question: "{admin_question}"
Objective: "{objective}", Channel: "{channel}"
Customer: ID {entity_id}, Segment: {segment}, Persona: {persona}, ChurnRisk: {churn_risk:.2f}, CLV: {clv_amount:.0f} MAD

Required Output Schema:
{{
  "variants": [
    {{
      "variant_label": "A",
      "variant_title": "Short Title (max 60 chars)",
      "message_text": "Customer message (max 180 chars)",
      "offer_type": "service_recovery | discount | vip_perk | onboarding | reactivation | none",
      "incentive_value": 0,
      "channel": "{channel}",
      "tone": "empathetic | commercial | informational | exclusive",
      "call_to_action": "CTA text (max 40 chars)"
    }}
  ]
}}
"""

    num_predict = 750 if num_variants >= 3 else 500

    try:
        raw_output = generate_text(prompt, temperature=0.1, max_tokens=num_predict)

        # 0. Check for Timeout
        if raw_output == "__TIMEOUT__":
            logger.info("Local LLM request timed out. Using deterministic fallback variant generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            _log_candidate_llm_output(admin_question, objective, entity_id, "timeout", "__TIMEOUT__")
            return (variants[:num_variants], default_exp_name, "timeout")

        # 1. Check for Empty Output
        if not raw_output or not raw_output.strip():
            logger.warning("LLM returned empty output. Using deterministic fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            _log_candidate_llm_output(admin_question, objective, entity_id, "empty_llm_output", "<empty>", failure_reason="LLM returned empty output")
            return (variants[:num_variants], default_exp_name, "empty_llm_output")

        # 2. Check for Truncated JSON
        if is_json_truncated(raw_output):
            logger.warning("LLM output is truncated or incomplete. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            _log_candidate_llm_output(admin_question, objective, entity_id, "partial_json", raw_output, failure_reason="Output truncated or unclosed brackets/quotes")
            return (variants[:num_variants], default_exp_name, "partial_json")

        # 3. Parse JSON Payload
        parsed_payload = repair_and_parse_json(raw_output)

        raw_array = []
        is_empty_variants_list = False

        if isinstance(parsed_payload, dict):
            if "variants" in parsed_payload:
                if isinstance(parsed_payload["variants"], list):
                    raw_array = parsed_payload["variants"]
                    if len(raw_array) == 0:
                        is_empty_variants_list = True
        elif isinstance(parsed_payload, list):
            raw_array = parsed_payload
            if len(raw_array) == 0:
                is_empty_variants_list = True

        if not raw_array and not is_empty_variants_list:
            raw_array = extract_and_parse_json_array(raw_output)

        # Debug Mode Logging
        debug_mode = os.getenv("OSMOS_AB_DEBUG_LLM", "").lower() in ["true", "1"]
        if debug_mode:
            logger.info(f"[DEBUG_LLM] Raw Output: {raw_output[:300]}")
            logger.info(f"[DEBUG_LLM] Parsed Payload Type: {type(parsed_payload).__name__}")
            if isinstance(parsed_payload, dict):
                logger.info(f"[DEBUG_LLM] Payload Keys Found: {list(parsed_payload.keys())}")
            logger.info(f"[DEBUG_LLM] Variants Extracted Count: {len(raw_array)}")

        # 4. Check for Empty Variants List
        if is_empty_variants_list:
            logger.warning("LLM output contains empty variants list. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            _log_candidate_llm_output(admin_question, objective, entity_id, "empty_variants", raw_output, failure_reason="Variants array was empty")
            return (variants[:num_variants], default_exp_name, "empty_variants")

        # 5. Check for Invalid / Unparseable JSON
        if not raw_array or not isinstance(raw_array, list) or len(raw_array) == 0:
            logger.warning("LLM output is invalid JSON or non-JSON text. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            _log_candidate_llm_output(admin_question, objective, entity_id, "invalid_json", raw_output, failure_reason="Invalid JSON or non-JSON text")
            return (variants[:num_variants], default_exp_name, "invalid_json")

        # 6. Check for Incomplete Variant Count
        if len(raw_array) < num_variants:
            logger.warning(f"LLM output returned {len(raw_array)} variants, but {num_variants} requested. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            _log_candidate_llm_output(admin_question, objective, entity_id, "incomplete_variant_count", raw_output, failure_reason=f"Returned {len(raw_array)} < requested {num_variants}")
            return (variants[:num_variants], default_exp_name, "incomplete_variant_count")

        # 5. Extract and Strict Required Field Check
        candidate_variants = []
        labels = ["A", "B", "C"]
        required_fields = ["variant_label", "variant_title", "message_text", "offer_type", "channel", "tone", "call_to_action"]

        for idx, rvar in enumerate(raw_array[:num_variants]):
            if not isinstance(rvar, dict):
                logger.warning("LLM variant item is not a dict. Using fallback generator.")
                variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
                _log_candidate_llm_output(admin_question, objective, entity_id, "invalid_json", raw_output, failure_reason="Variant item not dict")
                return (variants[:num_variants], default_exp_name, "invalid_json")

            missing = [f for f in required_fields if not str(rvar.get(f, "")).strip()]
            if missing:
                logger.warning(f"LLM variant item missing required fields: {missing}. Using fallback generator.")
                variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
                _log_candidate_llm_output(admin_question, objective, entity_id, "partial_json", raw_output, failure_reason=f"Missing required fields: {missing}")
                return (variants[:num_variants], default_exp_name, "partial_json")

            lbl = str(rvar.get("variant_label", labels[idx if idx < len(labels) else 0])).strip()
            v_title = str(rvar.get("variant_title", "")).strip()[:60]
            v_msg = str(rvar.get("message_text", "")).strip()[:180]
            v_cta = str(rvar.get("call_to_action", "Click Here")).strip()[:40]
            
            v_offer = str(rvar.get("offer_type", "none")).strip().lower()
            if v_offer not in ab_val.ALLOWED_OFFER_TYPES:
                v_offer = "none"
            v_tone = str(rvar.get("tone", "commercial")).strip().lower()
            if v_tone not in ["commercial", "empathetic", "informational", "exclusive"]:
                v_tone = "commercial"

            try:
                v_inc = float(rvar.get("incentive_value", 0.0))
            except (ValueError, TypeError):
                v_inc = 0.0

            var_obj = ABVariant(
                variant_label=lbl,
                variant_title=v_title,
                message_text=v_msg,
                offer_type=v_offer,
                incentive_value=v_inc,
                channel=rvar.get("channel", channel),
                tone=v_tone,
                call_to_action=v_cta,
                expected_behavior=str(rvar.get("expected_behavior", "Customer behavioral engagement")).strip()[:100]
            )
            candidate_variants.append(var_obj)

        # 6. Semantic Validation Check
        is_valid_semantic, semantic_reason = _validate_semantic_rules(candidate_variants, objective, entity_profile)
        if not is_valid_semantic:
            logger.warning(f"LLM variants failed semantic validation: {semantic_reason}. Using fallback generator.")
            variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
            _log_candidate_llm_output(admin_question, objective, entity_id, "semantic_validation_failed", raw_output, extracted_variants=candidate_variants, failure_reason=semantic_reason)
            return (variants[:num_variants], default_exp_name, "semantic_validation_failed")

        exp_name = f"A/B ({objective.title()}): {candidate_variants[0].variant_title[:30]} vs {candidate_variants[1].variant_title[:30]}" if len(candidate_variants) >= 2 else default_exp_name
        
        # Log successful candidate LLM output
        _log_candidate_llm_output(admin_question, objective, entity_id, "llm_success_valid", raw_output, extracted_variants=candidate_variants)

        return (candidate_variants[:num_variants], exp_name, "llm_success_valid")
    except Exception as e:
        logger.error(f"Error during LLM variant generation: {e}")
        variants = _build_fallback_variants(admin_question, objective, entity_id, segment, persona, channel)
        _log_candidate_llm_output(admin_question, objective, entity_id, "invalid_json", str(e), failure_reason=str(e))
        return (variants[:num_variants], default_exp_name, "invalid_json")

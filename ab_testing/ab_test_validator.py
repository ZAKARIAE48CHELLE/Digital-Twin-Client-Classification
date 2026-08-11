"""
OSMOS A/B Variant Validator (Phase 8.8)
=======================================
Deterministic rule validator evaluating A/B campaign variants against business,
persona, CLV, churn, and governance constraints.

Zero Database Write Guarantee:
This module performs in-memory validation only and never alters customer records or database tables.
"""

import re
import logging
from typing import Dict, Any, List
from ab_testing.ab_test_schemas import ABVariant

logger = logging.getLogger("OSMOS_AB_VALIDATOR")

ALLOWED_CHANNELS = ["email", "sms", "phone", "web_notification", "simulated_only"]
ALLOWED_OFFER_TYPES = ["discount", "service_recovery", "vip_perk", "onboarding", "reactivation", "none"]

PII_TERMS = ["ssn", "credit_card", "password", "bank_account", "secret", "private_key"]
FORBIDDEN_DISPATCH_TERMS = ["sent successfully to inbox", "email delivered to customer", "real sms dispatched"]


def validate_ab_variants(
    variants: List[ABVariant],
    entity_profile: Dict[str, Any],
    objective: str = "retention"
) -> Dict[str, Any]:
    """
    Evaluates a set of candidate A/B variants against deterministic business rules.
    Returns dict with {"is_valid": bool, "errors": list, "warnings": list, "normalized_variants": list}.
    """
    errors: List[str] = []
    warnings: List[str] = []
    normalized_variants: List[ABVariant] = []

    entity_type = entity_profile.get("entity_type", "Client")
    dynamic_class = entity_profile.get("dynamic_class", "Active Client")
    segment = entity_profile.get("customer_segment", "Standard Active Clients")
    persona = entity_profile.get("customer_persona", "Regular Buyer")
    churn_risk = float(entity_profile.get("churn_risk_score", 0.30))
    clv_amount = float(entity_profile.get("predicted_clv_amount_mad", 500.0))
    clv_segment = entity_profile.get("predicted_clv_segment", "Medium Value")

    is_frustrated = ("frustrated" in persona.lower() or "complaint" in segment.lower())
    is_churn_critical = (churn_risk >= 0.65 or dynamic_class == "Churn Risk Client")
    is_low_clv = (clv_segment == "Low Value" or clv_amount <= 300.0)
    is_prospect = (entity_type == "Prospect")

    labels_seen = set()

    # Rule 1: Label Uniqueness & Minimum Variants
    if len(variants) < 2:
        errors.append("A/B experiment requires at least 2 distinct variants ('A' and 'B').")

    has_service_recovery_variant = False

    for idx, var in enumerate(variants):
        var_warnings = []
        lbl = var.variant_label.upper() if var.variant_label else f"VAR_{idx}"

        # Duplicate label check
        if lbl in labels_seen:
            errors.append(f"Duplicate variant label detected: '{lbl}'. Variant labels must be unique.")
        labels_seen.add(lbl)

        # Message text check
        if not var.message_text or len(var.message_text.strip()) == 0:
            errors.append(f"Variant '{lbl}': Message text cannot be empty.")

        # Channel check
        if var.channel.lower() not in ALLOWED_CHANNELS:
            errors.append(f"Variant '{lbl}': Channel '{var.channel}' is not allowed. Must be one of {ALLOWED_CHANNELS}.")

        # Offer type check
        if var.offer_type.lower() not in ALLOWED_OFFER_TYPES:
            errors.append(f"Variant '{lbl}': Offer type '{var.offer_type}' is not allowed. Must be one of {ALLOWED_OFFER_TYPES}.")

        # Incentive value numeric check
        try:
            val = float(var.incentive_value)
            if val < 0:
                errors.append(f"Variant '{lbl}': Incentive value cannot be negative ({val}).")
        except (ValueError, TypeError):
            errors.append(f"Variant '{lbl}': Incentive value must be numeric.")
            val = 0.0

        # Rule 6: Discount ceiling check (Max 30%)
        if var.offer_type.lower() == "discount" and val > 30.0:
            errors.append(f"Variant '{lbl}': Discount incentive ({val}%) exceeds maximum allowed limit of 30%.")

        # Rule 7: Low CLV cost inefficiency check
        if is_low_clv and val > 15.0:
            var_warnings.append(f"Low CLV customer ({clv_amount:.0f} MAD): Incentive value ({val}) may cause cost inefficiency.")
            if val > 25.0:
                errors.append(f"Variant '{lbl}': High incentive ({val}) is blocked for Low CLV customers to prevent margin loss.")

        # Rule 8: Service recovery check for frustrated clients
        if var.offer_type.lower() == "service_recovery" or var.tone.lower() == "empathetic":
            has_service_recovery_variant = True

        # Rule 9: Churn critical upsell-only check
        if is_churn_critical and objective.lower() == "upsell" and var.offer_type.lower() == "vip_perk":
            errors.append(f"Variant '{lbl}': Upsell-only VIP offer is blocked for Churn Critical customers. Prioritize retention or service recovery.")

        # Rule 10: Prospect VIP wording check
        if is_prospect and ("vip" in var.variant_title.lower() or "loyalty" in var.message_text.lower()):
            var_warnings.append(f"Variant '{lbl}': Prospect entity received VIP/Loyalty wording prior to initial conversion.")

        # Rule 11: Client onboarding wording check
        if not is_prospect and var.offer_type.lower() == "onboarding" and objective.lower() != "reactivation":
            var_warnings.append(f"Variant '{lbl}': Existing Client received prospect onboarding offer type.")

        # Rule 12: PII terms check
        msg_lower = var.message_text.lower()
        for pii in PII_TERMS:
            if pii in msg_lower:
                errors.append(f"Variant '{lbl}': Contains forbidden sensitive PII term '{pii}'.")

        # Rule 13: Real dispatch terms check
        for forbidden in FORBIDDEN_DISPATCH_TERMS:
            if forbidden in msg_lower:
                errors.append(f"Variant '{lbl}': Contains forbidden real dispatch term '{forbidden}'. OSMOS uses simulated dispatches only.")

        # Attach warnings to variant
        var.validation_warnings = var_warnings
        if var_warnings:
            var.validation_status = "Warning"
            warnings.extend([f"Variant '{lbl}': {w}" for w in var_warnings])
        else:
            var.validation_status = "Valid"

        normalized_variants.append(var)

    # Rule 8 Check: Frustrated Client service recovery option mandate
    if is_frustrated and not has_service_recovery_variant:
        warnings.append("Customer is mapped to 'Frustrated Client' / 'Complaint-Driven Risk'. Including an empathetic service recovery variant is strongly recommended.")

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "normalized_variants": normalized_variants,
    }

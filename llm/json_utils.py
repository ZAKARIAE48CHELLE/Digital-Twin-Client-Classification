import re
import json
import logging

logger = logging.getLogger("OSMOS_LLM_JSON_UTILS")

def is_json_truncated(raw_text: str) -> bool:
    """Detects if raw text appears to be truncated JSON."""
    if not raw_text:
        return True
    s = raw_text.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE).rstrip("`").strip()
    if not s.startswith("{") and not s.startswith("["):
        return True
    if not (s.endswith("}") or s.endswith("]")):
        return True
    # Count quotes
    quotes = len(re.findall(r'(?<!\\)"', s))
    if quotes % 2 != 0:
        return True
    return False


def repair_and_parse_json(text: str) -> dict:
    """
    Cleans markdown code fences, replaces NULL/None literals, removes trailing commas,
    extracts the first valid JSON object, and parses incomplete or truncated JSON.
    """
    if not text or text == "__TIMEOUT__":
        return {}

    s = text.strip()
    
    # Strip markdown code blocks
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    
    # Extract first { to end
    idx_brace = s.find("{")
    if idx_brace != -1:
        s = s[idx_brace:]
    else:
        return {}

    # Replace unquoted NULL, Null, None with null
    s = re.sub(r'(?<=[:,\s\[{])\b(NULL|Null|None)\b', 'null', s)

    # Remove trailing commas before } or ]
    s = re.sub(r',\s*([}\]])', r'\1', s)

    # Attempt 1: Standard parse
    try:
        return json.loads(s)
    except Exception:
        pass

    # Attempt 2: Auto-close quotes and balance braces/brackets
    try:
        cand = s
        quotes = len(re.findall(r'(?<!\\)"', cand))
        if quotes % 2 != 0:
            cand += '"'

        cand = re.sub(r',\s*$', '', cand.strip())
        cand = re.sub(r',\s*([}\]])', r'\1', cand)

        in_q = False
        esc = False
        open_braces = 0
        open_brackets = 0

        for ch in cand:
            if ch == '"' and not esc:
                in_q = not in_q
            elif not in_q:
                if ch == '{':
                    open_braces += 1
                elif ch == '}':
                    open_braces = max(0, open_braces - 1)
                elif ch == '[':
                    open_brackets += 1
                elif ch == ']':
                    open_brackets = max(0, open_brackets - 1)
            esc = (ch == '\\' and not esc)

        repaired = cand + (']' * open_brackets) + ('}' * open_braces)
        return json.loads(repaired)
    except Exception:
        pass

    # Attempt 3: Regex extraction of completed variant objects
    try:
        match_variants = re.findall(r'(\{\s*"variant_label"\s*:\s*"[^"]+".*?\})', s, re.DOTALL)
        if match_variants:
            parsed_variants = []
            for v_str in match_variants:
                try:
                    if not v_str.endswith("}"):
                        v_str += "}"
                    parsed_variants.append(json.loads(v_str))
                except Exception:
                    pass
            if parsed_variants:
                exp_match = re.search(r'"experiment_name"\s*:\s*"([^"]+)"', s)
                exp_name = exp_match.group(1) if exp_match else "A/B Experiment"
                obj_match = re.search(r'"objective"\s*:\s*"([^"]+)"', s)
                obj_name = obj_match.group(1) if obj_match else "retention"
                return {
                    "experiment_name": exp_name,
                    "objective": obj_name,
                    "variants": parsed_variants
                }
    except Exception:
        pass

    return {}


def extract_and_parse_json(text, expected_keys=None):
    """
    Extracts the JSON substring from a text block and parses it with robust auto-repair.
    If parsing fails completely, returns a fallback dict with expected_keys initialized.
    """
    if not text or text == "__TIMEOUT__":
        return create_fallback_dict(expected_keys)
        
    parsed = repair_and_parse_json(text)
    
    if parsed:
        if expected_keys:
            for k in expected_keys:
                if k not in parsed:
                    parsed[k] = None
        return parsed
        
    logger.warning(f"Failed to parse JSON output after repair attempt. Raw text: {text[:200]}")
    return create_fallback_dict(expected_keys)


def create_fallback_dict(expected_keys):
    """Creates a fallback dictionary to prevent UI rendering errors."""
    fallback = {
        "summary_fr": "Impossible de charger la recommandation LLM automatique. Analyse déterministe activée.",
        "summary_en": "Unable to load automatic LLM recommendation. Deterministic analysis active.",
        "risk_explanation_fr": "Changement de comportement détecté nécessitant une prise de contact.",
        "risk_explanation_en": "Behavioral change detected requiring direct account follow-up.",
        "priority": "Medium",
        "recommended_action_fr": "Contacter le client pour faire un suivi personnalisé et réévaluer ses besoins.",
        "recommended_action_en": "Follow up directly with customer to review account status and needs.",

        "suggested_channel": "Email / Direct Call",
        "message_draft_fr": "Bonjour, nous aimerions faire le point avec vous sur votre compte et vos besoins actuels.",
        "message_draft_en": "Hello, we would like to follow up on your account and discuss your current needs.",
        "admin_guidance_fr": "Planifier un appel de courtoisie ou envoyer un email de fidélisation.",
        "admin_guidance_en": "Schedule a courtesy call or send a targeted retention email.",
        "confidence": "Low"
    }

    if expected_keys:
        for k in expected_keys:
            if k not in fallback:
                fallback[k] = None
    return fallback

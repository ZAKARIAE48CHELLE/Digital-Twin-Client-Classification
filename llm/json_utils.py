import re
import json
import logging

logger = logging.getLogger("OSMOS_LLM_JSON_UTILS")

def extract_and_parse_json(text, expected_keys=None):
    """
    Extracts the JSON substring from a text block and parses it.
    Cleans markdown code blocks if present.
    If parsing fails, returns a fallback dict with expected_keys initialized.
    """
    if not text:
        return create_fallback_dict(expected_keys)
        
    # Remove whitespace
    cleaned = text.strip()
    
    # Check for markdown code fence blocks
    if "```" in cleaned:
        # Match anything between ```json and ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        else:
            # Try to match the first { to the last }
            match_braces = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match_braces:
                cleaned = match_braces.group(1).strip()
                
    # Direct search for braces if no match was found
    if not (cleaned.startswith("{") and cleaned.endswith("}")):
        match_braces = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match_braces:
            cleaned = match_braces.group(1).strip()
            
    try:
        parsed = json.loads(cleaned)
        # Ensure all expected keys exist
        if expected_keys:
            for k in expected_keys:
                if k not in parsed:
                    parsed[k] = None
        return parsed
    except Exception as e:
        logger.warning(f"Failed to parse JSON output: {e}. Raw text: {text[:200]}")
        return create_fallback_dict(expected_keys)

def create_fallback_dict(expected_keys):
    """Creates a fallback dictionary to prevent UI rendering errors."""
    fallback = {
        "summary_fr": "Impossible de charger la recommandation.",
        "summary_en": "Unable to load the recommendation.",
        "risk_explanation_fr": "Le serveur local d'assistant LLM est indisponible ou a renvoyé un format incorrect.",
        "risk_explanation_en": "The local LLM assistant server is offline or returned an invalid format.",
        "priority": "Medium",
        "recommended_action_fr": "Veuillez vérifier la configuration Ollama.",
        "recommended_action_en": "Please check the Ollama configuration.",
        "suggested_channel": "Manual Review",
        "message_draft_fr": "Bonjour, nous aimerions faire le point sur votre dossier.",
        "message_draft_en": "Hello, we would like to follow up on your account.",
        "admin_guidance_fr": "Veuillez réanalyser l'historique client manuellement.",
        "admin_guidance_en": "Please re-analyze customer history manually.",
        "confidence": "Low"
    }
    if expected_keys:
        for k in expected_keys:
            if k not in fallback:
                fallback[k] = None
    return fallback

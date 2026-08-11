import time
import requests
import json
import logging
from database.db import get_cursor
from llm.llm_config import (
    is_llm_enabled,
    get_llm_provider,
    get_llm_model,
    get_llm_base_url,
    get_llm_timeout
)
from llm.json_utils import extract_and_parse_json

logger = logging.getLogger("OSMOS_LLM_CLIENT")

# Cached availability variables
_last_check_time = 0.0
_cached_availability = False
_cached_availability_reason = ""

def write_llm_audit_log(action_type, details_dict):
    """Write an entry to the system audit_logs database table."""
    try:
        from database.db import get_cursor
        query = """
            INSERT INTO audit_logs (action_type, details)
            VALUES (%(action_type)s, %(details)s);
        """
        import psycopg2.extras
        with get_cursor() as cur:
            cur.execute(query, {
                "action_type": action_type,
                "details": psycopg2.extras.Json(details_dict)
            })
    except Exception as e:
        logger.error(f"Failed to write LLM audit log: {e}")

def check_llm_available():
    """
    Checks if Ollama or the LLM service is running and the model is loaded.
    Caches availability check for 60 seconds.
    """
    global _last_check_time, _cached_availability, _cached_availability_reason
    
    if not is_llm_enabled():
        return False, "LLM Assistant is disabled in configuration."
        
    now = time.time()
    if now - _last_check_time < 60.0:
        return _cached_availability, _cached_availability_reason
        
    _last_check_time = now
    provider = get_llm_provider()
    base_url = get_llm_base_url()
    model = get_llm_model()
    timeout = min(5, get_llm_timeout()) # short timeout for availability check
    
    if provider == "ollama":
        try:
            # Check Ollama root endpoint
            resp = requests.get(f"{base_url}/", timeout=timeout)
            if resp.status_code != 200:
                _cached_availability = False
                _cached_availability_reason = f"Ollama returned HTTP {resp.status_code}."
                return _cached_availability, _cached_availability_reason
                
            # Verify if target model is loaded/pulled
            tags_resp = requests.get(f"{base_url}/api/tags", timeout=timeout)
            if tags_resp.status_code == 200:
                tags = tags_resp.json()
                models = [m.get("name") for m in tags.get("models", [])]
                # Match full or tagless model names
                if model in models or f"{model}:latest" in models or any(m.startswith(model) for m in models):
                    _cached_availability = True
                    _cached_availability_reason = f"Ollama connected. Model '{model}' loaded."
                else:
                    _cached_availability = False
                    _cached_availability_reason = f"Model '{model}' not found in Ollama registry."
            else:
                _cached_availability = False
                _cached_availability_reason = "Ollama active, but failed listing local tags."
        except requests.exceptions.RequestException as e:
            _cached_availability = False
            _cached_availability_reason = f"Ollama server offline at {base_url}."
    else:
        # Placeholder for other future providers
        _cached_availability = False
        _cached_availability_reason = f"LLM provider '{provider}' is not implemented yet."
        
    return _cached_availability, _cached_availability_reason

def generate_text(prompt, temperature=0.2, max_tokens=768):
    """Generate raw text response from local LLM with bounded token generation."""
    available, reason = check_llm_available()
    if not available:
        logger.warning(f"LLM generate requested but service is unavailable: {reason}")
        return ""
        
    provider = get_llm_provider()
    base_url = get_llm_base_url()
    model = get_llm_model()
    timeout = get_llm_timeout()
    
    if provider == "ollama":
        url = f"{base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
            else:
                err_msg = f"Ollama HTTP error {resp.status_code}: {resp.text}"
                logger.error(err_msg)
                write_llm_audit_log("LLM_HTTP_ERROR", {"status_code": resp.status_code, "error": resp.text})
                return ""
        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama request timed out: {e}")
            write_llm_audit_log("LLM_TIMEOUT", {"error": str(e)})
            try:
                import streamlit as st
                st.warning("The local LLM did not respond in time. The deterministic alert remains valid. Please retry or check Ollama.")
            except Exception:
                pass
            return "__TIMEOUT__"
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connection error during generation: {e}")
            write_llm_audit_log("LLM_CONNECTION_FAILED", {"error": str(e)})
            return ""
    return ""

def generate_json(prompt, temperature=0.1, expected_keys=None):
    """Generate structured JSON response from local LLM."""
    raw_text = generate_text(prompt, temperature=temperature)
    if raw_text == "__TIMEOUT__":
        return {
            "summary_fr": "Le modèle local n'a pas répondu dans le délai prévu.",
            "summary_en": "The local model did not respond within the expected timeout.",
            "risk_explanation_fr": "L'analyse déterministe reste disponible, mais l'explication LLM n'a pas pu être générée.",
            "risk_explanation_en": "The deterministic analysis is still available, but the LLM explanation could not be generated.",
            "priority": "Manual Review",
            "recommended_action_fr": "Réessayer la génération ou vérifier que le modèle Ollama est bien chargé.",
            "recommended_action_en": "Retry generation or verify that the Ollama model is properly loaded.",
            "suggested_channel": "Manual Review",
            "message_draft_fr": "",
            "message_draft_en": "",
            "admin_guidance_fr": "Vérifier Ollama, le modèle utilisé et le délai d'attente configuré.",
            "admin_guidance_en": "Check Ollama, the selected model, and the configured timeout.",
            "confidence": "Low"
        }
    return extract_and_parse_json(raw_text, expected_keys)


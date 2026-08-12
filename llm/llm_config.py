import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
try:
    load_dotenv()
except Exception:
    pass

def is_llm_enabled():
    """Check if the LLM assistant layer is enabled."""
    val = os.getenv("OSMOS_LLM_ENABLED", "false").lower()
    return val == "true" or val == "1"

def get_llm_provider():
    """Get LLM service provider. Defaults to 'ollama'."""
    return os.getenv("OSMOS_LLM_PROVIDER", "ollama").lower()

def get_llm_model():
    """Get the specific model name. Defaults to 'auramarket-chat:latest'."""
    val = os.getenv("OSMOS_LLM_MODEL")
    if val:
        return val
    return "auramarket-chat:latest"

def get_llm_base_url():
    """Get base URL of Ollama or LLM service."""
    return os.getenv("OSMOS_LLM_BASE_URL", "http://localhost:11434")

def get_llm_language():
    """Get LLM output language preference. Defaults to 'fr_en'."""
    return os.getenv("OSMOS_LLM_LANGUAGE", "fr_en")

def get_llm_timeout(default_val: int = 90) -> int:
    """Get timeout in seconds for LLM request. Reads OSMOS_LLM_TIMEOUT from env, defaulting to default_val (90s)."""
    env_str = os.getenv("OSMOS_LLM_TIMEOUT")
    if env_str:
        try:
            return min(120, max(5, int(env_str)))
        except ValueError:
            pass
    return default_val

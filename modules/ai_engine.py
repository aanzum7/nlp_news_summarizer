"""
InsightInMinutes - AI Inference & Multi-Model Cascade Core
Orchestrates Google Gemini inference with multi-model failover matching anzum.ai,
model quota cooldown tracking, automatic language detection, and strict structured response parsing.
"""

from __future__ import annotations
import logging
import time
import warnings
from typing import Tuple, Optional, Dict, List

# Silence automatic function calling warnings from google-genai
warnings.filterwarnings("ignore", message=".*automatic function calling.*")
logging.getLogger("google.genai").setLevel(logging.ERROR)
logging.getLogger("google.genai.models").setLevel(logging.ERROR)

import langdetect
from google import genai
from google.genai import types

from config import (
    DEFAULT_GEMINI_MODEL,
    GEMINI_FALLBACK_MODELS,
    MODEL_QUOTA_COOLDOWN_SECONDS,
)
from modules.metrics import estimate_tokens

# Global model quota cooldown registry: model_name -> expiration_timestamp
_exhausted_models: Dict[str, float] = {}


def get_active_model_pool() -> List[str]:
    """Builds prioritized candidate model pool matching anzum.ai failover strategy."""
    pool: List[str] = []
    if DEFAULT_GEMINI_MODEL:
        pool.append(DEFAULT_GEMINI_MODEL)
    for model_name in GEMINI_FALLBACK_MODELS:
        if model_name not in pool:
            pool.append(model_name)
    return pool


def execute_summary_cascade(
    content: str, api_key: str, min_limit: int, max_limit: int
) -> Tuple[Optional[str], Optional[str], Optional[str], int, int, Optional[str]]:
    """
    Executes an AI news summarization pass across the prioritized model cascade.
    Features automatic quota failover and cooldown tracking.

    Returns:
        (headline, summary_body, model_name, in_tokens, out_tokens, error_message)
    """
    try:
        detected_lang = langdetect.detect(content)
    except Exception:
        detected_lang = "en"

    client = genai.Client(api_key=api_key)

    prompt = (
        f"You are a master news editor. Summarize the following news content in the '{detected_lang}' language.\n"
        f"Strict Editorial Constraints:\n"
        f"- Length: strictly between {min_limit} and {max_limit} words.\n"
        f"- Line 1 must begin with 'HEADLINE: [punchy, professional news headline]'\n"
        f"- Line 2 onwards must begin with 'SUMMARY: [dense, high-signal news brief covering who, what, why, and key takeaways]'\n"
        f"- Maintain objective journalistic neutrality, preserve critical facts, dates, names, and statistical data.\n\n"
        f"Source Article:\n{content}"
    )

    model_pool = get_active_model_pool()
    now = time.time()
    collected_errors: List[str] = []

    for model_name in model_pool:
        # Check quota cooldown
        if model_name in _exhausted_models:
            if now < _exhausted_models[model_name]:
                continue
            del _exhausted_models[model_name]

        try:
            generate_config = types.GenerateContentConfig(
                temperature=0.3,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=generate_config,
            )

            if response and response.text:
                raw_text = response.text.strip()
                headline = "Flash News Intelligence"
                summary_body = raw_text

                if "HEADLINE:" in raw_text and "SUMMARY:" in raw_text:
                    parts = raw_text.split("SUMMARY:")
                    headline = parts[0].replace("HEADLINE:", "").strip()
                    summary_body = parts[1].strip()
                elif "\n" in raw_text:
                    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                    headline = lines[0].replace("HEADLINE:", "").strip()
                    summary_body = "\n\n".join(lines[1:]).replace("SUMMARY:", "").strip()

                in_tokens, out_tokens, _ = estimate_tokens(prompt, raw_text)
                return headline, summary_body, model_name, in_tokens, out_tokens, None

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                _exhausted_models[model_name] = now + MODEL_QUOTA_COOLDOWN_SECONDS
                collected_errors.append(f"{model_name}: 429 Quota cooldown initiated")
            else:
                collected_errors.append(f"{model_name}: {err_str[:60]}")
            continue

    friendly_err = "All model cascade nodes currently exhausted. " + " | ".join(collected_errors[:2])
    return None, None, None, 0, 0, friendly_err

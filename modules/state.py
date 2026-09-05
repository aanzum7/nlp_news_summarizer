"""
InsightInMinutes - State Management & Credentials
Encapsulates Streamlit session state initialization, credentials retrieval, and cache clearing.
"""

import os
from typing import Tuple, Optional
import streamlit as st


def init_session_state() -> None:
    """Initializes all necessary session state keys if not already present."""
    defaults = {
        "last_summary": None,
        "headline": None,
        "model_used": None,
        "reading_metrics": {
            "orig_words": 0,
            "summ_words": 0,
            "time_saved_sec": 0,
            "time_saved_display": "0s",
            "compression_pct": 0,
            "read_time_summary_sec": 0,
        },
        "token_metrics": {"input": 0, "output": 0, "total": 0},
        "cache_vault": {},
        "history_log": [],
        "target_url_input": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def read_api_key() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieves Google Gemini API key from .streamlit/secrets.toml
    with seamless fallback to environment variables (GEMINI_API_KEY or GOOGLE_API_KEY).
    """
    key = None
    try:
        if "genai" in st.secrets and "api_key" in st.secrets["genai"]:
            key = st.secrets["genai"]["api_key"]
    except Exception:
        pass

    # Check environment variable fallbacks
    if not key or key in ["YOUR_GEMINI_API_KEY_HERE", "your_api_key_here"]:
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not key or key in ["YOUR_GEMINI_API_KEY_HERE", "your_api_key_here"]:
        return None, (
            "Gemini API key is missing. Please configure it in `.streamlit/secrets.toml` "
            "under `[genai] api_key = \"...\"` or export the `GEMINI_API_KEY` environment variable."
        )

    return key.strip(), None


def clear_workspace() -> None:
    """Resets active summary state, token counters, and memory cache."""
    st.session_state.headline = None
    st.session_state.last_summary = None
    st.session_state.model_used = None
    st.session_state.reading_metrics = {
        "orig_words": 0,
        "summ_words": 0,
        "time_saved_sec": 0,
        "time_saved_display": "0s",
        "compression_pct": 0,
        "read_time_summary_sec": 0,
    }
    st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
    st.session_state.cache_vault = {}
    st.session_state.target_url_input = ""

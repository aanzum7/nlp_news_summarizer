"""
InsightInMinutes - Universal AI News Summarizer
Main Executable Application Orchestrator
"""

import streamlit as st

from config import get_custom_css
from modules.state import init_session_state, read_api_key
from modules.ui_components import (
    render_hero,
    render_sidebar,
    render_main_tabs,
)


def main():
    # 1. Page Configuration (Must be first Streamlit command)
    st.set_page_config(
        page_title="InsightInMinutes | 1-Minute AI News Reader",
        page_icon="🗞️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 2. State & Styling Setup
    init_session_state()
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # 3. Credentials & Sidebar HUD
    api_key, api_err = read_api_key()
    render_sidebar(api_err)

    # 4. Hero Header Banner
    render_hero()

    # 5. Guard: API Key Configuration Check
    if api_err:
        with st.container(border=True):
            st.error(f"⚠️ {api_err}")
            st.info(
                "👉 **How to configure your API key:**\n\n"
                "Add your Gemini API key into `.streamlit/secrets.toml`:\n"
                "```toml\n[genai]\napi_key = \"AIzaSy...\"\n```\n"
                "or set the `GEMINI_API_KEY` environment variable."
            )
        return

    # 6. Primary Interactive Views
    render_main_tabs(api_key)


if __name__ == "__main__":
    main()

import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import langdetect
from functools import lru_cache
import re

# ---------------------------
# ✅ Page Config (must be first Streamlit command!)
# ---------------------------
st.set_page_config(page_title="InsightInMinutes", page_icon="🔎", layout="wide")

# ---------------------------
# 🎨 THEME CONFIGURATION
# ---------------------------
THEME = {
    "background_color": "#f4db95",      # Creamy old-paper
    "text_color": "#0d0d0d",            # Dark text
    "header_color": "#111111",          # Darker headings
    "subheader_color": "#333333",       # Slightly lighter
    "button_color": "#444444",          # Charcoal
    "button_hover_color": "#222222",    # Almost black
    "card_border": "#c7b78b",           # Antique brown border
    "card_bg": "#fffdfa",               # Light creamy boxes
    "headline_color": "#000000",        # Headline black
    "summary_color": "#111111",         # Summary dark gray
    "section_padding": "18px",
    "font_family": "Georgia, serif"
}

# ---------------------------
# CSS STYLING
# ---------------------------
st.markdown(f"""
<style>
.stApp {{
    background-color: {THEME['background_color']};
    color: {THEME['text_color']};
    font-family: {THEME['font_family']};
}}

h1, h2, h3, h4, h5 {{
    text-align: center;
    color: {THEME['header_color']};
    margin-bottom: 12px;
}}
h3 {{
    color: {THEME['subheader_color']};
}}

.stButton>button {{
    background-color: {THEME['button_color']};
    color: white;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 500;
    width: 100%;
}}
.stButton>button:hover {{
    background-color: {THEME['button_hover_color']};
    color: white;
}}

.stTextArea textarea, .stTextInput>div>input {{
    background-color: {THEME['card_bg']} !important;
    border: 1px solid {THEME['card_border']} !important;
    border-radius: 6px !important;
    color: {THEME['text_color']} !important;
    caret-color: {THEME['text_color']} !important;
}}

[data-testid="stMarkdownContainer"] p {{
    color: {THEME['text_color']} !important;
    font-size: 15px;
    line-height: 1.6;
}}

.summary-section {{
    padding: {THEME['section_padding']};
    border: 1px solid {THEME['card_border']};
    background-color: {THEME['card_bg']};
    border-radius: 10px;
    margin-top: 15px;
    margin-bottom: 15px;
    text-align: center;
    color: {THEME['text_color']};
    box-shadow: 1px 1px 6px rgba(0,0,0,0.1);
}}

.sidebar-tabs {{
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 10px;
}}
.sidebar-tab {{
    padding: 8px 12px;
    background-color: {THEME['card_bg']};
    border: 1px solid {THEME['card_border']};
    border-radius: 6px;
    color: {THEME['text_color']};
    font-weight: 500;
    cursor: pointer;
    text-align: center;
    flex: 1;
}}
.sidebar-tab.active {{
    background-color: {THEME['button_color']};
    color: white;
}}
.sidebar-tab:hover {{
    background-color: {THEME['button_hover_color']};
    color: white;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# API Key Loader
# ---------------------------
def read_api_key():
    try:
        return st.secrets["genai"]["api_key"], None
    except KeyError:
        return None, "API key missing in `.streamlit/secrets.toml`."

# ---------------------------
# URL Extractor
# ---------------------------
def extract_content_from_url(url, target_classes):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = []
        for target_class in target_classes:
            paragraphs.extend(
                p.get_text(strip=True)
                for div in soup.find_all('div', class_=target_class)
                for p in div.find_all('p')
            )
        combined = "\n".join(paragraphs)
        if not combined or len(combined.split()) < 50:
            return None, "❌ Content too short or invalid."
        return combined, None
    except Exception as e:
        return None, f"Error: {e}"

# ---------------------------
# Summarizer
# ---------------------------
@lru_cache(maxsize=10)
def summarize_content(content, api_key, min_limit, max_limit):
    try:
        lang = langdetect.detect(content)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="Gemini-2.5-Flash-Lite",
            generation_config={"temperature": 0.4, "top_p": 0.9, "max_output_tokens": 1024},
        )
        chat = model.start_chat()
        prompt = (
            f"You are a journalist summarizing content in {lang}. "
            f"Generate a headline and a summary within {min_limit} to {max_limit} words, "
            "preserving the language and tone.\n\n"
            f"Content:\n{content}"
        )
        response = chat.send_message(prompt)
        if response and response.text:
            return response.text.strip(), None
        return None, "❌ No response generated."
    except Exception as e:
        return None, f"Error summarizing: {e}"

# ---------------------------
# Reset Output
# ---------------------------
def reset_output(page_type):
    if page_type == "url":
        st.session_state.pop("generated_url", None)
        st.session_state.pop("last_summary", None)
    elif page_type == "text":
        st.session_state.pop("generated_text", None)
        st.session_state.pop("last_summary", None)
    st.rerun()

# ---------------------------
# Detect Source
# ---------------------------
def detect_source_from_url(url):
    patterns = {
        "Daily Prothom Alo": r"prothomalo\.com",
        "The Daily Star": r"thedailystar\.net",
        "DW": r"dw\.com",
        "The Business Standard": r"tbsnews\.net",
        "Daily Manab Zamin": r"mzamin\.com",
    }
    for name, pattern in patterns.items():
        if re.search(pattern, url or ""):
            return name
    return "Other"

# ---------------------------
# Display Summary
# ---------------------------
def display_summary(summary_text):
    if summary_text:
        lines = summary_text.splitlines()
        st.markdown(
            f"<div class='summary-section'><h3 style='color:{THEME['headline_color']}'>📰 Headline</h3>"
            f"<p>{lines[0]}</p></div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='summary-section'><h3 style='color:{THEME['summary_color']}'>📄 Summary</h3>"
            f"<p>{' '.join(lines[1:])}</p></div>", unsafe_allow_html=True
        )

# ---------------------------
# URL Page
# ---------------------------
def url_page(api_key):
    st.title("🌐 URL Summarizer")
    url = st.text_input("Enter News URL:")

    if "last_url" not in st.session_state:
        st.session_state.last_url = ""
    if url != st.session_state.last_url:
        st.session_state.last_url = url
        st.session_state.generated_url = False
        st.session_state.last_summary = None

    detected_source = detect_source_from_url(url) if url else None
    target_classes_map = {
        "Daily Prothom Alo": ["story-element story-element-text"],
        "The Daily Star": ["pb-20 clearfix"],
        "DW": ["c17j8gzx rc0m0op r1ebneao s198y7xq rich-text li5mn0y r16w0xvi w1fzgn0z blt0baw"],
        "The Business Standard": ["section-content clearfix margin-bottom-2", "section-content margin-bottom-2"],
        "Daily Manab Zamin": ["col-sm-10 offset-sm-1 fs-5 lh-base mt-4 mb-5"],
    }

    if detected_source and detected_source != "Other":
        st.info(f"Detected Source: **{detected_source}**")
        target_classes = target_classes_map.get(detected_source, [])
        custom_class = ""
    else:
        st.info("Source not recognized. Provide CSS class for article content.")
        custom_class = st.text_input("Enter CSS Class for Article Content:")
        target_classes = [custom_class] if custom_class else []

    min_limit, max_limit = st.slider("Set Summary Length Range (words):", 50, 250, (70, 150))

    if "generated_url" not in st.session_state:
        st.session_state.generated_url = False

    if not st.session_state.generated_url:
        if st.button("🚀 Generate Summary", use_container_width=True):
            if url and target_classes and (detected_source != "Other" or custom_class):
                with st.spinner("Fetching and Summarizing..."):
                    content, error = extract_content_from_url(url, target_classes)
                    if error:
                        st.error(error)
                    elif content:
                        summary, error = summarize_content(content, api_key, min_limit, max_limit)
                        if error:
                            st.error(error)
                        else:
                            display_summary(summary)
                            st.session_state.generated_url = True
                            st.session_state.last_summary = summary
                            st.rerun()
                    else:
                        st.error("❌ Failed to extract content.")
            else:
                st.warning("Please enter URL and CSS Class.")
    else:
        display_summary(st.session_state.last_summary)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("♻️ Regenerate Summary", use_container_width=True):
                with st.spinner("Regenerating..."):
                    content, error = extract_content_from_url(url, target_classes)
                    if error:
                        st.error(error)
                    elif content:
                        summary, error = summarize_content(content, api_key, min_limit, max_limit)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.last_summary = summary
                            st.rerun()
        with col2:
            if st.button("🏠 Home", use_container_width=True):
                reset_output("url")

# ---------------------------
# Text Page
# ---------------------------
def text_page(api_key):
    st.title("📝 Text Summarizer")
    input_text = st.text_area("Paste Your Text Here:", height=250)
    min_limit, max_limit = st.slider("Set Summary Length Range (words):", 50, 250, (70, 150))

    if "generated_text" not in st.session_state:
        st.session_state.generated_text = False

    if not st.session_state.generated_text:
        if st.button("🚀 Generate Summary", use_container_width=True):
            if input_text.strip():
                with st.spinner("Generating..."):
                    summary, error = summarize_content(input_text.strip(), api_key, min_limit, max_limit)
                    if error:
                        st.error(error)
                    else:
                        display_summary(summary)
                        st.session_state.generated_text = True
                        st.session_state.last_summary = summary
                        st.rerun()
            else:
                st.warning("Please input some text.")
    else:
        display_summary(st.session_state.last_summary)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("♻️ Regenerate Summary", use_container_width=True):
                with st.spinner("Regenerating..."):
                    summary, error = summarize_content(input_text.strip(), api_key, min_limit, max_limit)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.last_summary = summary
                        st.rerun()
        with col2:
            if st.button("🏠 Home", use_container_width=True):
                reset_output("text")

# ---------------------------
# Main App
# ---------------------------
def main():
    # Sidebar Tabs & Info
    with st.sidebar:
        st.title("📰 InsightInMinutes")
        st.caption("⚡ AI-powered News Summarizer")
        st.markdown("""
            <div style='font-size: 14px; font-weight: normal;'>
            Summarize from <strong>URL</strong> or <strong>custom text</strong> using predefined or user-defined sources.  
            Built for <strong>speed, clarity, and insight</strong>.
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        if "selected_page" not in st.session_state:
            st.session_state.selected_page = "URL"
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌐 URL Summarizer", key="tab_url"):
                st.session_state.selected_page = "URL"
        with col2:
            if st.button("📝 Text Summarizer", key="tab_text"):
                st.session_state.selected_page = "TEXT"

        st.markdown("---")
        st.title("👨‍💻 About the Author")
        st.caption("Tanvir Anzum – AI & Data Researcher")
        st.markdown("""
            <div style='font-size: 14px; font-weight: normal;'>
            Passionate about turning <strong>data into insights</strong> and building <strong>AI-powered tools</strong> for real-world impact.
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style='font-size: 14px; font-weight: normal;'>
            <br>
            <a href="https://www.linkedin.com/in/aanzum" target="_blank">
                <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="16" style="vertical-align:middle; margin-right:6px;">
                <strong>LinkedIn</strong>
            </a>
            &nbsp;&nbsp;
            <a href="https://www.researchgate.net/profile/Tanvir-Anzum" target="_blank">
                <img src="https://upload.wikimedia.org/wikipedia/commons/5/5e/ResearchGate_icon_SVG.svg" alt="ResearchGate" width="16" style="vertical-align:middle; margin-right:6px;">
                <strong>Research</strong>
            </a>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    api_key, error_api = read_api_key()
    if error_api:
        st.error(error_api)
        return

    page = st.session_state.selected_page
    if page == "URL":
        url_page(api_key)
    else:
        text_page(api_key)

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    main()

import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import langdetect
import re

# ---------------------------
# ✅ Page Config (Must be First)
# ---------------------------
st.set_page_config(page_title="OneMinute News Reader | Pro News Dashboard", page_icon="⚡", layout="wide")

# Initialize Session States
if "last_summary" not in st.session_state:
    st.session_state.last_summary = None
if "headline" not in st.session_state:
    st.session_state.headline = None
if "model_used" not in st.session_state:
    st.session_state.model_used = None
if "token_metrics" not in st.session_state:
    st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
if "cache_vault" not in st.session_state:
    st.session_state.cache_vault = {}
if "preset_url" not in st.session_state:
    st.session_state.preset_url = ""

# ---------------------------
# 🎨 PREMIUM THEME CONFIGURATION
# ---------------------------
THEME = {
    "background_color": "#0F1115",       # Rich Slate Dark
    "card_bg": "#1A1D24",                # Charcoal Panel
    "card_border": "#2D3139",            # Modern Gray Trim
    "text_color": "#E1E4EA",             # Clean Off-White
    "accent_color": "#4F46E5",           # Electric Indigo
    "summary_accent": "#10B981",          # Emerald Green Accent
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
}

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {THEME['background_color']};
        font-family: {THEME['font_family']};
        color: {THEME['text_color']};
    }}
    
    .full-width-wrapper {{
        width: 100%;
        margin-bottom: 25px;
    }}
    
    /* 🎨 Premium Output Cards */
    .headline-card-premium {{
        background: {THEME['card_bg']};
        border: 1px solid {THEME['card_border']};
        border-left: 5px solid {THEME['accent_color']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 15px;
    }}
    
    .summary-card-premium {{
        background: {THEME['card_bg']};
        border: 1px solid {THEME['card_border']};
        border-left: 5px solid {THEME['summary_accent']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 15px;
    }}
    
    .badge-headline {{
        font-size: 11px;
        text-transform: uppercase;
        font-weight: 600;
        color: {THEME['accent_color']};
        letter-spacing: 0.05em;
        display: block;
        margin-bottom: 8px;
    }}
    
    .badge-summary {{
        font-size: 11px;
        text-transform: uppercase;
        font-weight: 600;
        color: {THEME['summary_accent']};
        letter-spacing: 0.05em;
        display: block;
        margin-bottom: 8px;
    }}
    
    .info-label {{
        font-size: 11px;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}
    
    h1, h2, h3, h4, h5 {{
        font-weight: 700;
        color: #FFFFFF;
    }}
    
    .stTextArea textarea, .stTextInput>div>input {{
        background-color: {THEME['card_bg']} !important;
        border: 1px solid {THEME['card_border']} !important;
        border-radius: 8px !important;
        color: {THEME['text_color']} !important;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: #111318 !important;
        border-right: 1px solid {THEME['card_border']};
    }}

    /* Contact Links Hover State */
    .social-btn-row a:hover {{
        opacity: 0.8;
    }}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# API Key Loader
# ---------------------------
def read_api_key():
    try:
        return st.secrets["genai"]["api_key"], None
    except Exception:
        return None, "API key missing in configuration files."

# ---------------------------
# Universal Intelligent Link Engine
# ---------------------------
def extract_universal_content(url, custom_class=None):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if custom_class:
            paragraphs = []
            for div in soup.find_all(class_=custom_class):
                paragraphs.extend([p.get_text(strip=True) for p in div.find_all('p')])
            if paragraphs:
                return "\n".join(paragraphs), None
                
        patterns = {
            "prothomalo\\.com": ["story-element-text"],
            "thedailystar\\.net": ["pb-20", "clearfix"],
            "dw\\.com": ["rich-text"],
            "tbsnews\\.net": ["section-content"],
            "mzamin\\.com": ["lh-base"]
        }
        for pattern, classes in patterns.items():
            if re.search(pattern, url):
                paragraphs = []
                for cls in classes:
                    for div in soup.find_all(class_=cls):
                        paragraphs.extend([p.get_text(strip=True) for p in div.find_all('p')])
                if paragraphs:
                    return "\n".join(paragraphs), None

        for element in soup(["nav", "footer", "header", "script", "style", "aside", "form"]):
            element.decompose()
            
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True).split()) > 8]
        combined = "\n".join(paragraphs)
        
        if len(combined.split()) < 40:
            combined = soup.get_text(separator="\n", strip=True)
            
        return combined, None
    except Exception as e:
        return None, f"Scraping Failure: {str(e)}"

# ---------------------------
# Resilient Cascade Fallback Inference Core
# ---------------------------
def execute_summary(content, api_key, min_limit, max_limit):
    try:
        detected_lang = langdetect.detect(content)
    except Exception:
        detected_lang = "en"
        
    client = genai.Client(api_key=api_key)
    
    prompt = (
        f"Summarize the following text in the {detected_lang} language. "
        f"Keep the response strictly short and dense between {min_limit} and {max_limit} words. "
        f"Format explicitly with 'HEADLINE:' on line 1, followed by 'SUMMARY:' on line 2.\n\n"
        f"Text:\n{content}"
    )

    model_cascade_pool = [
        {"name": "gemini-2.5-flash", "supports_thinking": False},
        {"name": "gemini-2.5-flash-lite", "supports_thinking": False},
        {"name": "gemini-2.0-flash", "supports_thinking": False}
    ]
    
    collected_errors = []
    
    for model_meta in model_cascade_pool:
        current_model = model_meta["name"]
        try:
            generate_config = types.GenerateContentConfig(
                tools=[types.Tool(googleSearch=types.GoogleSearch())]
            )
                
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=generate_config
            )
            
            if response and response.text:
                raw_text = response.text.strip()
                headline = "OneMinute Flash"
                summary_body = raw_text
                
                if "HEADLINE:" in raw_text and "SUMMARY:" in raw_text:
                    parts = raw_text.split("SUMMARY:")
                    headline = parts[0].replace("HEADLINE:", "").strip()
                    summary_body = parts[1].strip()
                elif "\n" in raw_text:
                    split_lines = [l for l in raw_text.splitlines() if l.strip()]
                    headline = split_lines[0]
                    summary_body = "\n".join(split_lines[1:])
                
                input_tokens = int(len(prompt.split()) * 1.3)
                output_tokens = int(len(raw_text.split()) * 1.3)
                
                st.session_state.token_metrics["input"] = input_tokens
                st.session_state.token_metrics["output"] = output_tokens
                st.session_state.token_metrics["total"] = input_tokens + output_tokens
                    
                return headline, summary_body, current_model, None
                
        except Exception as e:
            collected_errors.append(f"{current_model}: {str(e)}")
            continue
            
    combined_log = " | ".join(collected_errors)
    return None, None, None, f"Cascade Exhausted. Log: {combined_log}"

# ---------------------------
# UI Presentation Layer
# ---------------------------
def render_output_dashboard(model_used=None):
    if st.session_state.last_summary:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="headline-card-premium">
            <span class="badge-headline">OneMinute Flash Headline</span>
            <h2 style="text-align:left; margin:0; font-size:23px; color:#FFFFFF;">{st.session_state.headline}</h2>
        </div>
        <div class="summary-card-premium">
            <span class="badge-summary">Analytical Synthesis Summary</span>
            <p style="margin-top:4px; margin-bottom:0; line-height:1.7; font-size:14.5px; color:{THEME['text_color']};">{st.session_state.last_summary}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if model_used:
            st.caption(f"⚡ Engine Allocation Telemetry: Processed via free cluster `{model_used}` node.")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Main Shell Framework
# ---------------------------
def main():
    api_key, api_err = read_api_key()
    
    with st.sidebar:
        # Dynamic metrics values safely grabbed from session_state
        i_tok = st.session_state.token_metrics["input"]
        o_tok = st.session_state.token_metrics["output"]
        t_tok = st.session_state.token_metrics["total"]
        
        # 1. App Header Identity Block
        st.markdown(f"""
            <div style="background: {THEME['card_bg']}; border: 1px solid {THEME['card_border']}; border-radius: 12px; padding: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">⚡</span>
                    <h3 style='color:#FFFFFF; margin:0; font-weight:700; font-size: 15px; letter-spacing: -0.02em;'>InsightInMinutes- OneMinute News Reader</h3>
                </div>
                <div style='color:#4F46E5; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-top:6px;'>
                    Deep-Thinking Universal Core Engine
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. Reverted Token Metrics Module (Previous Boxed Metadata Layout)
        st.markdown(f"""
            <div style="background: {THEME['card_bg']}; border: 1px solid {THEME['card_border']}; border-radius: 12px; padding: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 16px;">
                <div class="info-label" style="margin-bottom: 12px;">📊 Current Token Allocation Metrics</div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 10px;">
                    <div style="background: #0F1115; padding: 10px; border-radius: 6px; border: 1px solid {THEME['card_border']};">
                        <div style="font-size: 10px; color: #9CA3AF; text-transform: uppercase; font-weight: 500;">Input Stream</div>
                        <div style="font-size: 16px; font-weight: 700; color: #FFFFFF;">{i_tok:,}</div>
                    </div>
                    <div style="background: #0F1115; padding: 10px; border-radius: 6px; border: 1px solid {THEME['card_border']};">
                        <div style="font-size: 10px; color: #9CA3AF; text-transform: uppercase; font-weight: 500;">Output Yield</div>
                        <div style="font-size: 16px; font-weight: 700; color: #FFFFFF;">{o_tok:,}</div>
                    </div>
                </div>
                <div style="background: #0F1115; padding: 10px; border-radius: 6px; border: 1px solid {THEME['card_border']}; display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 10px; color: #9CA3AF; text-transform: uppercase; font-weight: 500;">Billed Token Volume</div>
                    <div style="font-size: 16px; font-weight: 700; color: #FFFFFF;">{t_tok:,}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
            
            # Matching Author Profile Card
            st.markdown(f"""
                <div style="background: {CONFIG['card_bg']}; border: 1px solid {CONFIG['card_border']}; border-radius: 12px; padding: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    <div class="info-label" style="margin-bottom: 2px;">Project Architect</div>
                    <div style="font-size: 16px; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;">Tanvir Anzum</div>
                    <div style="font-size: 11px; font-weight: 600; color: {CONFIG['success_color']}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;">
                        🧬 AI & Data Researcher
                    </div>
                    <div style='font-size: 13px; color: #9CA3AF; line-height: 1.4; border-top: 1px solid {CONFIG['card_border']}; padding-top: 10px;'>
                        Passionate about turning <strong>data into insights</strong> and building <strong>AI-powered tools</strong> for real-world impact.
                    </div>
                    <div style='font-size: 13px; margin-top: 14px; display: flex; gap: 16px; border-top: 1px solid {CONFIG['card_border']}; padding-top: 12px;'>
                        <a href="https://www.linkedin.com/in/aanzum" target="_blank" style="text-decoration: none; color: #FFFFFF; display: flex; align-items: center; gap: 6px;">
                            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="14" style="vertical-align:middle;">
                            <strong>LinkedIn</strong>
                        </a>
                        <a href="https://www.researchgate.net/profile/Tanvir-Anzum" target="_blank" style="text-decoration: none; color: #FFFFFF; display: flex; align-items: center; gap: 6px;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/5/5e/ResearchGate_icon_SVG.svg" alt="ResearchGate" width="14" style="vertical-align:middle; filter: invert(1);">
                            <strong>Research</strong>
                        </a>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")

    if api_err:
        st.error(api_err)
        return

    # Workspace Section Layout (Streamlined URL Processor Pipeline)
    st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
    st.subheader("🌐 paste any online news link")
    
    # Quick URL Presets for instant user-end testing
    st.caption("✨ Quick Suggestion Templates (Click to test instantly):")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        if st.button("📰 Prothom Alo", use_container_width=True):
            st.session_state.preset_url = "https://www.prothomalo.com/bangladesh/district/dhaka"
    with col_p2:
        if st.button("📰 The Daily Star", use_container_width=True):
            st.session_state.preset_url = "https://www.thedailystar.net/news/bangladesh"
    with col_p3:
        if st.button("📰 TBS News", use_container_width=True):
            st.session_state.preset_url = "https://www.tbsnews.net/bangladesh"
    with col_p4:
        if st.button("📰 DW News", use_container_width=True):
            st.session_state.preset_url = "https://www.dw.com/en/top-stories/s-9097"

    # Input elements reflecting selected presets dynamically
    url = st.text_input(
        "Target News / Document Article Link:", 
        value=st.session_state.preset_url,
        label_visibility="collapsed", 
        key="url_input_box", 
        placeholder="Paste any live news link here..."
    )
    
    with st.expander("🛠️ Custom Crawler Target Overrides"):
        custom_class = st.text_input("Explicit Content CSS Selector Override Tag:", placeholder="e.g. story-element-text")
        
    min_limit, max_limit = st.slider("Synthesis Prose Word Boundaries:", 40, 300, (60, 90), key="url_slider")
    st.markdown("<br>", unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns([4, 1])
    with b_col1:
        process_url = st.button("🚀 Process OneMinute Read", use_container_width=True, key="url_run_btn")
    with b_col2:
        if st.button("🗑️ Clear Workspace", use_container_width=True, key="clear_url_action"):
            st.session_state.headline = None
            st.session_state.last_summary = None
            st.session_state.model_used = None
            st.session_state.preset_url = ""
            st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
            st.rerun()

    if process_url:
        if url.strip():
            cache_key = f"url_{url.strip()}_{min_limit}_{max_limit}"
            if cache_key in st.session_state.cache_vault:
                cached_data = st.session_state.cache_vault[cache_key]
                st.session_state.headline = cached_data["headline"]
                st.session_state.last_summary = cached_data["summary"]
                st.session_state.model_used = cached_data["model"] + " (Cached Memory)"
                st.toast("Retrieved from workspace cache memory!", icon="💾")
            else:
                with st.spinner("Analyzing web ecosystem components..."):
                    content, scrap_err = extract_universal_content(url.strip(), custom_class=custom_class.strip())
                    if scrap_err:
                        st.error(scrap_err)
                    elif content:
                        hd, sm, active_model, ai_err = execute_summary(content, api_key, min_limit, max_limit)
                        if ai_err:
                            st.error(ai_err)
                        else:
                            st.session_state.headline = hd
                            st.session_state.last_summary = sm
                            st.session_state.model_used = active_model
                            st.session_state.cache_vault[cache_key] = {"headline": hd, "summary": sm, "model": active_model}
                            st.rerun()
        else:
            st.warning("Please specify an active article link pointer.")

    render_output_dashboard(st.session_state.get("model_used"))
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

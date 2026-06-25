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
st.set_page_config(page_title="InsightInMinutes | Pro News Dashboard", page_icon="🔎", layout="wide")

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

# ---------------------------
# 🎨 PREMIUM COCKPIT & LITERARY CARD THEME
# ---------------------------
THEME = {
    "background_color": "#0A0C10",       # Deep Void Space
    "sidebar_bg": "#0F1219",             # Matte Slate Panel
    "card_bg": "#141923",                # Deep Tech Core Card
    "card_border": "#222A3A",            # Neon Subdued Border
    "text_color": "#E2E8F0",             # Bright Titanium Text
    "accent_color": "#6366F1",           # Electric Indigo Spark
    "summary_accent": "#06B6D4",          # Cyber Cyan Synthesis
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
}

st.markdown(f"""
<style>
    /* Global Core Reset & Styling */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {THEME['background_color']};
        font-family: {THEME['font_family']};
        color: {THEME['text_color']};
    }}
    
    .full-width-wrapper {{
        width: 100%;
        margin-bottom: 25px;
    }}
    
    /* 🧬 Premium Output HUD Cards */
    .headline-card-premium {{
        background: {THEME['card_bg']};
        border: 1px solid {THEME['card_border']};
        border-left: 6px solid {THEME['accent_color']};
        border-radius: 14px;
        padding: 26px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.15);
    }}
    
    .summary-card-premium {{
        background: {THEME['card_bg']};
        border: 1px solid {THEME['card_border']};
        border-left: 6px solid {THEME['summary_accent']};
        border-radius: 14px;
        padding: 26px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px -10px rgba(6, 182, 212, 0.15);
    }}
    
    .badge-headline {{
        font-size: 10px;
        text-transform: uppercase;
        font-weight: 700;
        color: {THEME['accent_color']};
        letter-spacing: 0.08em;
        display: inline-block;
        margin-bottom: 10px;
        background: rgba(99, 102, 241, 0.12);
        padding: 2px 8px;
        border-radius: 4px;
    }}
    
    .badge-summary {{
        font-size: 10px;
        text-transform: uppercase;
        font-weight: 700;
        color: {THEME['summary_accent']};
        letter-spacing: 0.08em;
        display: inline-block;
        margin-bottom: 10px;
        background: rgba(6, 182, 212, 0.12);
        padding: 2px 8px;
        border-radius: 4px;
    }}
    
    /* 📊 Next-Gen Sidebar Analytics Module */
    .token-container {{
        background: #0B0E14;
        border: 1px solid {THEME['card_border']};
        border-radius: 12px;
        padding: 18px;
        margin-top: 5px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
    }}
    .progress-bar-wrapper {{
        margin-bottom: 14px;
    }}
    .progress-bar-label {{
        display: flex;
        justify-content: space-between;
        font-size: 11.5px;
        font-weight: 700;
        margin-bottom: 10px;
        color: #38BDF8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .progress-legend {{
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        margin-bottom: 12px;
        background: rgba(255,255,255,0.02);
        padding: 6px;
        border-radius: 6px;
    }}
    .legend-item {{
        display: flex;
        align-items: center;
        gap: 6px;
        color: #CBD5E1;
    }}
    .progress-track-segmented {{
        background: #1E293B;
        border-radius: 30px;
        height: 8px;
        width: 100%;
        display: flex;
        overflow: hidden;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.6);
    }}
    .segment-input {{ background: #EF4444; height: 100%; transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 0 8px #EF4444; }}
    .segment-output {{ background: {THEME['summary_accent']}; height: 100%; transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 0 8px {THEME['summary_accent']}; }}
    
    .token-row-total {{
        display: flex;
        justify-content: space-between;
        padding-top: 10px;
        font-size: 13px;
        font-weight: 700;
        color: #38BDF8;
        border-top: 1px solid #1E293B;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }}
    
    /* 🏛️ Book Recommender-Style Literary Cards */
    .brand-hud-card {{
        background: linear-gradient(135deg, #181E2C 0%, #10141D 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }}
    .brand-hud-title {{
        font-size: 20px !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #FFFFFF, #93C5FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 4px 0 !important;
        letter-spacing: -0.03em;
    }}
    .brand-hud-tag {{
        font-size: 11px;
        color: #38BDF8;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.1em;
    }}
    
    .author-literary-card {{
        background: #131722;
        border: 1px solid #232A3C;
        border-radius: 12px;
        padding: 16px;
        margin-top: 25px;
        position: relative;
    }}
    .author-literary-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 15px; right: 15px; height: 2px;
        background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.4), transparent);
    }}
    .author-header-label {{
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #64748B;
        margin-bottom: 12px;
        display: block;
    }}
    .author-name-text {{
        font-size: 15px;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 2px;
    }}
    .author-role-tag {{
        font-size: 12px;
        color: #06B6D4;
        font-weight: 500;
        margin-bottom: 10px;
    }}
    .author-bio-quote {{
        font-size: 12.5px;
        color: #94A3B8;
        line-height: 1.5;
        font-style: italic;
        border-left: 2px solid #334155;
        padding-left: 8px;
        margin: 8px 0 0 0;
    }}
    
    /* Structural Typography Overrides */
    h1, h2, h3, h4, h5 {{
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }}
    
    /* Form Element Architecture */
    .stTextArea textarea, .stTextInput>div>input {{
        background-color: {THEME['card_bg']} !important;
        border: 1px solid {THEME['card_border']} !important;
        border-radius: 10px !important;
        color: {THEME['text_color']} !important;
        transition: all 0.2s ease-in-out;
    }}
    .stTextArea textarea:focus, .stTextInput>div>input:focus {{
        border-color: {THEME['accent_color']} !important;
        box-shadow: 0 0 0 1px {THEME['accent_color']} !important;
    }}
    
    /* Sidebar Shell Overlays */
    [data-testid="stSidebar"] {{
        background-color: {THEME['sidebar_bg']} !important;
        border-right: 1px solid {THEME['card_border']};
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
def extract_universal_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
                
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
            if model_meta["supports_thinking"]:
                generate_config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=1024),
                    tools=[types.Tool(googleSearch=types.GoogleSearch())]
                )
            else:
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
                headline = "Insights Update"
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
            <span class="badge-headline">Generated Flash Headline</span>
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
        # 🏛️ Brand HUD Layout
        st.markdown("""
        <div class="brand-hud-card">
            <h2 class="brand-hud-title">🔎 InsightInMinutes</h2>
            <div class="brand-hud-tag">Universal Core Engine</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 📊 Embedded Active Token Counters Module
        total_volume = st.session_state.token_metrics["total"]
        input_pct = (st.session_state.token_metrics["input"] / total_volume * 100) if total_volume > 0 else 0
        output_pct = (st.session_state.token_metrics["output"] / total_volume * 100) if total_volume > 0 else 0
        
        st.markdown(f"""
        <div class="token-container">
            <div class="progress-bar-wrapper">
                <div class="progress-bar-label">
                    <span>Active Token Counters</span>
                </div>
                <div class="progress-legend">
                    <div class="legend-item"><span style="color:#EF4444;">●</span> In ({st.session_state.token_metrics["input"]})</div>
                    <div class="legend-item"><span style="color:{THEME['summary_accent']};">●</span> Out ({st.session_state.token_metrics["output"]})</div>
                </div>
                <div class="progress-track-segmented">
                    <div class="segment-input" style="width: {input_pct}%;"></div>
                    <div class="segment-output" style="width: {output_pct}%;"></div>
                </div>
            </div>
            <div class="token-row-total">
                <span>Total Billed Volume</span>
                <span>{total_volume}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 📚 Editorial / Book Recommender-Style Author Module
        st.markdown("""
        <div class="author-literary-card">
            <span class="author-header-label">Curator Profile</span>
            <div class="author-name-text">Tanvir Anzum</div>
            <div class="author-role-tag">AI & Data Researcher</div>
            <p class="author-bio-quote">
                "Passionate about synthesis systems, cross-domain telemetry processing, and turning raw structured matrix vectors into human insights."
            </p>
        </div>
        """, unsafe_allow_html=True)

    if api_err:
        st.sidebar.error(api_err)
        return

    # Direct Interface Area Layout
    st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
    url = st.text_input("Paste a Live News Link:", key="url_input_box", placeholder="Paste any live link here...")
    
    min_limit, max_limit = st.slider("Synthesis Prose Word Boundaries:", 40, 300, (75, 90), key="url_slider")
    st.markdown("<br>", unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns([4, 1])
    with b_col1:
        process_url = st.button("🚀 Process Domain Insights", use_container_width=True, key="url_run_btn")
    with b_col2:
        if st.button("🗑️ Clear Workspace", use_container_width=True, key="clear_url_action"):
            st.session_state.headline = None
            st.session_state.last_summary = None
            st.session_state.model_used = None
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
                    content, scrap_err = extract_universal_content(url.strip())
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

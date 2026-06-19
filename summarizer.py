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
if "bullets" not in st.session_state:
    st.session_state.bullets = []
if "reading_time" not in st.session_state:
    st.session_state.reading_time = 0
if "sentiment" not in st.session_state:
    st.session_state.sentiment = "Neutral"
if "model_used" not in st.session_state:
    st.session_state.model_used = None
if "token_metrics" not in st.session_state:
    st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
if "cache_vault" not in st.session_state:
    st.session_state.cache_vault = {}

# ---------------------------
# 🎨 PREMIUM REFINED DESIGN THEME
# ---------------------------
THEME = {
    "background_color": "#0F1115",       # Rich Slate Dark
    "card_bg": "#1A1D24",                # Charcoal Panel
    "card_border": "#2D3139",            # Modern Gray Trim
    "text_color": "#E1E4EA",             # Clean Off-White
    "accent_color": "#4F46E5",           # Electric Indigo
    "classic_summary_bg": "#FFFDF6",     # High-Contrast Paper White
    "classic_summary_border": "#C5A880", # Premium Gold Asset Border
    "classic_text_color": "#111111",     # Deep Typography Ink Gray
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

    /* 📜 Classic Editorial Content Paper White Block Styles */
    .summary-section {{
        padding: 30px;
        border: 1px solid {THEME['classic_summary_border']};
        border-top: 6px solid {THEME['classic_summary_border']};
        background-color: {THEME['classic_summary_bg']};
        border-radius: 6px;
        margin-top: 20px;
        margin-bottom: 20px;
        color: {THEME['classic_text_color']};
        box-shadow: 0 15px 35px -10px rgba(0,0,0,0.5);
    }}
    .summary-section h2 {{
        color: #000000 !important;
        font-family: 'Georgia', serif;
        font-size: 28px;
        font-weight: 800;
        margin-top: 0;
        margin-bottom: 15px;
        text-align: left;
        line-height: 1.3;
    }}
    .summary-section p {{
        color: {THEME['classic_text_color']} !important;
        font-size: 15.5px;
        line-height: 1.7;
        text-align: justify;
        margin-bottom: 20px;
    }}
    
    /* Meta Information Badges */
    .meta-badge-container {{
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }}
    .meta-badge {{
        background: rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.1);
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: #444444;
    }}
    
    /* Bulleted Editorial Core Insights */
    .takeout-header {{
        font-size: 13px;
        text-transform: uppercase;
        font-weight: 700;
        color: #8B6E4E;
        letter-spacing: 0.06em;
        margin-top: 20px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(0,0,0,0.1);
        padding-bottom: 4px;
    }}
    .bullet-item {{
        font-size: 14.5px;
        margin: 8px 0;
        display: flex;
        gap: 8px;
        align-items: flex-start;
        color: #222222;
    }}
    
    /* Segmented Telemetry Inline Box Component styling */
    .token-container {{
        background: #111318;
        border: 1px solid {THEME['card_border']};
        border-radius: 10px;
        padding: 16px;
        margin-top: 10px;
    }}
    .progress-bar-wrapper {{
        margin-bottom: 14px;
    }}
    .progress-bar-label {{
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        margin-bottom: 4px;
        color: #9CA3AF;
    }}
    .progress-legend {{
        display: flex;
        gap: 12px;
        font-size: 11px;
        margin-bottom: 8px;
    }}
    .legend-item {{
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    .progress-track-segmented {{
        background: #2D3139;
        border-radius: 20px;
        height: 10px;
        width: 100%;
        display: flex;
        overflow: hidden;
    }}
    .segment-input {{ background: #EF4444; height: 100%; transition: width 0.6s ease-in-out; }}
    .segment-output {{ background: #10B981; height: 100%; transition: width 0.6s ease-in-out; }}
    
    .token-row-total {{
        display: flex;
        justify-content: space-between;
        padding-top: 8px;
        font-size: 14px;
        font-weight: bold;
        color: #3B82F6;
        border-top: 1px solid #2D3139;
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

    .terminal-card {{
        background: #1E1E24;
        border-left: 4px solid #EF4444;
        padding: 18px;
        border-radius: 8px;
        font-family: monospace;
        color: #F87171;
        margin: 15px 0;
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
# Advanced Editorial Engine Core
# ---------------------------
def execute_summary(content, api_key, min_limit, max_limit):
    try:
        detected_lang = langdetect.detect(content)
    except Exception:
        detected_lang = "en"
        
    client = genai.Client(api_key=api_key)
    
    prompt = (
        f"You are an expert news desk editor. Summarize the content in the {detected_lang} language.\n"
        f"Extract structural analytical elements according to the following constraints:\n"
        f"1. Generate an impactful headline prefixed with 'HEADLINE:'.\n"
        f"2. Extract exactly 3 clear summary takeaways prefixed with 'BULLETS:'. Separate each bullet point with a tilde (~).\n"
        f"3. Classify article sentiment tone cleanly as Positive, Negative, or Neutral, prefixed with 'SENTIMENT:'.\n"
        f"4. Write a dense prose summary essay between {min_limit} and {max_limit} words, prefixed with 'SUMMARY:'.\n\n"
        f"Source Text Content:\n{content}"
    )

    model_cascade_pool = [
        {"name": "gemini-2.5-flash", "supports_thinking": False},
        {"name": "gemini-2.5-flash-lite", "supports_thinking": False},
        {"name": "gemini-2.0-flash", "supports_thinking": False},
        {"name": "gemini-3-flash-preview", "supports_thinking": True}
    ]
    
    collected_errors = []
    
    for model_meta in model_cascade_pool:
        current_model = model_meta["name"]
        try:
            if model_meta["supports_thinking"]:
                generate_config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
                    tools=[types.Tool(googleSearch=types.GoogleSearch())]
                )
            else:
                generate_config = types.GenerateContentConfig(
                    tools=[types.Tool(googleSearch=types.GoogleSearch())]
                )
                
            response = client.models.generate_content(
                model=current_model, contents=prompt, config=generate_config
            )
            
            if response and response.text:
                raw_text = response.text.strip()
                
                headline = "Insights Wire Brief"
                summary_body = raw_text
                bullets = ["Core takeout analysis completed safely."]
                sentiment = "Neutral"
                
                try:
                    headline_match = re.search(r"HEADLINE:\s*(.*?)(?=\n[A-Z]+:|$)", raw_text, re.DOTALL)
                    bullets_match = re.search(r"BULLETS:\s*(.*?)(?=\n[A-Z]+:|$)", raw_text, re.DOTALL)
                    sentiment_match = re.search(r"SENTIMENT:\s*(.*?)(?=\n[A-Z]+:|$)", raw_text, re.DOTALL)
                    summary_match = re.search(r"SUMMARY:\s*(.*?)$", raw_text, re.DOTALL)
                    
                    if headline_match: headline = headline_match.group(1).strip()
                    if sentiment_match: sentiment = sentiment_match.group(1).strip()
                    if summary_match: summary_body = summary_match.group(1).strip()
                    if bullets_match: 
                        bullets = [b.replace("-", "").strip() for b in bullets_match.group(1).split("~") if b.strip()]
                except Exception:
                    split_lines = [l for l in raw_text.splitlines() if l.strip()]
                    if split_lines: headline = split_lines[0]
                
                raw_words_count = len(content.split())
                st.session_state.reading_time = max(1, round(raw_words_count / 220))
                st.session_state.bullets = bullets
                st.session_state.sentiment = sentiment

                input_tokens = int(len(prompt.split()) * 1.3)
                output_tokens = int(len(raw_text.split()) * 1.3)
                
                st.session_state.token_metrics["input"] = input_tokens
                st.session_state.token_metrics["output"] = output_tokens
                st.session_state.token_metrics["total"] = input_tokens + output_tokens
                    
                return headline, summary_body, current_model, None
                
        except Exception as e:
            collected_errors.append(f"{current_model}: {str(e)}")
            continue
            
    return None, None, None, "Cascade pools exhausted."

# ---------------------------
# UI Presentation Layer
# ---------------------------
def render_output_dashboard(model_used=None):
    if st.session_state.last_summary:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        
        # Assembling bullet loops safely
        bullet_html_payload = ""
        for b in st.session_state.bullets:
            if b.strip():
                bullet_html_payload += f'<div class="bullet-item">🔸 <span>{b.strip()}</span></div>'
        
        # 📜 Beautiful Unified Paper White Newsroom Box Component
        st.markdown(f"""
        <div class="summary-section">
            <h2>{st.session_state.headline}</h2>
            
            <div class="meta-badge-container">
                <div class="meta-badge">📖 Read Time: {st.session_state.reading_time} min</div>
                <div class="meta-badge">📊 Sentiment: {st.session_state.sentiment}</div>
                <div class="meta-badge" style="color:#4F46E5;">⚡ Engine: {model_used}</div>
            </div>
            
            <p>{st.session_state.last_summary}</p>
            
            <div class="takeout-header">⚡ Core Editorial Takeouts</div>
            {bullet_html_payload}
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Workspace Main Shell Controller Entrypoint
# ---------------------------
def main():
    api_key, api_err = read_api_key()
    
    with st.sidebar:
        st.markdown("<h2 style='text-align:left; color:#FFF; margin-bottom:0;'>🔎 InsightInMinutes</h2>", unsafe_allow_html=True)
        st.caption("Pro Editorial Summarization Suite")
        
        st.markdown("---")
        st.markdown("### 📊 Active Token Counters")
        
        total_volume = st.session_state.token_metrics["total"]
        input_pct = (st.session_state.token_metrics["input"] / total_volume * 100) if total_volume > 0 else 0
        output_pct = (st.session_state.token_metrics["output"] / total_volume * 100) if total_volume > 0 else 0
        
        st.sidebar.markdown(f"""
        <div class="token-container">
            <div class="progress-bar-wrapper">
                <div class="progress-bar-label">
                    <span>Token Distribution Mix</span>
                    <span>{total_volume} total</span>
                </div>
                <div class="progress-legend">
                    <div class="legend-item"><span style="color:#EF4444;">●</span> Input ({st.session_state.token_metrics["input"]})</div>
                    <div class="legend-item"><span style="color:#10B981;">●</span> Output ({st.session_state.token_metrics["output"]})</div>
                </div>
                <div class="progress-track-segmented">
                    <div class="segment-input" style="width: {input_pct}%;"></div>
                    <div class="segment-output" style="width: {output_pct}%;"></div>
                </div>
            </div>
            <div class="token-row-total">
                <span>Billed Token Volume</span>
                <span>{total_volume}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.title("👨‍💻 About the Author")
        st.caption("Tanvir Anzum – AI & Data Researcher")
        st.markdown("<div style='font-size:14px; color:#9CA3AF;'>Passionate about turning data into insights.</div>", unsafe_allow_html=True)

    if api_err:
        st.error(api_err)
        return

    # 🌐 Tab Navigation Setup Panel
    tab_url, tab_text = st.tabs(["🌐 Live Domain URL Pipeline", "📝 Raw Text Block Parser"])

    with tab_url:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        url = st.text_input("Target News / Document Article Link:", key="url_input_box", placeholder="Paste any live link here...")
        
        with st.expander("🛠️ Custom Crawler Target Overrides"):
            custom_class = st.text_input("Explicit Content CSS Selector Override Tag:", placeholder="e.g. story-element-text")
            
        # Default Slider Constraints updated to exact 75-90 metric counts bounds window
        min_limit, max_limit = st.slider("Synthesis Prose Word Boundaries:", 40, 300, (75, 90), key="url_slider")
        st.markdown("<br>", unsafe_allow_html=True)
        
        b_col1, b_col2 = st.columns([4, 1])
        with b_col1:
            process_url = st.button("🚀 Process Editorial Briefing", use_container_width=True, key="url_run_btn")
        with b_col2:
            if st.button("🗑️ Clear Workspace", use_container_width=True, key="clear_url_action"):
                st.session_state.headline = None
                st.session_state.last_summary = None
                st.session_state.model_used = None
                st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
                st.markdown("<script>window.location.reload();</script>", unsafe_allow_html=True)
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

    with tab_text:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        raw_text = st.text_area("Pro Text Matrix Dropzone Area Block:", key="text_input_box", height=250, placeholder="Paste text copy blocks directly into this zone area...")
        
        # Default Slider Constraints updated to exact 75-90 metric counts bounds window
        min_limit, max_limit = st.slider("Synthesis Prose Word Boundaries:", 40, 300, (75, 90), key="text_slider")
        st.markdown("<br>", unsafe_allow_html=True)
        
        b_col1, b_col2 = st.columns([4, 1])
        with b_col1:
            process_text = st.button("🚀 Synthesize Transcripts Passage", use_container_width=True, key="text_run_btn")
        with b_col2:
            if st.button("🗑️ Clear Workspace", use_container_width=True, key="clear_text_action"):
                st.session_state.headline = None
                st.session_state.last_summary = None
                st.session_state.model_used = None
                st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
                st.rerun()

        if process_text:
            if raw_text.strip():
                cache_key = f"text_{hash(raw_text.strip())}_{min_limit}_{max_limit}"
                if cache_key in st.session_state.cache_vault:
                    cached_data = st.session_state.cache_vault[cache_key]
                    st.session_state.headline = cached_data["headline"]
                    st.session_state.last_summary = cached_data["summary"]
                    st.session_state.model_used = cached_data["model"] + " (Cached Memory)"
                else:
                    with st.spinner("Processing sequence matrix inputs..."):
                        hd, sm, active_model, ai_err = execute_summary(raw_text.strip(), api_key, min_limit, max_limit)
                        if ai_err:
                            st.error(ai_err)
                        else:
                            st.session_state.headline = hd
                            st.session_state.last_summary = sm
                            st.session_state.model_used = active_model
                            st.session_state.cache_vault[cache_key] = {"headline": hd, "summary": sm, "model": active_model}
                            st.rerun()
            else:
                st.warning("Please supply valid inputs into character map buffers.")

        render_output_dashboard(st.session_state.get("model_used"))
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

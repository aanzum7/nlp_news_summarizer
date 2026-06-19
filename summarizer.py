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
st.set_page_config(page_title="InsightInMinutes | Pro Editorial Suite", page_icon="📰", layout="wide")

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
# 🎨 HIGH-CONTRAST NEWSROOM DESIGN THEME
# ---------------------------
THEME = {
    "background_color": "#090A0F",       # Midnight Ink Dark
    "card_bg": "#12141C",                # Slate Dashboard Surface
    "card_border": "#1E2230",            # Structural Trim
    "text_color": "#E2E8F0",             # Editorial Body Text
    "accent_color": "#6366F1",           # Electric Indigo
    "editorial_cream": "#FFFDF6",        # High-Contrast Paper White
    "editorial_ink": "#111111",          # Deep Typography Gray
    "editorial_gold": "#C5A880",         # Premium Asset Border
    "font_family": "'Inter', system-ui, -apple-system, sans-serif"
}

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {THEME['background_color']};
        font-family: {THEME['font_family']};
        color: {THEME['text_color']};
    }}
    
    /* Full Width Control Containers */
    .full-width-wrapper {{
        width: 100%;
        margin-bottom: 25px;
    }}
    
    /* 📜 Executive Newsroom Editorial Box Style */
    .pro-editorial-board {{
        background-color: {THEME['editorial_cream']};
        border-top: 6px solid {THEME['editorial_gold']};
        border-bottom: 2px solid {THEME['editorial_gold']};
        padding: 35px;
        border-radius: 4px;
        color: {THEME['editorial_ink']};
        box-shadow: 0 20px 40px -15px rgba(0,0,0,0.7);
    }}
    
    .pro-editorial-board h2 {{
        color: {THEME['editorial_ink']} !important;
        font-family: 'Georgia', serif;
        font-weight: 800;
        font-size: 32px;
        line-height: 1.2;
        margin-top: 0;
        margin-bottom: 15px;
        text-align: left;
    }}
    
    .pro-editorial-board p {{
        color: {THEME['editorial_ink']} !important;
        font-family: 'Georgia', serif;
        font-size: 16px;
        line-height: 1.8;
        text-align: justify;
    }}
    
    /* Dynamic Metric Badges */
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
        letter-spacing: 0.03em;
        color: #444444;
    }}
    
    /* Bulleted Flash Core takeaways layout */
    .takeout-header {{
        font-size: 14px;
        text-transform: uppercase;
        font-weight: 700;
        color: {THEME['editorial_gold']};
        letter-spacing: 0.06em;
        margin-top: 20px;
        margin-bottom: 8px;
        border-bottom: 1px solid rgba(0,0,0,0.1);
        padding-bottom: 4px;
    }}
    .bullet-item {{
        font-size: 14px;
        margin: 6px 0;
        display: flex;
        gap: 8px;
        align-items: flex-start;
        color: #222222;
    }}
    
    /* Interactive Sidebar Metrics Box with Color Progress Bars */
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
        background-color: #12141C !important;
        border: 1px solid {THEME['card_border']} !important;
        border-radius: 8px !important;
        color: {THEME['text_color']} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: #0B0C10 !important;
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
# Pro Sequence Complex Inference Core
# ---------------------------
def execute_summary(content, api_key, min_limit, max_limit):
    try:
        detected_lang = langdetect.detect(content)
    except Exception:
        detected_lang = "en"
        
    client = genai.Client(api_key=api_key)
    
    # Professional journalistic structured parsing schema blueprint
    prompt = (
        f"You are a professional editorial news desk agent operating in language space: {detected_lang}.\n"
        f"Analyze the text corpus provided below and extract analytical structures.\n\n"
        f"Strict Formatting Rules:\n"
        f"1. Generate a sharp, impactful news headline prefixed exactly with 'HEADLINE:'.\n"
        f"2. Extract exactly 3 core bullet points summary takeaways prefixed exactly with 'BULLETS:'. Separate each bullet with a tilde character (~).\n"
        f"3. Quantify the underlying article tone sentiment as exactly one of [Positive, Negative, Neutral] prefixed exactly with 'SENTIMENT:'.\n"
        f"4. Author a detailed analytical synthesis summary essay of length {min_limit} to {max_limit} words, prefixed exactly with 'SUMMARY:'.\n\n"
        f"Text Material:\n{content}"
    )

    model_cascade_pool = [
        {"name": "gemini-2.5-flash", "supports_thinking": False},
        {"name": "gemini-2.5-flash-lite", "supports_thinking": False},
        {"name": "gemini-2.0-flash", "supports_thinking": False},
        {"name": "gemini-3-flash-preview", "supports_thinking": True}
    ]
    
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
                
                # Structural block extractor mapping
                headline = "Editorial Wire Briefing"
                summary_body = "Failed to parse system elements text."
                bullets = ["Core takeout analysis tracking live."]
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
                    # Generic string chunking backup safety layout
                    split_lines = [l for l in raw_text.splitlines() if l.strip()]
                    if len(split_lines) > 1:
                        headline = split_lines[0]
                        summary_body = "\n".join(split_lines[1:])
                
                # Estimate word counting metrics parameters
                raw_words_count = len(content.split())
                st.session_state.reading_time = max(1, round(raw_words_count / 230))
                st.session_state.bullets = bullets
                st.session_state.sentiment = sentiment

                input_tokens = int(len(prompt.split()) * 1.3)
                output_tokens = int(len(raw_text.split()) * 1.3)
                st.session_state.token_metrics["input"] = input_tokens
                st.session_state.token_metrics["output"] = output_tokens
                st.session_state.token_metrics["total"] = input_tokens + output_tokens
                    
                return headline, summary_body, current_model, None
                
        except Exception as e:
            continue
            
    return None, None, None, "All editorial cascade system pools exhausted under current quota matrices."

# ---------------------------
# UI Presentation Layer
# ---------------------------
def render_output_dashboard(model_used=None):
    if st.session_state.last_summary:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        
        # Build list structure elements block safely
        bullet_html_payload = ""
        for b in st.session_state.bullets:
            if b.strip():
                bullet_html_payload += f'<div class="bullet-item">🔸 <span>{b.strip()}</span></div>'
        
        # 👑 Premium Editorial Workspace Layout
        st.markdown(f"""
        <div class="pro-editorial-board">
            <h2>{st.session_state.headline}</h2>
            
            <div class="meta-badge-container">
                <div class="meta-badge">📖 Read Time: {st.session_state.reading_time} min</div>
                <div class="meta-badge">📊 Sentiment: {st.session_state.sentiment}</div>
                <div class="meta-badge" style="color:{THEME['accent_color']};">⚡ Matrix Engine: {model_used}</div>
            </div>
            
            <p>{st.session_state.last_summary}</p>
            
            <div class="takeout-header">⚡ Core Editorial Takeouts</div>
            {bullet_html_payload}
        </div>
        """, unsafe_allow_html=True)
        
        # Clean production grade native copy container
        st.markdown("##### 📋 Clipboard Wire String")
        copy_string = f"📌 {st.session_state.headline}\n\n📝 SUMMARY:\n{st.session_state.last_summary}"
        st.code(copy_string, language="markdown", wrap_lines=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Main Application Entrypoint Framework
# ---------------------------
def main():
    api_key, api_err = read_api_key()
    
    with st.sidebar:
        st.markdown("<h2 style='text-align:left; color:#FFF; margin-bottom:0;'>🔎 InsightInMinutes</h2>", unsafe_allow_html=True)
        st.caption("Pro Editorial Summarization Suite")
        
        # 📊 Secure Sidebar Token Execution Progress Frame
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
        st.markdown("""
            <div style='font-size: 14px; font-weight: normal; color:#9CA3AF;'>
            Passionate about turning <strong>data into insights</strong> and building <strong>AI-powered tools</strong> for real-world impact.
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style='font-size: 14px; font-weight: normal;'>
            <br>
            <a href="https://www.linkedin.com/in/aanzum" target="_blank" style="color:#4F46E5; text-decoration:none;">
                <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="14" style="vertical-align:middle; margin-right:4px;">
                <strong>LinkedIn</strong>
            </a>
            &nbsp;&nbsp;&nbsp;
            <a href="https://www.researchgate.net/profile/Tanvir-Anzum" target="_blank" style="color:#4F46E5; text-decoration:none;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/5/5e/ResearchGate_icon_SVG.svg" alt="ResearchGate" width="14" style="vertical-align:middle; margin-right:4px;">
                <strong>Research</strong>
            </a>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    if api_err:
        st.error(api_err)
        return

    # 🌐 Native Navigation Tab Stack Workspace Panels
    tab_url, tab_text = st.tabs(["🌐 Live Domain URL Pipeline", "📝 Raw Text Block Parser"])

    with tab_url:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        url = st.text_input("Target News / Document Article Link:", key="url_input_box", placeholder="Paste any live domain link or data resource page here...")
        
        with st.expander("🛠️ Custom Crawler Target Overrides"):
            custom_class = st.text_input("Explicit Content CSS Selector Override Tag:", placeholder="e.g. article-body-paragraphs-class")
            
        min_limit, max_limit = st.slider("Synthesis Prose Word Boundaries:", 50, 400, (80, 180), key="url_slider")
        
        b_col1, b_col2 = st.columns([4, 1])
        with b_col1:
            process_url = st.button("🚀 Process Editorial Briefing", use_container_width=True, key="url_run_btn")
        with b_col2:
            if st.button("🗑️ Clear Active Workspace", use_container_width=True, key="clear_url_action"):
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
                    st.session_state.model_used = cached_data["model"] + " (Cached Cache Memory)"
                    st.toast("Retrieved from local workspace memory cache!", icon="💾")
                else:
                    with st.spinner("Scraping web components ecosystem & assembling editorial breakdown structure..."):
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
                                st.toast("Insights parsing finalized completely!", icon="✅")
                                st.rerun()
            else:
                st.warning("Please verify text is assigned inside link address parameter inputs.")
        
        render_output_dashboard(st.session_state.get("model_used"))
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_text:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        raw_text = st.text_area("Pro Text Matrix Dropzone Area Block:", key="text_input_box", height=250, placeholder="Paste raw documentation passages, literature entries, or notes details directly inside this workspace area...")
        min_limit, max_limit = st.slider("Synthesis Prose Word Boundaries:", 50, 400, (80, 180), key="text_slider")
        
        b_col1, b_col2 = st.columns([4, 1])
        with b_col1:
            process_text = st.button("🚀 Synthesize Transcripts Passage", use_container_width=True, key="text_run_btn")
        with b_col2:
            if st.button("🗑️ Clear Active Workspace", use_container_width=True, key="clear_text_action"):
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
                    st.session_state.model_used = cached_data["model"] + " (Cached Cache Memory)"
                    st.toast("Retrieved from local workspace memory cache!", icon="💾")
                else:
                    with st.spinner("Processing sequence matrix variables across context logs..."):
                        hd, sm, active_model, ai_err = execute_summary(raw_text.strip(), api_key, min_limit, max_limit)
                        if ai_err:
                            st.error(ai_err)
                        else:
                            st.session_state.headline = hd
                            st.session_state.last_summary = sm
                            st.session_state.model_used = active_model
                            st.session_state.cache_vault[cache_key] = {"headline": hd, "summary": sm, "model": active_model}
                            st.toast("Insights processing complete!", icon="✅")
                            st.rerun()
            else:
                st.warning("Please supply valid inputs into character map buffers.")
                
        render_output_dashboard(st.session_state.get("model_used"))
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

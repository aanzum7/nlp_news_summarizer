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
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "URL"
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
if "favorited_insights" not in st.session_state:
    st.session_state.favorited_insights = set()

# ---------------------------
# 🎨 PREMIUM THEME CONFIGURATION
# ---------------------------
THEME = {
    "background_color": "#0F1115",       # Rich Slate Dark
    "card_bg": "#1A1D24",                # Charcoal Panel
    "card_border": "#2D3139",            # Modern Gray Trim
    "text_color": "#E1E4EA",             # Clean Off-White
    "accent_color": "#4F46E5",           # Electric Indigo
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
}

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {THEME['background_color']};
        font-family: {THEME['font_family']};
        color: {THEME['text_color']};
    }}
    
    .news-card {{
        background: {THEME['card_bg']};
        border: 1px solid {THEME['card_border']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 15px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }}
    
    /* Interactive Dashboard Metrics Box with Color Progress Bars */
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
    .progress-track {{
        background: #2D3139;
        border-radius: 20px;
        height: 8px;
        width: 100%;
        overflow: hidden;
    }}
    .progress-fill-red {{
        background: #EF4444;
        height: 100%;
        border-radius: 20px;
        transition: width 0.6s ease-in-out;
    }}
    .progress-fill-green {{
        background: #10B981;
        height: 100%;
        border-radius: 20px;
        transition: width 0.6s ease-in-out;
    }}
    .token-row-total {{
        display: flex;
        justify-content: space-between;
        padding-top: 8px;
        font-size: 14px;
        font-weight: bold;
        color: #3B82F6;
        border-top: 1px solid #2D3139;
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
        st.markdown(f"""
        <div class="news-card" style="border-left: 5px solid {THEME['accent_color']};">
            <span style="font-size:11px; text-transform:uppercase; font-weight:600; color:{THEME['accent_color']}; tracking-spacing:0.05em;">Generated Flash Headline</span>
            <h2 style="text-align:left; margin-top:4px; font-size:24px; color:#FFFFFF;">{st.session_state.headline}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Premium Native Clipboard Copy Shell Component
        st.markdown("### 📄 Analytical Synthesis Summary")
        full_markdown_payload = f"📌 {st.session_state.headline}\n\n{st.session_state.last_summary}"
        st.code(full_markdown_payload, language="markdown", wrap_lines=True)
        
        # Actions Row
        current_id = st.session_state.headline
        is_loved = current_id in st.session_state.favorited_insights
        love_label = "❤️ Favorited" if is_loved else "🤍 Add to Favorites"
        
        col_fav, _ = st.columns([1.5, 4])
        with col_fav:
            if st.button(love_label, key="love_btn_action", use_container_width=True):
                if is_loved:
                    st.session_state.favorited_insights.remove(current_id)
                    st.toast("Removed from reading vault.")
                else:
                    st.session_state.favorited_insights.add(current_id)
                    st.toast("Saved to reading vault!", icon="❤️")
                st.rerun()

        if model_used:
            st.caption(f"⚡ Engine Allocation Telemetry: Processed via free cluster `{model_used}` node.")

# ---------------------------
# Base Route Workspace Views
# ---------------------------
def render_url_workspace(api_key):
    st.subheader("🌐 Universal URL Pipeline")
    
    url = st.text_input("Target Article Link:", key="url_input_box", placeholder="Paste any live media network link or resource page here...")
    
    with st.expander("🛠️ Advanced Extraction Configurations"):
        custom_class = st.text_input("Explicit Content CSS Selector Override (Optional):", placeholder="e.g. article-body-text-class")
        
    min_limit, max_limit = st.slider("Target Length Footprint (Words count limits):", 40, 300, (50, 120))
    st.markdown("<br>", unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns([4, 1])
    with b_col1:
        process_clicked = st.button("🚀 Process Domain Insights", use_container_width=True)
    with b_col2:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_url_action"):
            st.session_state.headline = None
            st.session_state.last_summary = None
            st.session_state.model_used = None
            st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
            st.markdown("<script>window.location.reload();</script>", unsafe_allow_html=True)
            st.rerun()

    if process_clicked:
        if url.strip():
            cache_key = f"url_{url.strip()}_{min_limit}_{max_limit}"
            if cache_key in st.session_state.cache_vault:
                cached_data = st.session_state.cache_vault[cache_key]
                st.session_state.headline = cached_data["headline"]
                st.session_state.last_summary = cached_data["summary"]
                st.session_state.model_used = cached_data["model"] + " (Cached Memory)"
                st.toast("Retrieved instantly from session cache!", icon="💾")
            else:
                with st.spinner("Extracting web payload components & generating insight layout..."):
                    content, scrap_err = extract_universal_content(url.strip(), custom_class=custom_class.strip())
                    if scrap_err:
                        st.error(scrap_err)
                    elif content:
                        hd, sm, active_model, ai_err = execute_summary(content, api_key, min_limit, max_limit)
                        if ai_err:
                            st.markdown("""
                            <div class="terminal-card">
                                🚨 <b>[AI Engine Outage Status: Roadtrip Pitstop]</b><br>
                                <span style="color:#A1A1AA;">Context: Cascade Fallback Pool Exhausted</span><br><br>
                                <i>"Whoops! All free models are currently catching their breath at a highway diner. 
                                Let's give the parameters a moment to cycle before running again."</i>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.session_state.headline = hd
                            st.session_state.last_summary = sm
                            st.session_state.model_used = active_model
                            st.session_state.cache_vault[cache_key] = {"headline": hd, "summary": sm, "model": active_model}
                            st.toast("Insights processing complete!", icon="✅")
                            st.rerun()
        else:
            st.warning("Please supply a valid location URL link pointer.")
            
    render_output_dashboard(st.session_state.get("model_used"))

def render_text_workspace(api_key):
    st.subheader("📝 Textual Matrix Pipeline")
    
    raw_text = st.text_area("Source Text Dropzone Block:", key="text_input_box", height=250, placeholder="Paste your text here...")
    min_limit, max_limit = st.slider("Target Length Footprint (Words count limits):", 40, 300, (50, 120))
    st.markdown("<br>", unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns([4, 1])
    with b_col1:
        process_clicked = st.button("🚀 Synthesize Textual Blocks", use_container_width=True)
    with b_col2:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_text_action"):
            st.session_state.headline = None
            st.session_state.last_summary = None
            st.session_state.model_used = None
            st.session_state.token_metrics = {"input": 0, "output": 0, "total": 0}
            st.rerun()

    if process_clicked:
        if raw_text.strip():
            cache_key = f"text_{hash(raw_text.strip())}_{min_limit}_{max_limit}"
            if cache_key in st.session_state.cache_vault:
                cached_data = st.session_state.cache_vault[cache_key]
                st.session_state.headline = cached_data["headline"]
                st.session_state.last_summary = cached_data["summary"]
                st.session_state.model_used = cached_data["model"] + " (Cached Memory)"
                st.toast("Retrieved instantly from session cache!", icon="💾")
            else:
                with st.spinner("Executing sequence processing logic across inputs..."):
                    hd, sm, active_model, ai_err = execute_summary(raw_text.strip(), api_key, min_limit, max_limit)
                    if ai_err:
                        st.markdown("""
                        <div class="terminal-card">
                            🚨 <b>[AI Engine Outage Status: Roadtrip Pitstop]</b><br>
                            <span style="color:#A1A1AA;">Context: Cascade Fallback Pool Exhausted</span><br><br>
                            <i>"Whoops! All free models are currently catching their breath at a highway diner. 
                            Let's give the parameters a moment to cycle before running again."</i>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.session_state.headline = hd
                        st.session_state.last_summary = sm
                        st.session_state.model_used = active_model
                        st.session_state.cache_vault[cache_key] = {"headline": hd, "summary": sm, "model": active_model}
                        st.toast("Synthesis processing complete!", icon="✅")
                        st.rerun()
        else:
            st.warning("Please populate the data container target with character arrays.")
            
    render_output_dashboard(st.session_state.get("model_used"))

# ---------------------------
# Main Shell Framework
# ---------------------------
def main():
    api_key, api_err = read_api_key()
    
    with st.sidebar:
        st.markdown("<h2 style='text-align:left; color:#FFF; margin-bottom:0;'>🔎 InsightInMinutes</h2>", unsafe_allow_html=True)
        st.caption("Deep-Thinking Universal Core Engine")
        st.markdown("---")
        
        st.markdown("### Pipeline Portals")
        if st.button("🌐 Live Domain URL Pipeline", use_container_width=True):
            st.session_state.selected_page = "URL"
            st.session_state.last_summary = None
            st.rerun()
        if st.button("📝 Raw Text Block Parser", use_container_width=True):
            st.session_state.selected_page = "TEXT"
            st.session_state.last_summary = None
            st.rerun()
            
        # Fixed 100% Core Dynamic Progress Tracking Side Panel
        st.markdown("---")
        st.markdown("### 📊 Active Token Counters")
        
        total_volume = st.session_state.token_metrics["total"]
        input_pct = (st.session_state.token_metrics["input"] / total_volume * 100) if total_volume > 0 else 0
        output_pct = (st.session_state.token_metrics["output"] / total_volume * 100) if total_volume > 0 else 0
        
        # Fixed: Passed into dedicated sidebar renderer context block
        st.sidebar.markdown(f"""
        <div class="token-container">
            <div class="progress-bar-wrapper">
                <div class="progress-bar-label">
                    <span>Input Volume Allocation</span>
                    <span>{st.session_state.token_metrics["input"]} tokens</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill-red" style="width: {input_pct}%;"></div>
                </div>
            </div>
            
            <div class="progress-bar-wrapper">
                <div class="progress-bar-label">
                    <span>Output Volume Allocation</span>
                    <span>{st.session_state.token_metrics["output"]} tokens</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill-green" style="width: {output_pct}%;"></div>
                </div>
            </div>
            
            <div class="token-row-total">
                <span>Total Accounted Volume</span>
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

    if st.session_state.selected_page == "URL":
        render_url_workspace(api_key)
    else:
        render_text_workspace(api_key)

if __name__ == "__main__":
    main()

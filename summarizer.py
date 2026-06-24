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
if "agg_news_data" not in st.session_state:
    st.session_state.agg_news_data = []

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

    .news-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 20px;
        margin-top: 15px;
    }}
    .news-card {{
        background: {THEME['card_bg']};
        border: 1px solid {THEME['card_border']};
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .source-badge {{
        font-size: 10px;
        text-transform: uppercase;
        font-weight: bold;
        padding: 3px 8px;
        border-radius: 4px;
        color: #FFF;
        display: inline-block;
        margin-bottom: 10px;
        width: max-content;
    }}
    .source-pa {{ background-color: #0284C7; }}
    .source-tds {{ background-color: #B45309; }}
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
            "prothomalo\\.com": ["story-element-text", "story-elements"],
            "thedailystar\\.net": ["pb-20", "clearfix", "story-section", "article-content"]
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
# Automated Feed Discovery Engine
# ---------------------------
def discover_macro_news():
    feeds = {
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "The Daily Star": "https://www.thedailystar.net/frontpage/rss.xml"
    }
    discovered_records = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for source, endpoint in feeds.items():
        try:
            res = requests.get(endpoint, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, features="xml")
                items = soup.find_all("item")
                count = 0
                for item in items:
                    if count >= 5:
                        break
                    title = item.find("title").get_text(strip=True) if item.find("title") else ""
                    link = item.find("link").get_text(strip=True) if item.find("link") else ""
                    if title and link:
                        discovered_records.append({
                            "source": source,
                            "title": title,
                            "link": link,
                            "summary": None,
                            "headline": None
                        })
                        count += 1
        except Exception:
            continue
    return discovered_records

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
        st.markdown("<h2 style='text-align:left; color:#FFF; margin-bottom:0;'>🔎 InsightInMinutes</h2>", unsafe_allow_html=True)
        st.caption("Deep-Thinking Universal Core Engine")
        
        st.markdown("---")
        st.markdown("### 📊 Active Token Counters")
        
        total_volume = st.session_state.token_metrics["total"]
        input_pct = (st.session_state.token_metrics["input"] / total_volume * 100) if total_volume > 0 else 0
        output_pct = (st.session_state.token_metrics["output"] / total_volume * 100) if total_volume > 0 else 0
        
        st.markdown(f"""
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

    # Tabs definition
    tab_auto, tab_url, tab_text = st.tabs([
        "📰 Automated Regional News Desk", 
        "🌐 Live Domain URL Pipeline", 
        "📝 Raw Text Block Parser"
    ])

    with tab_auto:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        st.markdown("### ⚡ Live Regional Ecosystem Feeds")
        st.caption("Fetches real-time macro updates (Top 5 items per publication) from Prothom Alo and The Daily Star.")
        
        if st.button("🔄 Poll News Ecosystem Feeds", use_container_width=True):
            with st.spinner("Polling live discovery hubs..."):
                discovered = discover_macro_news()
                if not discovered:
                    st.warning("No new feeds discovered from endpoints.")
                else:
                    current_links = {item["link"] for item in st.session_state.agg_news_data}
                    new_count = 0
                    for item in reversed(discovered):
                        if item["link"] not in current_links:
                            st.session_state.agg_news_data.insert(0, item)
                            new_count += 1
                    st.success(f"Ecosystem synced. Added {new_count} newer updates to workspace stack.")

        if st.session_state.agg_news_data:
            st.markdown('<div class="news-grid">', unsafe_allow_html=True)
            for index, news in enumerate(st.session_state.agg_news_data):
                badge_class = "source-pa" if news["source"] == "Prothom Alo" else "source-tds"
                
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <div>
                            <span class="source-badge {badge_class}">{news['source']}</span>
                            <h4 style="margin: 0 0 10px 0; font-size:16px; color:#FFF;">{news['title']}</h4>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([3, 1])
                    with c2:
                        if st.button("Synthesize", key=f"sys_{index}_{hash(news['link'])}", use_container_width=True):
                            with st.spinner("Scraping content..."):
                                content, scrap_err = extract_universal_content(news["link"])
                                if scrap_err:
                                    st.error(scrap_err)
                                elif content:
                                    hd, sm, active_model, ai_err = execute_summary(content, api_key, 60, 90)
                                    if ai_err:
                                        st.error(ai_err)
                                    else:
                                        st.session_state.agg_news_data[index]["headline"] = hd
                                        st.session_state.agg_news_data[index]["summary"] = sm
                                        st.toast("Analysis successfully synthesized!", icon="✅")
                    
                    if news["headline"] and news["summary"]:
                        st.markdown(f"""
                        <div style="margin-top:10px; padding:12px; background:#111318; border-radius:6px; border-left:3px solid #10B981;">
                            <strong style="color:#FFF; display:block; font-size:13px;">⚡ {news['headline']}</strong>
                            <p style="font-size:12.5px; margin:4px 0 0 0; color:#9CA3AF; line-height:1.5;">{news['summary']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Ecosystem stack empty. Click 'Poll News Ecosystem Feeds' to synchronize records.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_url:
        st.markdown('<div class="full-width-wrapper">', unsafe_allow_html=True)
        url = st.text_input("Target News / Document Article Link:", key="url_input_box", placeholder="Paste any live link here...")
        
        with st.expander("🛠️ Custom Crawler Target Overrides"):
            custom_class = st.text_input("Explicit Content CSS Selector Override Tag:", placeholder="e.g. story-element-text")
            
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
        
        min_limit, max_limit = st.slider("Synthesis Prose Word Boundaries:", 40, 300, (75, 90), key="text_slider")
        st.markdown("<br>", unsafe_allow_html=True)
        
        b_col1, b_col2 = st.columns([4, 1])
        with b_col1:
            process_text = st.button("🚀 Synthesize Textual Blocks", use_container_width=True, key="text_run_btn")
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

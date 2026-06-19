import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import langdetect
import re

# ---------------------------
# ✅ Page Config (Strictly First)
# ---------------------------
st.set_page_config(page_title="InsightInMinutes | Pro News Dashboard", page_icon="🔎", layout="wide")

# Initialize Session States
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "URL"
if "last_summary" not in st.session_state:
    st.session_state.last_summary = None
if "headline" not in st.session_state:
    st.session_state.headline = None

# ---------------------------
# 🎨 PREMIUM THEME CONFIGURATION
# ---------------------------
THEME = {
    "background_color": "#0F1115",       # Rich Slate Dark
    "card_bg": "#1A1D24",                # Charcoal Panel
    "card_border": "#2D3139",            # Modern Gray Trim
    "text_color": "#E1E4EA",             # Clean Off-White
    "accent_color": "#4F46E5",           # Electric Indigo
    "accent_hover": "#4338CA",           # Deep Indigo
    "headline_color": "#FFFFFF",         # Pure White Headline
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
}

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {THEME['background_color']};
        font-family: {THEME['font_family']};
        color: {THEME['text_color']};
    }}
    
    /* Panel Cards */
    .news-card {{
        background: {THEME['card_bg']};
        border: 1px solid {THEME['card_border']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }}
    
    /* Typography Overrides */
    h1, h2, h3, h4, h5 {{
        font-weight: 700;
        color: #FFFFFF;
    }}
    
    /* Inputs */
    .stTextArea textarea, .stTextInput>div>input {{
        background-color: {THEME['card_bg']} !important;
        border: 1px solid {THEME['card_border']} !important;
        border-radius: 8px !important;
        color: {THEME['text_color']} !important;
    }}
    .stTextArea textarea:focus, .stTextInput>div>input:focus {{
        border-color: {THEME['accent_color']} !important;
    }}
    
    /* Sidebar Layout Fixes */
    [data-testid="stSidebar"] {{
        background-color: #111318 !important;
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
        
        # Scenario 1: Custom Explicit Override CSS target rule provided by user
        if custom_class:
            paragraphs = []
            for div in soup.find_all(class_=custom_class):
                paragraphs.extend([p.get_text(strip=True) for p in div.find_all('p')])
            if paragraphs:
                return "\n".join(paragraphs), None
                
        # Scenario 2: Semi-automated known media signatures match
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

        # Scenario 3: Deep fallback heuristic (Universal Parser)
        # Drops typical boilerplate navigation clusters to map readable prose blocks on any URL link.
        for element in soup(["nav", "footer", "header", "script", "style", "aside", "form"]):
            element.decompose()
            
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True).split()) > 8]
        combined = "\n".join(paragraphs)
        
        if len(combined.split()) < 40:
            # Drop constraint checks to capture raw textual nodes safely if layout contains few paragraphs
            combined = soup.get_text(separator="\n", strip=True)
            
        return combined, None
    except Exception as e:
        return None, f"Scraping Failure: {str(e)}"

# ---------------------------
# GenAI Processing Core
# ---------------------------
def execute_summary(content, api_key, min_limit, max_limit):
    try:
        detected_lang = langdetect.detect(content)
    except Exception:
        detected_lang = "en"
        
    try:
        # Initialize the updated google-genai Client structure
        client = genai.Client(api_key=api_key)
        
        prompt = (
            f"Analyze the following textual corpus. Generate a short, informative headline "
            f"followed by a clean structured news summary within {min_limit} to {max_limit} words. "
            f"Crucial rule: Write entirely inside the {detected_lang} language space. "
            f"Format response explicitly with 'HEADLINE:' and 'SUMMARY:' prefixes to ensure proper parsing.\n\n"
            f"Corpus Content:\n{content}"
        )
        
        generate_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
            tools=[types.Tool(googleSearch=types.GoogleSearch())]
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=generate_config
        )
        
        if response and response.text:
            raw_text = response.text.strip()
            # Parsed structural extraction metrics block
            headline = "Market Insights Update"
            summary_body = raw_text
            
            if "HEADLINE:" in raw_text and "SUMMARY:" in raw_text:
                parts = raw_text.split("SUMMARY:")
                headline = parts[0].replace("HEADLINE:", "").strip()
                summary_body = parts[1].strip()
            elif "\n" in raw_text:
                split_lines = [l for l in raw_text.splitlines() if l.strip()]
                headline = split_lines[0]
                summary_body = "\n".join(split_lines[1:])
                
            return headline, summary_body, None
        return None, None, "No output delivered from inference nodes."
    except Exception as e:
        return None, None, f"AI Processing Error: {str(e)}"

# ---------------------------
# UI Presentation Layer
# ---------------------------
def render_output_dashboard():
    if st.session_state.last_summary:
        st.markdown(f"""
        <div class="news-card" style="border-left: 5px solid {THEME['accent_color']};">
            <span style="font-size:11px; text-transform:uppercase; font-weight:600; color:{THEME['accent_color']}; tracking-spacing:0.05em;">Generated Flash Headline</span>
            <h2 style="text-align:left; margin-top:4px; font-size:24px; color:{THEME['headline_color']};">{st.session_state.headline}</h2>
        </div>
        <div class="news-card">
            <span style="font-size:11px; text-transform:uppercase; font-weight:600; color:#10B981; tracking-spacing:0.05em;">Analytical Synthesis Summary</span>
            <p style="margin-top:8px; line-height:1.7; font-size:15px; color:{THEME['text_color']};">{st.session_state.last_summary}</p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------
# Base Route Views
# ---------------------------
def render_url_workspace(api_key):
    st.subheader("🌐 Universal URL Pipeline")
    url = st.text_input("Target Article Link:", placeholder="Paste any live media network link or resource page here...")
    
    with st.expander("🛠️ Advanced Extraction Configurations"):
        custom_class = st.text_input("Explicit Content CSS Selector Override (Optional):", placeholder="e.g. article-body-text-class")
        
    min_limit, max_limit = st.slider("Target Length Footprint (Words count limits):", 40, 300, (60, 140))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Process Domain Insights", use_container_width=True):
        if url.strip():
            with st.spinner("Extracting web payload components & generating insight layout..."):
                content, scrap_err = extract_universal_content(url.strip(), custom_class=custom_class.strip())
                if scrap_err:
                    st.error(scrap_err)
                elif content:
                    hd, sm, ai_err = execute_summary(content, api_key, min_limit, max_limit)
                    if ai_err:
                        st.error(ai_err)
                    else:
                        st.session_state.headline = hd
                        st.session_state.last_summary = sm
                        st.toast("Insights processing complete!", icon="✅")
        else:
            st.warning("Please supply a valid location URL link pointer.")
            
    render_output_dashboard()

def render_text_workspace(api_key):
    st.subheader("📝 Textual Matrix Pipeline")
    raw_text = st.text_area("Source Text Dropzone Block:", height=250, placeholder="Paste your transcripts, documentation, raw field files or manuscript passages directly into this block area...")
    min_limit, max_limit = st.slider("Target Length Footprint (Words count limits):", 40, 300, (60, 140))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Synthesize Textual Blocks", use_container_width=True):
        if raw_text.strip():
            with st.spinner("Executing sequence processing logic across inputs..."):
                hd, sm, ai_err = execute_summary(raw_text.strip(), api_key, min_limit, max_limit)
                if ai_err:
                    st.error(ai_err)
                else:
                    st.session_state.headline = hd
                    st.session_state.last_summary = sm
                    st.toast("Synthesis processing complete!", icon="✅")
        else:
            st.warning("Please populate the data container target with character arrays.")
            
    render_output_dashboard()

# ---------------------------
# Main Shell Framework
# ---------------------------
def main():
    api_key, api_err = read_api_key()
    
    with st.sidebar:
        st.markdown("<h2 style='text-align:left; color:#FFF; margin-bottom:0;'>🔎 InsightInMinutes</h2>", unsafe_allow_html=True)
        st.caption("Deep-Thinking Universal Core Engine")
        st.markdown("---")
        
        # Navigation Interface Block Actions
        st.markdown("### Pipeline Portals")
        if st.button("🌐 Live Domain URL Pipeline", use_container_width=True):
            st.session_state.selected_page = "URL"
            st.session_state.last_summary = None
            st.rerun()
        if st.button("📝 Raw Text Block Parser", use_container_width=True):
            st.session_state.selected_page = "TEXT"
            st.session_state.last_summary = None
            st.rerun()
            
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

    # Workspace Portal Routers
    if st.session_state.selected_page == "URL":
        render_url_workspace(api_key)
    else:
        render_text_workspace(api_key)

if __name__ == "__main__":
    main()

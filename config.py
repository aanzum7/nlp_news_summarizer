"""
InsightInMinutes - Application Configuration & Theme System
Defines visual aesthetics, color palettes, model cascades, sample outlets, and author metadata.
Kept external so .streamlit/ retains only secrets.toml.
"""

# -----------------------------------------------------------------------------
# Visual Design System & Palette (Modern Cyber-Slate Glassmorphism)
# -----------------------------------------------------------------------------
THEME = {
    # Core Surfaces
    "bg_dark": "#0B0F19",             # Deep obsidian void
    "bg_card": "#131B2E",             # Matte navy/slate card surface
    "bg_card_secondary": "#1A243B",   # Elevated card surface
    "bg_sidebar": "#0D1322",          # Dark sidebar cockpit
    "card_border": "#232F48",         # Crisp subtle border
    "card_border_glow": "rgba(99, 102, 241, 0.3)",
    
    # Typography Colors
    "text_primary": "#F8FAFC",        # Crisp white
    "text_secondary": "#94A3B8",      # Slate subtext
    "text_muted": "#64748B",          # Low-emphasis label
    
    # Accent Accords
    "primary_indigo": "#6366F1",      # Electric Indigo Brand
    "accent_cyan": "#06B6D4",         # Cyber Cyan Summary Accent
    "accent_emerald": "#10B981",      # Success & Status
    "accent_amber": "#F59E0B",        # Attention
    "accent_rose": "#F43F5E",         # Input Segment
    
    # Typography
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "mono_font": "'JetBrains Mono', 'Fira Code', monospace",
}

# -----------------------------------------------------------------------------
# Google Gemini Model Cascade Pool (Matched with anzum.ai Multi-Model Architecture)
# -----------------------------------------------------------------------------
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

GEMINI_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-pro-preview",
    "gemini-pro-latest",
    "gemini-2.5-pro",
]

# Cooldown duration in seconds before retrying a model that hit 429 quota limits
MODEL_QUOTA_COOLDOWN_SECONDS = 600

# -----------------------------------------------------------------------------
# Universal Web Scraper Targeted Selectors
# -----------------------------------------------------------------------------
SCRAPER_TARGET_PATTERNS = {
    r"prothomalo\.com": ["story-element-text"],
    r"thedailystar\.net": ["pb-20", "clearfix"],
    r"dw\.com": ["rich-text"],
    r"tbsnews\.net": ["section-content"],
    r"mzamin\.com": ["lh-base"],
    r"bbc\.(com|co\.uk)": ["article__body-content", "ssrcss-1q0x1q5-RichTextContainer"],
    r"techcrunch\.com": ["entry-content", "article-content"],
}

# -----------------------------------------------------------------------------
# Sample News Article Presets for One-Click Testing
# -----------------------------------------------------------------------------
SAMPLE_NEWS_ARTICLES = [
    {
        "label": "🇧🇩 Daily Star (Business)",
        "url": "https://www.thedailystar.net/business/economy/news/bangladesh-bank-raises-policy-rate-9-3665311",
        "outlet": "The Daily Star"
    },
    {
        "label": "🌐 DW World News",
        "url": "https://www.dw.com/en/world/s-10292",
        "outlet": "Deutsche Welle"
    },
    {
        "label": "🇧🇩 Prothom Alo (National)",
        "url": "https://en.prothomalo.com/bangladesh/national",
        "outlet": "Prothom Alo"
    },
    {
        "label": "💻 TechCrunch (AI Insights)",
        "url": "https://techcrunch.com/category/artificial-intelligence/",
        "outlet": "TechCrunch"
    }
]

# -----------------------------------------------------------------------------
# Author & Architect Metadata
# -----------------------------------------------------------------------------
AUTHOR_INFO = {
    "name": "Tanvir Anzum",
    "role": "AI & Data Researcher",
    "chips": [
        "📍 Hamburg, DE",
        "⚡ 5+ Yrs Exp",
        "🤖 RecSys & ML",
    ],
    "bio": "Passionate about turning raw news data into high-impact intelligence briefs and engineering production-grade generative AI tools.",
    "links": {
        "linkedin": "https://www.linkedin.com/in/aanzum",
        "researchgate": "https://www.researchgate.net/profile/Tanvir-Anzum",
        "github": "https://github.com/aanzum7",
    }
}

# -----------------------------------------------------------------------------
# Complete Modern Elegant CSS Injection
# -----------------------------------------------------------------------------
def get_custom_css() -> str:
    """Generates modern, elegant CSS tokens and responsive card styles."""
    css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global reset & typography */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: __BG_DARK__ !important;
        font-family: __FONT_FAMILY__;
        color: __TEXT_PRIMARY__ !important;
    }

    /* Top header bar adjustment */
    header[data-testid="stHeader"] {
        background-color: rgba(11, 15, 25, 0.85) !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid __CARD_BORDER__;
    }

    /* Sidebar Cockpit */
    [data-testid="stSidebar"] {
        background-color: __BG_SIDEBAR__ !important;
        border-right: 1px solid __CARD_BORDER__ !important;
    }

    /* Brand HUD Card */
    .brand-hud-card {
        background: linear-gradient(145deg, #131B2E 0%, #0D1424 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        margin-bottom: 18px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    .brand-hud-title {
        font-size: 22px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #A5B4FC 60%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 6px 0 !important;
        letter-spacing: -0.02em;
    }
    .brand-hud-tag {
        font-size: 11px;
        color: __ACCENT_CYAN__;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.12em;
    }

    /* Author HUD Card */
    .author-card {
        background: __BG_CARD__;
        border: 1px solid __CARD_BORDER__;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        margin-top: 14px;
    }
    .author-name {
        font-size: 17px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 2px;
    }
    .author-title {
        font-size: 12px;
        font-weight: 600;
        color: __ACCENT_CYAN__;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
    }
    .author-bio {
        font-size: 12.5px;
        color: __TEXT_SECONDARY__;
        line-height: 1.45;
        border-top: 1px solid __CARD_BORDER__;
        padding-top: 10px;
        margin-bottom: 12px;
    }
    .author-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 12px;
    }
    .chip {
        font-size: 10.5px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        background: rgba(99, 102, 241, 0.12);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.25);
    }
    .author-socials {
        display: flex;
        gap: 14px;
        border-top: 1px solid __CARD_BORDER__;
        padding-top: 10px;
    }
    .social-link {
        text-decoration: none !important;
        color: #FFFFFF !important;
        font-size: 12.5px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: color 0.2s ease;
    }
    .social-link:hover {
        color: __ACCENT_CYAN__ !important;
    }

    /* Token HUD */
    .token-container {
        background: #0B0E14;
        border: 1px solid __CARD_BORDER__;
        border-radius: 12px;
        padding: 16px;
        margin-top: 14px;
    }
    .token-bar-label {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 6px;
        color: __TEXT_SECONDARY__;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .token-legend {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        margin-bottom: 10px;
        background: rgba(255,255,255,0.02);
        padding: 6px 10px;
        border-radius: 6px;
    }
    .progress-segmented-track {
        background: #1E293B;
        border-radius: 30px;
        height: 8px;
        width: 100%;
        display: flex;
        overflow: hidden;
    }
    .token-seg-in { background: __ACCENT_ROSE__; height: 100%; transition: width 0.4s ease; box-shadow: 0 0 6px __ACCENT_ROSE__; }
    .token-seg-out { background: __ACCENT_CYAN__; height: 100%; transition: width 0.4s ease; box-shadow: 0 0 6px __ACCENT_CYAN__; }

    /* Tech Badge Pills */
    .tech-badges-wrapper {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 14px;
    }
    .tech-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.02em;
    }
    .badge-indigo {
        background: rgba(99, 102, 241, 0.12);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .badge-cyan {
        background: rgba(6, 182, 212, 0.12);
        color: #22D3EE;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }
    .badge-emerald {
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-amber {
        background: rgba(245, 158, 11, 0.12);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    /* Uniform Metric Cards - Equal Sizing (Matches Tallest Box) & Full Text Wrapping */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) {
        display: flex !important;
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) > div[data-testid="stColumn"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) > div > div {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        height: 100% !important;
    }
    div[data-testid="stMetric"] {
        background-color: __BG_CARD__ !important;
        border: 1px solid __CARD_BORDER__ !important;
        border-radius: 12px !important;
        padding: 18px 16px !important;
        min-height: 145px !important;
        height: 100% !important;
        flex: 1 1 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-sizing: border-box !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
    }
    /* Metric Label - Full text wrapping */
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetric"] label {
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
        color: __TEXT_SECONDARY__ !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 4px !important;
    }
    /* Metric Value - Full word wrapping for model names without ellipsis cutoff */
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] *,
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricValue"] span {
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
        text-overflow: clip !important;
        overflow: visible !important;
        line-height: 1.25 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        margin: 4px 0 !important;
    }
    /* Metric Delta - Full text wrapping & clean spacing */
    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] *,
    div[data-testid="stMetricDelta"] svg {
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
    }

    /* Headline & Summary Cards with Full Width & Word Wrapping */
    .headline-card-premium {
        background: __BG_CARD__;
        border: 1px solid __CARD_BORDER__;
        border-left: 5px solid __PRIMARY_INDIGO__;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 12px 30px -10px rgba(99, 102, 241, 0.2);
        width: 100% !important;
        box-sizing: border-box !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
    }
    .summary-card-premium {
        background: __BG_CARD__;
        border: 1px solid __CARD_BORDER__;
        border-left: 5px solid __ACCENT_CYAN__;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 12px 30px -10px rgba(6, 182, 212, 0.2);
        width: 100% !important;
        box-sizing: border-box !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: normal !important;
    }
    .badge-card-pill {
        font-size: 10px;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.08em;
        display: inline-block;
        margin-bottom: 8px;
        padding: 3px 10px;
        border-radius: 6px;
    }

    /* History Timeline Card */
    .history-item-card {
        background: __BG_CARD__;
        border: 1px solid __CARD_BORDER__;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 14px;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
    }

    /* Error & Alert Background Polish (Obsidian Glassmorphism) */
    div[data-testid="stAlert"] {
        background-color: rgba(19, 27, 46, 0.92) !important;
        border: 1px solid __CARD_BORDER__ !important;
        border-radius: 10px !important;
        color: #F8FAFC !important;
        box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(10px) !important;
    }
    div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
        color: #F1F5F9 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stAlert"].st-emotion-cache-12w0qpk,
    div[data-testid="stAlert"][data-test-error="true"] {
        border-left: 4px solid __ACCENT_ROSE__ !important;
    }

    /* Streamlit Widget Polish */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput>div>div>input, .stTextArea textarea {
        background-color: __BG_CARD__ !important;
        border: 1px solid __CARD_BORDER__ !important;
        border-radius: 8px !important;
        color: #F8FAFC !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea textarea:focus {
        border-color: __PRIMARY_INDIGO__ !important;
        box-shadow: 0 0 0 1px __PRIMARY_INDIGO__ !important;
    }

    /* Tab Polish */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid __CARD_BORDER__;
        padding-bottom: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        color: __TEXT_SECONDARY__ !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: __BG_CARD__ !important;
        border: 1px solid __CARD_BORDER__ !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
</style>
"""
    replacements = {
        "__BG_DARK__": THEME["bg_dark"],
        "__BG_CARD__": THEME["bg_card"],
        "__BG_SIDEBAR__": THEME["bg_sidebar"],
        "__CARD_BORDER__": THEME["card_border"],
        "__TEXT_PRIMARY__": THEME["text_primary"],
        "__TEXT_SECONDARY__": THEME["text_secondary"],
        "__PRIMARY_INDIGO__": THEME["primary_indigo"],
        "__ACCENT_CYAN__": THEME["accent_cyan"],
        "__ACCENT_ROSE__": THEME["accent_rose"],
        "__FONT_FAMILY__": THEME["font_family"],
    }
    for token, val in replacements.items():
        css = css.replace(token, val)
    return css


"""
InsightInMinutes - UI Presentation Components
Modular Streamlit interface components: Sidebar HUD, Hero Banner,
KPI Dashboard, and Tab Views.
"""

import time
from typing import Optional
import streamlit as st

from config import THEME, AUTHOR_INFO
from modules.state import clear_workspace
from modules.scraper import extract_universal_content
from modules.ai_engine import execute_summary_cascade
from modules.metrics import compute_reading_metrics
from modules.cache import generate_cache_key, get_cache
from modules.rate_limiter import get_rate_limiter


# -----------------------------------------------------------------------------
# Helper: Backward-Compatible Spacer
# -----------------------------------------------------------------------------
def add_vertical_space(size: str = "small") -> None:
    """Safe spacer compatible across all Streamlit versions (including Streamlit Cloud)."""
    if hasattr(st, "space"):
        st.space(size)
    else:
        height_map = {"small": "12px", "medium": "20px", "large": "30px"}
        px = height_map.get(size, "12px")
        st.markdown(f"<div style='margin-top: {px};'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 1. Hero Header Banner
# -----------------------------------------------------------------------------
def render_hero() -> None:
    """Renders the top branding hero with gradient typography and tech badges."""
    st.markdown("""
    <div style="padding: 4px 0 16px 0;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
            <h1 style="margin: 0; font-size: 2.3rem; font-weight: 800; letter-spacing: -0.02em; background: linear-gradient(135deg, #FFFFFF 0%, #C7D2FE 40%, #38BDF8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                InsightInMinutes
            </h1>
            <span style="background: rgba(99, 102, 241, 0.18); color: #A5B4FC; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 9999px; padding: 2px 10px; font-size: 11px; font-weight: 700; text-transform: uppercase;">
                v2.5 Pro
            </span>
        </div>
        <p style="color: #94A3B8; font-size: 1.02rem; margin: 0 0 12px 0; max-width: 800px; line-height: 1.55;">
            Enterprise-grade news synthesis powered by multi-model Gemini cascades. Transform lengthy international articles into punchy, verified intelligence briefs in seconds.
        </p>
        <div class="tech-badges-wrapper">
            <span class="tech-badge badge-indigo">🤖 Multi-Model Cascade</span>
            <span class="tech-badge badge-cyan">🌐 Universal Web Engine</span>
            <span class="tech-badge badge-emerald">⚡ Sub-Second Synthesis</span>
            <span class="tech-badge badge-amber">🌍 Multilingual Auto-Detect</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Sidebar Cockpit
# -----------------------------------------------------------------------------
def render_sidebar(api_err: Optional[str]) -> None:
    """Renders the sidebar with brand HUD, live token progress, author card, and controls."""
    with st.sidebar:
        # Brand HUD
        st.markdown(f"""
        <div class="brand-hud-card">
            <h1 class="brand-hud-title">🗞️ InsightInMinutes</h1>
            <div class="brand-hud-tag">1-Minute AI News Reader</div>
        </div>
        """, unsafe_allow_html=True)

        # Status Badges
        if api_err:
            st.markdown(":red-badge[:material/warning: API Key Missing]")
        else:
            st.markdown(
                ":green-badge[:material/check_circle: Engine Online] "
                ":blue-badge[:material/cloud: Gemini Failover Active]"
            )

        # Live Token Telemetry
        total_vol = st.session_state.token_metrics["total"]
        in_vol = st.session_state.token_metrics["input"]
        out_vol = st.session_state.token_metrics["output"]
        in_pct = (in_vol / total_vol * 100) if total_vol > 0 else 0
        out_pct = (out_vol / total_vol * 100) if total_vol > 0 else 0

        st.markdown(f"""
        <div class="token-container">
            <div class="token-bar-label">
                <span>Active Token Telemetry</span>
                <span style="color:{THEME['primary_indigo']}; font-weight:700;">{total_vol:,}</span>
            </div>
            <div class="token-legend">
                <div style="display:flex; align-items:center; gap:6px; color:#CBD5E1;">
                    <span style="color:{THEME['accent_rose']};">●</span> In ({in_vol:,})
                </div>
                <div style="display:flex; align-items:center; gap:6px; color:#CBD5E1;">
                    <span style="color:{THEME['accent_cyan']};">●</span> Out ({out_vol:,})
                </div>
            </div>
            <div class="progress-segmented-track">
                <div class="token-seg-in" style="width: {in_pct}%;"></div>
                <div class="token-seg-out" style="width: {out_pct}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Author / Architect HUD Card (Strictly 3 chips)
        chips_html = "".join([f'<span class="chip">{c}</span>' for c in AUTHOR_INFO.get("chips", [])])
        st.markdown(f"""
        <div class="author-card">
            <div class="author-name">{AUTHOR_INFO['name']}</div>
            <div class="author-title">🧬 {AUTHOR_INFO['role']}</div>
            <div class="author-chips">
                {chips_html}
            </div>
            <div class="author-bio">{AUTHOR_INFO['bio']}</div>
            <div class="author-socials">
                <a href="{AUTHOR_INFO['links']['linkedin']}" target="_blank" class="social-link">
                    <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="14" style="vertical-align:middle;">
                    LinkedIn
                </a>
                <a href="{AUTHOR_INFO['links']['researchgate']}" target="_blank" class="social-link">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/5/5e/ResearchGate_icon_SVG.svg" width="14" style="vertical-align:middle; filter: invert(1);">
                    Research
                </a>
                <a href="{AUTHOR_INFO['links']['github']}" target="_blank" class="social-link">
                    <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" width="14" style="vertical-align:middle; filter: invert(1);">
                    GitHub
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        add_vertical_space("small")
        if st.button("Clear Workspace & Cache", icon=":material/delete_sweep:", use_container_width=True):
            clear_workspace()
            get_cache().clear()
            get_rate_limiter().reset_session("user_session")
            st.toast("Workspace and cache reset successfully!", icon="🧹")
            st.rerun()


# -----------------------------------------------------------------------------
# 3. Output Synthesis Dashboard
# -----------------------------------------------------------------------------
def render_output_dashboard(model_used: Optional[str] = None, key_prefix: str = "default") -> None:
    """Renders uniform KPI cards, Flash Headline, and Analytical News Brief."""
    if not st.session_state.last_summary:
        return

    m = st.session_state.reading_metrics
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    st.subheader(":material/insights: Executive Synthesis Brief")

    # KPI Metric Cards - Uniform sizing & word-wrapped matching tallest card
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="Time Saved",
            value=m["time_saved_display"],
            delta=f"{m['compression_pct']}% compressed",
            border=True,
        )
    with m2:
        orig_mins = m.get("read_time_orig_min", round(m.get("orig_words", 0) / 220, 1))
        st.metric(
            label="Original Length",
            value=f"{m['orig_words']:,} words",
            delta=f"~{orig_mins}m read time",
            delta_color="off",
            border=True,
        )
    with m3:
        summ_sec = m.get("read_time_summary_sec", 30)
        st.metric(
            label="Summary Length",
            value=f"{m['summ_words']:,} words",
            delta=f"~{summ_sec}s read time",
            delta_color="off",
            border=True,
        )
    with m4:
        st.metric(
            label="Active Engine Node",
            value=model_used or "Gemini",
            delta="14-Cascade Fallback",
            delta_color="off",
            border=True,
        )

    # Headline Card - Full width & auto text wrapping
    st.markdown(f"""
    <div class="headline-card-premium">
        <span class="badge-card-pill" style="background: rgba(99, 102, 241, 0.15); color: #818CF8; border: 1px solid rgba(99, 102, 241, 0.3);">
            Generated Flash Headline
        </span>
        <h2 style="margin: 0; font-size: 1.4rem; font-weight: 700; color: #FFFFFF; line-height: 1.4; word-wrap: break-word; overflow-wrap: break-word;">
            {st.session_state.headline}
        </h2>
    </div>
    """, unsafe_allow_html=True)

    # Summary Body Card - Full width & auto text wrapping
    st.markdown(f"""
    <div class="summary-card-premium">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="badge-card-pill" style="background: rgba(6, 182, 212, 0.15); color: #22D3EE; border: 1px solid rgba(6, 182, 212, 0.3);">
                Analytical Intelligence Synthesis
            </span>
            <span style="font-size: 11px; color: #94A3B8;">
                Estimated Read Time: ~{m['read_time_summary_sec']}s
            </span>
        </div>
        <div style="font-size: 1rem; line-height: 1.75; color: {THEME['text_primary']}; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap;">{st.session_state.last_summary}</div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4. Tab 1: Web URL Reader
# -----------------------------------------------------------------------------
def render_url_tab(api_key: str) -> None:
    """Renders the clean, focused URL input and summarization workflow."""
    with st.container(border=True):
        st.markdown("##### :material/link: Article Source Link")

        url_input = st.text_input(
            label="Target News Article Link:",
            value=st.session_state.target_url_input,
            placeholder="Paste any article link (e.g. Daily Star, Prothom Alo, BBC, DW, TechCrunch)...",
            label_visibility="collapsed",
            key="active_url_field",
        )

        add_vertical_space("small")
        min_limit, max_limit = st.slider(
            "Synthesis Prose Word Boundaries:",
            min_value=40,
            max_value=300,
            value=(70, 95),
            key="url_slider_bounds",
        )

        btn_col1, btn_col2 = st.columns([4, 1])
        with btn_col1:
            process_url = st.button(
                "Generate 1-Minute Summary ✨",
                type="primary",
                use_container_width=True,
                icon=":material/bolt:",
                key="run_url_action",
            )
        with btn_col2:
            if st.button("Reset Input", use_container_width=True, icon=":material/refresh:", key="reset_url_field"):
                st.session_state.target_url_input = ""
                st.session_state.headline = None
                st.session_state.last_summary = None
                st.rerun()

    if process_url:
        cleaned_url = url_input.strip()
        if not cleaned_url:
            st.warning("Please paste an active news article link to begin.")
            return

        # Rate Limiting Guard
        limiter = get_rate_limiter()
        allowed, limit_msg = limiter.check_rate_limit("user_session")
        if not allowed:
            st.warning(f"⚡ {limit_msg}")
            return

        cache = get_cache()
        cache_key = generate_cache_key(cleaned_url, min_limit, max_limit)
        cached_record = cache.get(cache_key) or st.session_state.cache_vault.get(cache_key)

        if cached_record:
            st.session_state.headline = cached_record["headline"]
            st.session_state.last_summary = cached_record["summary"]
            st.session_state.model_used = f"{cached_record['model']} (Memory Cache)"
            st.session_state.reading_metrics = cached_record["metrics"]
            st.toast("Retrieved instantly from optimized cache!", icon="⚡")
        else:
            with st.status("Generating News Synthesis...", expanded=True) as status_box:
                status_box.write("🕸️ Fetching article DOM & extracting textual content...")
                try:
                    content, scrap_err = extract_universal_content(cleaned_url)
                except Exception as e:
                    content, scrap_err = None, f"Scraper exception: {str(e)}"

                if scrap_err:
                    status_box.update(label="Scraping encountered an issue", state="error", expanded=False)
                    st.warning(f"Unable to scrape article: {scrap_err}")
                elif content:
                    status_box.write("🧠 Engaging Google Gemini multi-model cascade...")
                    try:
                        hd, sm, active_model, in_tok, out_tok, ai_err = execute_summary_cascade(
                            content, api_key, min_limit, max_limit
                        )
                    except Exception as e:
                        hd, sm, active_model, in_tok, out_tok, ai_err = None, None, None, 0, 0, str(e)

                    if ai_err:
                        status_box.update(label="Inference notice", state="error", expanded=False)
                        st.warning(f"Synthesis paused: {ai_err}")
                    else:
                        status_box.update(label="Intelligence brief ready!", state="complete", expanded=False)
                        metrics = compute_reading_metrics(content, sm)
                        st.session_state.headline = hd
                        st.session_state.last_summary = sm
                        st.session_state.model_used = active_model
                        st.session_state.reading_metrics = metrics

                        # Token Telemetry update
                        st.session_state.token_metrics["input"] += in_tok
                        st.session_state.token_metrics["output"] += out_tok
                        st.session_state.token_metrics["total"] += (in_tok + out_tok)

                        record = {
                            "headline": hd,
                            "summary": sm,
                            "model": active_model,
                            "metrics": metrics,
                            "source": cleaned_url,
                            "timestamp": time.strftime("%H:%M:%S"),
                        }
                        cache.set(cache_key, record)
                        st.session_state.cache_vault[cache_key] = record
                        st.session_state.history_log.insert(0, record)
                        st.rerun()

    render_output_dashboard(st.session_state.get("model_used"), key_prefix="url")


# -----------------------------------------------------------------------------
# 5. Tab 2: Direct Text Summarizer
# -----------------------------------------------------------------------------
def render_text_tab(api_key: str) -> None:
    """Renders the direct text paste and summarization workflow."""
    with st.container(border=True):
        st.markdown("##### :material/edit_note: Raw Article or Report Text")
        raw_text = st.text_area(
            label="Direct Article Content:",
            height=220,
            placeholder="Paste news text, speech transcripts, policy briefs, or press releases here...",
            label_visibility="collapsed",
            key="raw_text_input",
        )

        add_vertical_space("small")
        t_min, t_max = st.slider(
            "Synthesis Prose Word Boundaries:",
            min_value=40,
            max_value=300,
            value=(70, 95),
            key="text_slider_bounds",
        )

        col_tb1, col_tb2 = st.columns([4, 1])
        with col_tb1:
            process_text = st.button(
                "Synthesize Text ✨",
                type="primary",
                use_container_width=True,
                icon=":material/bolt:",
                key="run_text_action",
            )
        with col_tb2:
            if st.button("Clear Text", use_container_width=True, icon=":material/backspace:", key="clear_text_field"):
                st.session_state.headline = None
                st.session_state.last_summary = None
                st.rerun()

    if process_text:
        cleaned_text = raw_text.strip()
        if not cleaned_text:
            st.warning("Please enter or paste text to summarize.")
            return
        if len(cleaned_text.split()) < 25:
            st.warning("Content is too brief (minimum 25 words required for coherent synthesis).")
            return

        # Rate Limiting Guard
        limiter = get_rate_limiter()
        allowed, limit_msg = limiter.check_rate_limit("user_session")
        if not allowed:
            st.warning(f"⚡ {limit_msg}")
            return

        cache = get_cache()
        cache_key = generate_cache_key(cleaned_text, t_min, t_max)
        cached_record = cache.get(cache_key) or st.session_state.cache_vault.get(cache_key)

        if cached_record:
            st.session_state.headline = cached_record["headline"]
            st.session_state.last_summary = cached_record["summary"]
            st.session_state.model_used = f"{cached_record['model']} (Memory Cache)"
            st.session_state.reading_metrics = cached_record["metrics"]
            st.toast("Retrieved from optimized cache!", icon="⚡")
        else:
            with st.status("Processing Text Synthesis...", expanded=True) as status_box:
                status_box.write("🧠 Engaging Gemini reasoning engine...")
                try:
                    hd, sm, active_model, in_tok, out_tok, ai_err = execute_summary_cascade(
                        cleaned_text, api_key, t_min, t_max
                    )
                except Exception as e:
                    hd, sm, active_model, in_tok, out_tok, ai_err = None, None, None, 0, 0, str(e)

                if ai_err:
                    status_box.update(label="Inference failure", state="error", expanded=False)
                    st.warning(f"Synthesis paused: {ai_err}")
                else:
                    status_box.update(label="Synthesis complete!", state="complete", expanded=False)
                    metrics = compute_reading_metrics(cleaned_text, sm)
                    st.session_state.headline = hd
                    st.session_state.last_summary = sm
                    st.session_state.model_used = active_model
                    st.session_state.reading_metrics = metrics

                    st.session_state.token_metrics["input"] += in_tok
                    st.session_state.token_metrics["output"] += out_tok
                    st.session_state.token_metrics["total"] += (in_tok + out_tok)

                    record = {
                        "headline": hd,
                        "summary": sm,
                        "model": active_model,
                        "metrics": metrics,
                        "source": "Direct Text Input",
                        "timestamp": time.strftime("%H:%M:%S"),
                    }
                    cache.set(cache_key, record)
                    st.session_state.cache_vault[cache_key] = record
                    st.session_state.history_log.insert(0, record)
                    st.rerun()

    render_output_dashboard(st.session_state.get("model_used"), key_prefix="text")


# -----------------------------------------------------------------------------
# 6. Tab 3: Session History & Telemetry (Enhanced UX)
# -----------------------------------------------------------------------------
def render_history_tab() -> None:
    """Renders comprehensive session analytics and timeline cards."""
    history = st.session_state.history_log

    if not history:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align: center; padding: 35px 20px;">
                <div style="font-size: 40px; margin-bottom: 12px;">📊</div>
                <h3 style="margin: 0 0 8px 0; color: #FFFFFF;">No Intelligence Briefs Yet</h3>
                <p style="color: #94A3B8; font-size: 14px; max-width: 480px; margin: 0 auto;">
                    Articles and reports summarized during this session will automatically appear here with full telemetry, word counts, and time-saving metrics.
                </p>
            </div>
            """, unsafe_allow_html=True)
        return

    # Cumulative Telemetry KPI Grid
    total_articles = len(history)
    total_time_saved_sec = sum(item["metrics"]["time_saved_sec"] for item in history)
    total_time_saved_mins = round(total_time_saved_sec / 60.0, 1)
    avg_compression = int(sum(item["metrics"]["compression_pct"] for item in history) / total_articles)
    total_tokens = st.session_state.token_metrics["total"]

    st.markdown("##### :material/analytics: Session Telemetry Overview")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.metric("Total Briefs", f"{total_articles}", border=True)
    with h2:
        st.metric("Total Saved", f"~{total_time_saved_mins}m", border=True)
    with h3:
        st.metric("Avg Compression", f"{avg_compression}%", border=True)
    with h4:
        st.metric("Tokens Billed", f"{total_tokens:,}", border=True)

    add_vertical_space("small")
    head_col, action_col = st.columns([4, 1])
    with head_col:
        st.markdown(f"##### :material/history: History Timeline ({total_articles} items)")
    with action_col:
        if st.button("Clear Log", icon=":material/delete:", use_container_width=True):
            st.session_state.history_log = []
            st.toast("History log cleared!", icon="🧹")
            st.rerun()

    for idx, item in enumerate(history):
        m = item["metrics"]
        st.markdown(f"""
        <div class="history-item-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #FFFFFF; line-height: 1.4;">
                    {item['headline']}
                </h3>
                <div style="display: flex; gap: 6px; flex-shrink: 0;">
                    <span class="tech-badge badge-indigo">{item['model']}</span>
                    <span class="tech-badge badge-cyan">{item['timestamp']}</span>
                </div>
            </div>
            <div style="font-size: 0.95rem; line-height: 1.65; color: #CBD5E1; margin-bottom: 12px; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap;">
                {item['summary']}
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 12px; border-top: 1px solid #232F48; padding-top: 10px; font-size: 12px; color: #94A3B8;">
                <span>📄 Original: <strong>{m['orig_words']:,} words</strong></span>
                <span>⚡ Summary: <strong>{m['summ_words']:,} words</strong></span>
                <span>⏱️ Saved: <strong>{m['time_saved_display']}</strong></span>
                <span>🌐 Source: <strong>{item['source'][:45]}...</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. Main Navigation Tabs Orchestrator
# -----------------------------------------------------------------------------
def render_main_tabs(api_key: str) -> None:
    """Orchestrates the primary tabbed interface."""
    tab_url, tab_text, tab_history = st.tabs([
        "1-Minute Web Reader 🗞️",
        "Direct Text Summarizer 📝",
        "Session History & Telemetry 📊",
    ])

    with tab_url:
        render_url_tab(api_key)

    with tab_text:
        render_text_tab(api_key)

    with tab_history:
        render_history_tab()

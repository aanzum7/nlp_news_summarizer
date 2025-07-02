import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import langdetect
from functools import lru_cache


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
            model_name="gemini-2.0-flash",
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
# Reset Only Output (Not Input)
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
# URL Summarizer (Page 1)
# ---------------------------
def url_page(api_key):
    st.title("🌐 URL Summarizer")

    url = st.text_input("Enter News URL:")

    source_mode = st.radio(
        "Source Type",
        ["Predefined Source", "Custom CSS Class"],
        horizontal=True
    )

    target_classes = []
    if source_mode == "Predefined Source":
        source = st.radio(
            "Choose Source",
            ["Daily Prothom Alo", "The Daily Star", "DW", "The Business Standard", "Daily Manab Zamin"],
            horizontal=True
        )
        target_classes_map = {
            "Daily Prothom Alo": ["story-element story-element-text"],
            "The Daily Star": ["pb-20 clearfix"],
            "DW": ["cc0m0op s1ebneao rich-text t1it8i9i r1wgtjne wgx1hx2 b1ho1h07"],
            "The Business Standard": ["section-content clearfix margin-bottom-2", "section-content margin-bottom-2"],
            "Daily Manab Zamin": ["col-sm-10 offset-sm-1 fs-5 lh-base mt-4 mb-5"],
        }
        target_classes = target_classes_map.get(source, [])
    else:
        custom_class = st.text_input("Enter CSS Class for Article Content:")
        if custom_class:
            target_classes = [custom_class]

    min_limit, max_limit = st.slider(
        "Set Summary Length Range (words):",
        50, 250, (70, 150)
    )

    if "generated_url" not in st.session_state:
        st.session_state.generated_url = False

    if not st.session_state.generated_url:
        if st.button("🚀 Generate Summary", use_container_width=True):
            if url and target_classes:
                with st.spinner("Fetching and Summarizing..."):
                    content, error = extract_content_from_url(url, target_classes)
                    if error:
                        st.error(error)
                    elif content:
                        summary, error = summarize_content(content, api_key, min_limit, max_limit)
                        if error:
                            st.error(error)
                        else:
                            st.subheader("📑 Summary & Headline")
                            st.success(summary)

                            st.session_state.generated_url = True
                            st.session_state.last_summary = summary
                            st.rerun()
                    else:
                        st.error("❌ Failed to extract content.")
            else:
                st.warning("Please enter URL and CSS Class.")
    else:
        st.subheader("📑 Summary & Headline")
        st.success(st.session_state.last_summary)

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
                    else:
                        st.error("❌ Failed to extract content.")
        with col2:
            if st.button("🏠 Home", use_container_width=True):
                reset_output("url")


# ---------------------------
# Text Summarizer (Page 2)
# ---------------------------
def text_page(api_key):
    st.title("📝 Text Summarizer")

    input_text = st.text_area("Paste Your Text Here:", height=250)

    min_limit, max_limit = st.slider(
        "Set Summary Length Range (words):",
        50, 250, (70, 150)
    )

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
                        st.subheader("📑 Summary & Headline")
                        st.success(summary)

                        st.session_state.generated_text = True
                        st.session_state.last_summary = summary
                        st.rerun()
            else:
                st.warning("Please input some text.")
    else:
        st.subheader("📑 Summary & Headline")
        st.success(st.session_state.last_summary)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("♻️ Regenerate Summary", use_container_width=True):
                with st.spinner("Regenerating..."):
                    summary, error = summarize_content(
                        input_text.strip(), api_key, min_limit, max_limit
                    )
                    if error:
                        st.error(error)
                    else:
                        st.session_state.last_summary = summary
                        st.rerun()
        with col2:
            if st.button("🏠 Home", use_container_width=True):
                reset_output("text")


# ---------------------------
# Main App with Navigation
# ---------------------------
def main():
    st.set_page_config(page_title="InsightInMinutes", layout="wide")

    # ---------------------------
    # Sidebar
    # ---------------------------
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

        page = st.radio(            
            "Navigate to:",
            ["🌐 URL Summarizer", "📝 Text Summarizer"]
        )

    api_key, error_api = read_api_key()
    if error_api:
        st.error(error_api)
        return

    if page == "🌐 URL Summarizer":
        url_page(api_key)
    else:
        text_page(api_key)


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    main()

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


# Streamlit UI
def main():
    # Display author information in the sidebar
    st.sidebar.title("About the Author")
    st.sidebar.markdown("""
        **Tanvir Anzum**  
        *Author, Data Scientist, and Machine Learning Enthusiast*  

        With a passion for leveraging technology to solve real-world problems, I specialize in building recommendation systems, data analytics, and machine learning models. Currently, I work on innovative projects in the analytics & recommendation space.

        ---

        Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/aanzum/).
        """)

    # Add "About the Project" section above the author section
    st.sidebar.title("About the Project")
    st.sidebar.markdown("""
        **InsightInMinutes: News Summarizer with AI**  
        This project aims to provide quick and accurate summaries of news articles using advanced AI. 
        It extracts content from news websites and generates summaries while preserving the original language and tone. 
        The app supports multiple news sources and allows users to input custom CSS classes for content extraction.
        """)

    # Title for the app
    st.title("InsightInMinutes: News Summarizer with AI")

    # Description
    st.write(
        """
        **Welcome to the News Summarizer!**  
        Select a news source, input a URL, and I'll fetch and summarize its content using advanced AI, keeping the tone and language consistent with the original.
        """
    )

    # Dropdown menu for selecting news source
    source = st.selectbox(
        "Select the news source:",
        ["Daily Prothom Alo", "The Daily Star", "DW", "The Business Standard", "Daily Manab Zamin",
         "Other"]
    )

    # Map source to target classes
    target_classes_map = {
        "Daily Prothom Alo": ["story-element story-element-text"],
        "The Daily Star": ["pb-20 clearfix"],
        "DW": ["cc0m0op s1ebneao rich-text t1it8i9i r1wgtjne wgx1hx2 b1ho1h07"],
        "The Business Standard": ["section-content clearfix margin-bottom-2", "section-content margin-bottom-2"],
        "Daily Manab Zamin": ["col-sm-10 offset-sm-1 fs-5 lh-base mt-4 mb-5"]
    }

    # Initialize target classes
    target_classes = target_classes_map.get(source, [])

    # Show custom CSS class input only if "Other" is selected
    if source == "Other":
        custom_class = st.text_input("Enter a custom CSS class:")
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

                        # Collect feedback after displaying the summary
                        collect_feedback()
                else:
                    st.error("Failed to extract content from the provided URL. Please check the URL or try a different source.")
        else:
            st.error("Please provide both a valid URL and API key.")


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    main()

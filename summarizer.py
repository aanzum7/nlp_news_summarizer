import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import langdetect
from functools import lru_cache

# Function to fetch and parse data from a URL
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

        combined_paragraph = "\n".join(paragraphs)
        if not combined_paragraph or len(combined_paragraph.split()) < 50:
            return None, "Extracted content is too short or invalid."
        return combined_paragraph, None
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {e}"
    except Exception as e:
        return None, f"Error fetching content: {e}"

# Function to read the API key
def read_api_key():
    try:
        return st.secrets["genai"]["api_key"], None
    except KeyError:
        return None, "API key is not configured in secrets."

# Caching to optimize API calls
@lru_cache(maxsize=10)
def summarize_content(content, api_key):
    try:
        language = langdetect.detect(content)
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel("gemini-1.5-flash", generation_config={
            "temperature": 0.5,
            "top_p": 0.9,
            "max_output_tokens": 2000,
        })

        chat_session = model.start_chat()
        prompt = (
            f"You are a journalist summarizing news in {language}. "
            "Summarize the following content in its original language, "
            "preserving its tone and accuracy. "
            "Provide a headline separately that best emphasizes the core message.\n\n"
            f"{content}"
        )
        
        response = chat_session.send_message(prompt)
        return response.text.strip() if response and response.text else None, "No response generated."
    except Exception as e:
        return None, f"Error summarizing content: {e}"

# Function to collect user feedback
def collect_feedback():
    st.subheader("Feedback")
    feedback = st.radio("Rate the summary:", ["👍", "👎"], index=None, key="feedback_rating")
    comments = st.text_area("Additional comments (optional):", key="feedback_comments")
    
    if st.button("Submit Feedback"):
        if feedback:
            print(f"Feedback: {feedback}, Comments: {comments}")
            st.success("Thank you for your feedback!")
            st.session_state.feedback_rating = None
            st.session_state.feedback_comments = ""
        else:
            st.warning("Please select a rating before submitting.")

# Streamlit UI
def main():
    st.sidebar.title("About the Project")
    st.sidebar.markdown(
        """
        **InsightInMinutes: AI News Summarizer**
        This tool extracts and summarizes news articles in their original language while maintaining tone and accuracy.
        """
    )

    st.sidebar.title("About the Author")
    st.sidebar.markdown(
        """
        **Tanvir Anzum**  
        Data Scientist & Machine Learning Enthusiast
        [LinkedIn](https://www.linkedin.com/in/aanzum/)
        """
    )

    st.title("InsightInMinutes: AI News Summarizer")
    st.write("Enter a news URL, and I'll summarize it while keeping its original tone and language.")
    
    source = st.selectbox("Select the news source:", [
        "Daily Prothom Alo", "The Daily Star", "DW", "The Business Standard", "Daily Manab Zamin", "Other"
    ])
    
    target_classes_map = {
        "Daily Prothom Alo": ["story-element story-element-text"],
        "The Daily Star": ["pb-20 clearfix"],
        "DW": ["cc0m0op s1ebneao rich-text t1it8i9i r1wgtjne wgx1hx2 b1ho1h07"],
        "The Business Standard": ["section-content clearfix margin-bottom-2", "section-content margin-bottom-2"],
        "Daily Manab Zamin": ["col-sm-10 offset-sm-1 fs-5 lh-base mt-4 mb-5"]
    }
    target_classes = target_classes_map.get(source, [])

    if source == "Other":
        custom_class = st.text_input("Enter a custom CSS class:")
        if custom_class:
            target_classes = [custom_class]
    
    url = st.text_input("Enter the URL of the news article:")
    api_key, error = read_api_key()
    if error:
        st.error(error)
        return
    
    if st.button("Summarize"):
        if url and api_key:
            with st.spinner("Fetching and summarizing content..."):
                content, error = extract_content_from_url(url, target_classes)
                if error:
                    st.error(f"Error: {error}. Check the URL or try a different source.")
                elif content:
                    summary, error = summarize_content(content, api_key)
                    if error:
                        st.error(f"Error: {error}. Please try again.")
                    else:
                        st.subheader("News Summary:")
                        st.write(summary)
                        collect_feedback()
                else:
                    st.error("Failed to extract content. Check the URL or try another source.")
        else:
            st.error("Provide both a valid URL and API key.")

if __name__ == "__main__":
    main()

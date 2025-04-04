import streamlit as st  # type: ignore
import requests
from bs4 import BeautifulSoup  # type: ignore
import google.generativeai as genai  # type: ignore
import langdetect  # type: ignore
from functools import lru_cache  # For caching API responses


# Function to fetch and parse data from a URL
def extract_content_from_url(url, target_classes):
    try:
        # Fetch the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad HTTP status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        paragraphs = []
        # Iterate through all target classes
        for target_class in target_classes:
            paragraphs.extend(
                p.get_text(strip=True)
                for div in soup.find_all('div', class_=target_class)
                for p in div.find_all('p')
            )

        # Combine paragraphs into a single string
        combined_paragraph = "\n".join(paragraphs)
        if not combined_paragraph or len(combined_paragraph.split()) < 50:  # Check for valid content
            return None, "The extracted content is too short or invalid. Please check the URL or the class configuration."
        return combined_paragraph, None

    except requests.exceptions.RequestException as e:
        return None, f"Network error: {e}"
    except Exception as e:
        return None, f"Error fetching content: {e}"


# Function to read the API key from Streamlit secrets
def read_api_key():
    try:
        api_key = st.secrets["genai"]["api_key"]
        return api_key, None  # Return the API key and no error
    except KeyError:
        return None, "API key is not configured in secrets."


# Cache the summarization function to reduce latency
@lru_cache(maxsize=10)
def summarize_content(content, api_key):
    try:
        # Detect the language of the input content
        language = langdetect.detect(content)

        # Configure Generative AI with the API key
        genai.configure(api_key=api_key)

        # Set generation parameters
        generation_config = {
            "temperature": 0.5,  # Lower temperature for factual consistency
            "top_p": 0.9,
            "max_output_tokens": 1200,  # Enough space for detailed content
        }

        # Create the model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config
        )

        # Start a new chat session for each request
        chat_session = model.start_chat()  # Ensure a new chat session is started each time

        # Enhanced prompt for preserving original language and generating both summary and title
        prompt = (
            f"You are a journalist tasked with summarizing news in {language}. "
            "Summarize the following content accurately in the same language as the input, "
            "without translating or changing the tone. "
            "Also, provide a headline in the same language that best emphasizes the core message of the news:\n\n"
            f"{content}"
        )

        # Send the prompt to the model
        response = chat_session.send_message(prompt)

        if response and response.text:
            # Return both summary and headline
            return response.text.strip(), None
        else:
            return None, "No response generated."

    except Exception as e:
        return None, f"Error summarizing content: {e}"


# Function to collect user feedback
def collect_feedback():
    st.subheader("Feedback")
    feedback = st.radio(
        "How would you rate the summary?",
        options=["👍", "👎"],
        index=None,  # No default selection
        key="feedback_rating",  # Unique key for the radio button
    )
    comments = st.text_area("Additional comments (optional):", key="feedback_comments")

    # Add a submit button for feedback
    if st.button("Submit Feedback"):
        if feedback:
            # Print feedback to the console
            print(f"Feedback: {feedback}, Comments: {comments}")
            st.success("Thank you for your feedback!")
            # Reset the feedback form
            st.session_state.feedback_rating = None
            st.session_state.feedback_comments = ""
        else:
            st.warning("Please select a rating before submitting.")


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

    # Input for the news URL
    url = st.text_input("Enter the URL of the news article:")

    # Read the API key from the config file
    api_key, error = read_api_key()
    if error:  # Check if an error occurred
        st.error(error)
        return

    if st.button("Summarize"):
        if url and api_key:
            with st.spinner("Fetching and summarizing content..."):
                content, error = extract_content_from_url(url, target_classes)
                if error:
                    st.error(f"Error: {error}. Please check the URL or try a different source.")
                elif content:
                    summary, error = summarize_content(content, api_key)
                    if error:
                        st.error(f"Error: {error}. Please try again.")
                    else:
                        st.subheader("News Summary:")
                        st.write(summary)

                        # Collect feedback after displaying the summary
                        collect_feedback()
                else:
                    st.error("Failed to extract content from the provided URL. Please check the URL or try a different source.")
        else:
            st.error("Please provide both a valid URL and API key.")


if __name__ == "__main__":
    main()

Here's a sample `README.md` file you can use for your project. This README provides an overview of the project, installation instructions, usage, and other relevant details.

```markdown
# News Summarizer

A Streamlit-based web application that fetches, summarizes, and provides headlines for news articles. The app uses the Generative AI model to generate accurate summaries while maintaining the original tone and language of the content.

## Features
- Extracts content from a provided URL.
- Summarizes the content in the same language as the source.
- Generates a headline for the summarized content.
- Allows users to select different news sources for content extraction.
- Supports custom CSS class configuration for unsupported news sources.

## Prerequisites

Before running the app, ensure you have the following:

- Python 3.7 or higher
- `pip` (Python package installer)
- A valid **Generative AI API key** (e.g., for Gemini)

## Installation

### 1. Clone the repository:
```bash
git clone https://github.com/your-username/news-summarizer.git
cd news-summarizer
```

### 2. Set up a Python virtual environment (optional but recommended):
```bash
python -m venv venv
```

### 3. Activate the virtual environment:
- On Windows:
  ```bash
  venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 4. Install dependencies:
```bash
pip install -r requirements.txt
```

### 5. Add your API key:
- Create a folder named `.streamlit` in the root of the project if it doesn't exist.
- Inside the `.streamlit` folder, create a `secrets.toml` file with the following structure:

```toml
[genai]
api_key = "your_actual_api_key"
```

> **Note**: Do not upload your `secrets.toml` file to any public repositories to keep your API key secure.

### 6. Run the app:
```bash
streamlit run summarizer.py
```

This will start the Streamlit app and open it in your default web browser.

## Usage

1. **Select a News Source**: Choose from pre-configured news sources (e.g., Daily Prothom Alo, The Daily Star, etc.), or provide a custom CSS class if the source is unsupported.
2. **Enter the URL**: Provide the URL of a news article you'd like to summarize.
3. **Click "Summarize"**: The app will fetch the content, generate a summary, and display it on the page.

## Customization

- **Adding New News Sources**: To add a new news source, add the target CSS class for the content extraction in the `target_classes_map` dictionary in the code.
- **Adjusting Summarization Settings**: You can customize the generation settings like temperature, max tokens, etc., within the `summarize_content` function.

## Dependencies

This project uses the following Python libraries:

- `streamlit`: Framework for creating web apps.
- `requests`: For fetching the web page content.
- `BeautifulSoup4`: For parsing HTML and extracting content.
- `google.generativeai`: Google’s Generative AI API for summarization.
- `langdetect`: For detecting the language of the content.

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

## Troubleshooting

- **API Key Issues**: Ensure that your `secrets.toml` is correctly configured and placed inside the `.streamlit` folder.
- **No content extracted**: If the app is unable to extract content from the URL, verify that the target classes are correctly set for the news source.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

### Notes:
- Replace the GitHub link with your own repository URL.
- Add more specific troubleshooting or feature-related sections as needed.

Let me know if you'd like me to adjust the README further!
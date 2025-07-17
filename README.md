# Excel Chat Assistant (Mistral 7B API)

A Streamlit app that lets you upload an Excel file and ask questions in natural language. The app uses the Mistral 7B API to generate Python code for data analysis and visualization.

## Features

- Upload Excel files
- Ask questions (math, stats, groupings, filters, plots)
- Get answers as text, tables, or charts

## Setup

1. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

2. Get your Mistral API key from [Mistral AI](https://console.mistral.ai/).

3. Create a `.env` file in the project root with your API key:
    ```
    MISTRAL_API_KEY=your-key-here
    ```
4. Run the app:
    ```
    streamlit run app.py
    ```

## Security

This app executes LLM-generated code. For production, consider sandboxing or code validation.

---

Powered by [Mistral 7B API](https://docs.mistral.ai/api/) and [Streamlit](https://streamlit.io/). 
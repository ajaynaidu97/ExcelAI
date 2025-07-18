import streamlit as st
import pandas as pd
from llm_api import query_mistral_api
from utils import extract_code
from code_executor import execute_code
import uuid
import os
from PIL import Image
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for safe chart generation

st.set_page_config(page_title="Excel Chat Assistant", layout="wide")
st.markdown("""
    <style>
    .stApp {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }
    .bottom-form-container {
        margin-top: auto;
        position: sticky;
        bottom: 0;
        background: white;
        z-index: 100;
        padding-top: 1em;
        padding-bottom: 1em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Excel Chat Assistant (Mistral 7B API)")
st.write("Upload an Excel file and ask questions in natural language. Get answers as text, tables, or charts!")

# Ensure charts directory exists
CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

# File upload
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.session_state['df'] = df
    st.write("Preview of your data:")
    st.dataframe(df.head())
else:
    st.info("Please upload an Excel file to get started.")
    st.stop()

# Chat history: store tuples (user_question, assistant_answer, answer_type, answer_data, code)
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

chat_history = st.session_state["chat_history"]

# Input at the bottom using a sticky container (rendered first)
st.markdown('<div class="bottom-form-container">', unsafe_allow_html=True)
with st.form(key="question_form", clear_on_submit=True):
    user_question = st.text_input("Ask a question about your data:", key="question_input")
    ask_clicked = st.form_submit_button("Ask")

    if ask_clicked and user_question:
        with st.spinner("Thinking..."):
            columns = ', '.join(df.columns)
            sample_rows = df.head(3).to_dict(orient='records')
            chart_filename = os.path.join(CHARTS_DIR, f"chart_{uuid.uuid4().hex}.png")
            chart_filename = chart_filename.replace("\\", "/")  # Ensure forward slashes for matplotlib
            prompt = (
                "You are a Python data analyst. Given a pandas DataFrame called df, "
                f"whose columns are: {columns}. Here are some sample rows:\n{sample_rows}\n"
                "When answering the following question, if the column names in the question do not exactly match, "
                "infer the most relevant columns based on their meaning and the context of the question. "
                "Write Python code to answer the question. "
                "Always assign the final answer to a variable named result. "
                "If the question is about counts, distributions, or frequencies, always generate and save a bar chart using matplotlib, and do not just return the value counts as text. "
                "Always call methods with parentheses (e.g., use count() not count) and assign the result to the variable result. "
                "When using pandas str.contains, always set na=False to avoid errors with missing values. "
                "Always handle missing (NaN) values explicitly in your code. For example, use na=False in string operations, dropna() or fillna() as appropriate in filters and aggregations. "
                f"If a chart is needed, use matplotlib and save the figure to '{chart_filename}'.\n"
                "Return ONLY the Python code in a single code block, with no explanation or comments.\n"
                f"Question: {user_question}\n"
                "Python code:"
            )
            try:
                llm_response = query_mistral_api(prompt)
                code = extract_code(llm_response)
                code = code.replace('chart.png', chart_filename)
                output_text, result_var, chart_generated, error = execute_code(code, st.session_state['df'])

                if error:
                    # Fallback: if error is about NA / NaN, show a user-friendly message
                    if 'NA / NaN' in error or 'missing values' in error:
                        answer_type = "text"
                        answer = "Error: Your data contains missing (NaN) values. Please check your data or rephrase your question to handle missing values."
                        answer_data = None
                    else:
                        answer_type = "text"
                        answer = f"Error executing code:\n{error}"
                        answer_data = None
                elif chart_generated and os.path.exists(chart_filename):
                    answer_type = "chart"
                    answer = "[Chart produced below]"
                    answer_data = chart_filename
                elif result_var is not None:
                    import types
                    if isinstance(result_var, types.MethodType):
                        result_var = result_var()
                    if isinstance(result_var, pd.DataFrame):
                        answer_type = "table"
                        answer = "[Table produced below]"
                        answer_data = result_var
                    elif isinstance(result_var, pd.Series):
                        lowered = user_question.lower()
                        if any(word in lowered for word in ["plot", "chart", "graph", "bar", "histogram", "line"]):
                            import matplotlib.pyplot as plt
                            plt.figure(figsize=(10, 6))
                            result_var.plot(kind='bar')
                            plt.title('Bar Chart of Result')
                            plt.tight_layout()
                            plt.savefig(chart_filename)
                            plt.close()
                            answer_type = "chart"
                            answer = "[Chart produced below]"
                            answer_data = chart_filename
                        else:
                            answer_type = "text"
                            answer = str(result_var)
                            answer_data = None
                    else:
                        answer_type = "text"
                        answer = str(result_var)
                        answer_data = None
                elif output_text.strip():
                    answer_type = "text"
                    answer = output_text
                    answer_data = None
                else:
                    lowered = user_question.lower()
                    if any(word in lowered for word in ["plot", "chart", "graph", "bar", "histogram", "line"]):
                        answer_type = "chart"
                        import glob
                        png_files = sorted(glob.glob(os.path.join(CHARTS_DIR, '*.png')), key=os.path.getmtime, reverse=True)
                        if png_files:
                            answer = "[Most recent chart produced below]"
                            answer_data = png_files[0]
                        else:
                            answer = "No chart was produced, but a chart was requested. Please check your column names or try rephrasing."
                            answer_data = None
                    else:
                        answer_type = "text"
                        answer = f"No output generated. Available columns: {list(df.columns)}"
                        answer_data = None

                st.session_state["chat_history"].append((user_question, answer, answer_type, answer_data, code))
            except Exception as e:
                st.session_state["chat_history"].append((user_question, f"Error: {e}", "text", None, ""))

st.markdown('</div>', unsafe_allow_html=True)

# Now render the chat history after processing the form, so the new answer is immediately visible
with st.container():
    # Most recent Q&A
    if chat_history:
        st.markdown("---")
        st.subheader("Most Recent Exchange")
        q, a, a_type, a_data, code = chat_history[-1]
        st.markdown(f"**You:** {q}")
        if a_type == "text":
            st.markdown(f"**Assistant:** {a}")
        elif a_type == "table":
            st.markdown(f"**Assistant:**")
            st.dataframe(a_data)
        elif a_type == "chart":
            st.markdown(f"**Assistant:**")
            if a_data is not None:
                st.image(a_data)
            else:
                st.write("No chart file was produced.")

    # Previous chat history
    if len(chat_history) > 1:
        st.markdown("---")
        st.subheader("Previous Chat History")
        for q, a, a_type, a_data, code in chat_history[:-1]:
            st.markdown(f"**You:** {q}")
            if a_type == "text":
                st.markdown(f"**Assistant:** {a}")
            elif a_type == "table":
                st.markdown(f"**Assistant:**")
                st.dataframe(a_data)
            elif a_type == "chart":
                st.markdown(f"**Assistant:**")
                if a_data is not None:
                    st.image(a_data)
                else:
                    st.write("No chart file was produced.")

st.markdown("---")
st.caption("Powered by Mistral 7B API and Streamlit")

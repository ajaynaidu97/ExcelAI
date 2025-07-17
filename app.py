import streamlit as st
import pandas as pd
from llm_api import query_mistral_api
from utils import extract_code
from code_executor import execute_code

st.set_page_config(page_title="Excel Chat Assistant", layout="wide")
st.title("Excel Chat Assistant (Mistral 7B API)")
st.write("Upload an Excel file and ask questions in natural language. Get answers as text, tables, or charts!")

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

# Chat history: store tuples (user_question, assistant_answer, answer_type, answer_data)
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

chat_history = st.session_state["chat_history"]

# Layout: Chat history (except most recent), then most recent Q&A, then input at the bottom
with st.container():
    if len(chat_history) > 1:
        st.markdown("---")
        st.subheader("Previous Chat History")
        for q, a, a_type, a_data in chat_history[:-1]:
            st.markdown(f"**You:** {q}")
            if a_type == "text":
                st.markdown(f"**Assistant:** {a}")
            elif a_type == "table":
                st.markdown(f"**Assistant:**")
                st.dataframe(a_data)
            elif a_type == "chart":
                st.markdown(f"**Assistant:**")
                st.image(a_data)

# Most recent Q&A
if chat_history:
    st.markdown("---")
    st.subheader("Most Recent Exchange")
    q, a, a_type, a_data = chat_history[-1]
    st.markdown(f"**You:** {q}")
    if a_type == "text":
        st.markdown(f"**Assistant:** {a}")
    elif a_type == "table":
        st.markdown(f"**Assistant:**")
        st.dataframe(a_data)
    elif a_type == "chart":
        st.markdown(f"**Assistant:**")
        st.image(a_data)

# Spacer to push input to bottom
st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)

# Input at the bottom
with st.container():
    user_question = st.text_input("Ask a question about your data:", key="question_input")
    ask_clicked = st.button("Ask", key="ask_button")

if ask_clicked and user_question:
    with st.spinner("Thinking..."):
        prompt = (
            "You are a Python data analyst. Given a pandas DataFrame called df, "
            "write Python code to answer the following question. "
            "If a chart is needed, use matplotlib and save the figure to 'chart.png'.\n"
            f"Question: {user_question}\n"
            "Python code:"
        )
        try:
            llm_response = query_mistral_api(prompt)
            code = extract_code(llm_response)
            output_text, result_var, chart_generated, error = execute_code(code, st.session_state['df'])

            # Decide answer type and data
            if error:
                answer_type = "text"
                answer = f"Error executing code:\n{error}"
                answer_data = None
            elif chart_generated:
                answer_type = "chart"
                answer = "[Chart produced below]"
                answer_data = "chart.png"
            elif result_var is not None:
                if isinstance(result_var, pd.DataFrame):
                    answer_type = "table"
                    answer = "[Table produced below]"
                    answer_data = result_var
                else:
                    answer_type = "text"
                    answer = str(result_var)
                    answer_data = None
            elif output_text.strip():
                answer_type = "text"
                answer = output_text
                answer_data = None
            else:
                answer_type = "text"
                answer = "No output generated."
                answer_data = None

            st.session_state["chat_history"].append((user_question, answer, answer_type, answer_data))
        except Exception as e:
            st.session_state["chat_history"].append((user_question, f"Error: {e}", "text", None))

st.markdown("---")
st.caption("Powered by Mistral 7B API and Streamlit") 
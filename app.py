import streamlit as st
import pdfplumber
import docx
import pandas as pd
from openai import OpenAI
import os

# ===========================
# Load OpenAI API Key
# ===========================
# 1️⃣ Load from Streamlit secrets or fallback to environment variable
os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["api_key"]

# 2️⃣ Initialize OpenAI client
client = OpenAI()

# ===========================
# Page Config
# ===========================
st.set_page_config(
    page_title="AI Research Assistant",
    layout="wide",
)

# ===========================
# Initialize Session State
# ===========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""

# ===========================
# Sidebar - File Upload
# ===========================
st.sidebar.header("📂 Upload Document")
uploaded_file = st.sidebar.file_uploader(
    "Choose PDF, DOCX, or XLSX",
    type=["pdf", "docx", "xlsx"]
)

# ===========================
# File Parsing Logic
# ===========================
def extract_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
        text = df.to_string(index=False)
    return text

if uploaded_file:
    extracted_text = extract_text(uploaded_file)
    st.session_state.doc_text = extracted_text
    st.sidebar.success(f"✅ {uploaded_file.name} uploaded & parsed!")
    st.sidebar.write("**Preview:**")
    st.sidebar.write(extracted_text[:300] + " ...")

# ===========================
# GPT helper
# ===========================
def call_gpt(prompt, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful research assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# ===========================
# Main Title
# ===========================
st.title("📚 AI Research Assistant")
st.caption("Chat with your research documents!")

st.markdown("---")

# ===========================
# Chat History
# ===========================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# ===========================
# Chat Input
# ===========================
user_input = st.chat_input("Ask a question, request a summary, or get topic suggestions...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if not st.session_state.doc_text:
        response = "⚠️ *Please upload a document first!*"
    else:
        # Decide action based on user input
        if "summary" in user_input.lower():
            prompt = f"Please provide a clear summary of this document:\n\n{st.session_state.doc_text[:4000]}"
        elif "topic" in user_input.lower():
            prompt = f"Suggest 5 unique research topics based on this document:\n\n{st.session_state.doc_text[:4000]}"
        else:
            prompt = f"Answer this question based only on the document:\n\nDocument:\n{st.session_state.doc_text[:4000]}\n\nQuestion: {user_input}"

        response = call_gpt(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

# ===========================
# Footer
# ===========================
st.markdown("---")
st.caption("🚀 Built with ❤️ using Streamlit & OpenAI | v3.0")


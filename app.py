import streamlit as st
import pdfplumber
import docx
import pandas as pd
import requests
import json

# ============================
# 📂 File Extraction Logic
# ============================

def extract_text(uploaded_file):
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
        text = df.to_string(index=False)
    return text.strip()

# ============================
# 🤖 Ask LLaMA API
# ============================

def ask_llama_stream(question, context):
    if len(context) > 4000:
        context = context[:4000]

    prompt = f"""You are an expert research assistant.
Answer clearly, concisely, and only using the provided context.
If you don't know, say "I don't know".

Context:
{context}

Question:
{question}

Answer:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "model": "tinyllama",  # ✅ RAM-friendly
            "prompt": prompt,
            "stream": True
        }),
        stream=True
    )

    if response.status_code != 200:
        yield "❌ Error talking to LLaMA."
        return

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            token = data.get("response", "")
            yield token

# ============================
# 🎨 Page & UI Setup
# ============================

st.set_page_config(page_title="📄 Research PDF Chatbot", layout="wide")

st.markdown("""
<style>
/* Global page dark theme */
body {
  background-color: #111827;
  color: #e5e7eb;
  font-family: 'Segoe UI', sans-serif;
}

.sidebar .sidebar-content {
  background-color: #1f2937;
}

.block-container {
  padding-top: 2rem;
}

/* Chat bubbles */
.chat-container {
  max-height: 70vh;
  overflow-y: auto;
  padding: 1rem;
  border-radius: 12px;
  background-color: #1f2937;
  border: 1px solid #374151;
}

.message {
  padding: 0.85rem 1rem;
  border-radius: 12px;
  margin: 0.75rem 0;
  line-height: 1.6;
  max-width: 90%;
  word-wrap: break-word;
}

.user-message {
  background-color: #2563eb;
  color: white;
  margin-left: auto;
  text-align: right;
}

.bot-message {
  background-color: #374151;
  color: #f9fafb;
  margin-right: auto;
  text-align: left;
}

textarea, input[type="text"] {
  background-color: #111827 !important;
  color: #f9fafb !important;
  border-radius: 8px;
  border: 1px solid #4b5563;
  padding: 0.65rem 1rem;
}

button[kind="primary"] {
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
}

button:hover {
  background-color: #1d4ed8;
}

.stButton>button {
  background-color: #2563eb;
  color: #fff;
  border-radius: 8px;
  padding: 0.5rem 1rem;
}

.stButton>button:hover {
  background-color: #1d4ed8;
}

.stDownloadButton>button {
  background-color: #4b5563;
  color: #f9fafb;
  border-radius: 6px;
}

.stDownloadButton>button:hover {
  background-color: #374151;
}

.stTextInput>div>div>input {
  background-color: #111827;
  color: #f9fafb;
}

.sidebar .block-container {
  background-color: #1f2937;
}

.stSidebar {
  background-color: #1f2937;
}
</style>
""", unsafe_allow_html=True)


# ============================
# 🗃️ Session State Init
# ============================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "all_chats" not in st.session_state:
    st.session_state.all_chats = []

if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# ============================
# 📑 Sidebar
# ============================

with st.sidebar:
    st.title("📄 PDF Research Chatbot")

    uploaded_file = st.file_uploader("📤 Upload PDF, DOCX, XLSX", type=["pdf", "docx", "xlsx"])

    if uploaded_file:
        st.success(f"✅ Uploaded: {uploaded_file.name}")

    if st.button("🆕 New Chat"):
        if st.session_state.chat_history:
            st.session_state.all_chats.append(st.session_state.chat_history.copy())
        st.session_state.chat_history = []
        st.session_state.clear_input = True
        st.experimental_rerun()


    if st.button("🗑️ Clear All Chats"):
        st.session_state.chat_history = []
        st.session_state.all_chats = []
        st.session_state.clear_input = True
        st.experimental_rerun()


    if uploaded_file:
        text = extract_text(uploaded_file)
        st.download_button(
            "⬇️ Download Extracted Text",
            data=text,
            file_name="extracted_text.txt",
            mime="text/plain"
        )

    if st.session_state.all_chats:
        st.markdown("### 🕓 Previous Chats")
    for i, chat in enumerate(reversed(st.session_state.all_chats[-3:]), 1):
        chat_idx = len(st.session_state.all_chats) - i
        st.markdown(f"**Chat {chat_idx+1}**")
        for role, msg in chat[-2:]:
            icon = "🙋" if role == "user" else "🤖"
            st.markdown(f"- {icon} {msg[:70]}{'...' if len(msg) > 70 else ''}")
        if st.button(f"🔄 Load Chat {chat_idx+1}"):
            st.session_state.chat_history = chat.copy()
            st.experimental_rerun()


# ============================
# 💬 Main Chat Area
# ============================

if uploaded_file:
    text = extract_text(uploaded_file)

    st.markdown("### 💬 Chat History")
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for role, msg in st.session_state.chat_history:
        css_class = "user-message" if role == "user" else "bot-message"
        st.markdown(f'<div class="message {css_class}">{msg}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.clear_input:
        st.session_state["question_input"] = ""
        st.session_state.clear_input = False

    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([6, 1])
        user_input = cols[0].text_input(
            "Ask from the PDF...", key="question_input",
            label_visibility="collapsed", placeholder="Type your question..."
        )
        submitted = cols[1].form_submit_button("Send")

    if submitted and user_input.strip():
        st.session_state.chat_history.append(("user", user_input.strip()))
        with st.spinner("🤖 Thinking..."):
            streamed_answer = ""
            response_placeholder = st.empty()
            for token in ask_llama_stream(user_input.strip(), context=text[:4000]):
                streamed_answer += token
                response_placeholder.markdown(
                    f'<div class="message bot-message">{streamed_answer}▌</div>',
                    unsafe_allow_html=True
                )
            st.session_state.chat_history.append(("bot", streamed_answer.strip()))
        st.experimental_rerun()


    # Regenerate
    if st.session_state.chat_history:
        last_question = None
        for role, msg in reversed(st.session_state.chat_history):
            if role == "user":
                last_question = msg
                break
        if last_question:
            if st.button("🔄 Regenerate Last Answer"):
                with st.spinner("♻️ Regenerating..."):
                    streamed_answer = ""
                    response_placeholder = st.empty()
                    for token in ask_llama_stream(last_question, context=text[:4000]):
                        streamed_answer += token
                        response_placeholder.markdown(
                            f'<div class="message bot-message">{streamed_answer}▌</div>',
                            unsafe_allow_html=True
                        )
                    st.session_state.chat_history.append(("bot", streamed_answer.strip()))
                st.experimental_rerun()


    # Download chat history
    if st.session_state.chat_history:
        chat_text = "\n\n".join(
            f"{'🙋 User:' if role == 'user' else '🤖 Bot:'} {msg}"
            for role, msg in st.session_state.chat_history
        )
        st.download_button(
            "💾 Download Chat",
            data=chat_text,
            file_name="chat_history.txt",
            mime="text/plain",
        )

else:
    st.info("📄 Upload a PDF, DOCX, or XLSX from the sidebar to begin.")

import streamlit as st
import pdfplumber
import requests
import json

# --- PDF Extraction ---
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

# --- Ask LLaMA API ---
def ask_llama3_stream(question, context):
    prompt = f"""You are a concise and helpful assistant like ChatGpt.
Answer the question clearly using the context.

Context:
{context}

Question:
{question}

Answer:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "model": "phi3",  # or llama3 or mistral
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

# --- Page Setup ---
st.set_page_config(page_title="📄 PDF Chat", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
.chat-container {
    max-height: 65vh;
    overflow-y: auto;
    padding: 1rem;
    border-radius: 10px;
    background-color: #f8fafc;
    border: 1px solid #ddd;
}
.message {
    padding: 0.75rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    line-height: 1.5;
}
.user-message {
    background-color: #dbeafe;
    color: #1e3a8a;
    text-align: right;
}
.bot-message {
    background-color: #e2e8f0;
    color: #111827;
    text-align: left;
}
textarea, input[type="text"] {
    background-color: #f0f4f8 !important;
    border-radius: 8px;
    border: 1px solid #ccc;
    padding: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# --- Session State Init ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "all_chats" not in st.session_state:
    st.session_state.all_chats = []

if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# --- Sidebar ---
with st.sidebar:
    st.title("📄 PDF Chatbot")
    uploaded_file = st.file_uploader("📤 Upload PDF", type="pdf")

    if st.button("🆕 New Chat"):
        if st.session_state.chat_history:
            st.session_state.all_chats.append(st.session_state.chat_history.copy())
        st.session_state.chat_history = []
        st.session_state.clear_input = True
        st.experimental_rerun()

    if st.session_state.all_chats:
        st.markdown("### 🕓 Previous Chats")
        for i, chat in enumerate(reversed(st.session_state.all_chats[-3:]), 1):
            st.markdown(f"**Chat {len(st.session_state.all_chats)-i+1}**")
            for role, msg in chat[-2:]:
                icon = "🙋" if role == "user" else "🤖"
                st.markdown(f"- {icon} {msg[:70]}{'...' if len(msg) > 70 else ''}")

# --- Main App ---
if uploaded_file:
    text = extract_text_from_pdf(uploaded_file)

    # --- Chat Display ---
    st.markdown("### 💬 Chat History")
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for role, msg in st.session_state.chat_history:
        css_class = "user-message" if role == "user" else "bot-message"
        st.markdown(f'<div class="message {css_class}">{msg}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Clear previous input ---
    if st.session_state.clear_input:
        st.session_state["question_input"] = ""
        st.session_state.clear_input = False

    # --- Chat Input UI with Button ---
    with st.form(key="chat_form", clear_on_submit=True):
        cols = st.columns([6, 1])
        user_input = cols[0].text_input("Ask from the PDF...", key="question_input", label_visibility="collapsed", placeholder="Type your question...")
        submitted = cols[1].form_submit_button("Send")

    if submitted and user_input.strip():
        st.session_state.chat_history.append(("user", user_input.strip()))
        with st.spinner("🤖 Thinking..."):
            streamed_answer = ""
            response_placeholder = st.empty()
            for token in ask_llama3_stream(user_input.strip(), context=text[:1500]):
                streamed_answer += token
                response_placeholder.markdown(f'<div class="message bot-message">{streamed_answer}▌</div>', unsafe_allow_html=True)

            st.session_state.chat_history.append(("bot", streamed_answer.strip()))
        st.rerun()

else:
    st.info("📄 Upload a PDF from the sidebar to begin.")

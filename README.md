# 📄 AI PDF Research Chatbot

A **local, privacy-friendly AI research assistant** to help you:
- 📂 Upload PDF, DOCX, or XLSX files
- 🤖 Ask questions about the document
- ✨ Get quick summaries
- 🧠 Suggest research topics
- 💬 All powered by a **local LLM** — no OpenAI API required!

---

## ⚡️ Features

✅ Upload **PDF, DOCX, XLSX**  
✅ Extract and display text  
✅ Ask any question from the document  
✅ Get summaries or topic suggestions  
✅ Save and load **previous chats**  
✅ 100% **offline** — runs on your own laptop with **Ollama**

---

## 🚀 How to Run

### 1️⃣ Install Python dependencies

```bash
pip install -r requirements.txt

2️⃣ Install Ollama
👉 Download Ollama and install it for your OS.

Then pull a small model:
ollama pull tinyllama

3️⃣ Start Ollama server
Open a terminal and run:
ollama serve
OR just run:
ollama run tinyllama
This starts your local LLM API on localhost:11434.

4️⃣ Start the chatbot
Open a new terminal and run:

streamlit run app.py
Visit: http://localhost:8501

✅ Upload your PDF
✅ Ask your questions
✅ Enjoy your private AI research assistant!

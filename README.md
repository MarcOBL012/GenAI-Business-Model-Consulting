# 🚀 AI Business Model Consultant

An AI-based business assistant and consultant that runs **100% locally and portably**. This project uses a RAG (Retrieval-Augmented Generation) system to analyze PDF documents and help users model their businesses, including the automatic generation of diagrams (mindmaps and Canvas) using Mermaid code.

This project was developed by **Marco Obispo - UNI - Sistemas Analiticos**.



## 🌟 Main Features

* **100% Local and Private Execution:** By using GPT4All models (and optionally Ollama), your data and documents never leave your computer.
* **Desktop Interface (GUI):** Thanks to `pywebview`, the FastAPI-based web system renders as a native desktop application.
* **RAG (Retrieval-Augmented Generation) System:** Allows uploading `.pdf` files directly from the interface so the AI can read them, index them in a vector database (ChromaDB), and answer questions based on your own commercial or academic information.
* **Visual Generation of Models:** The system prompt is configured to structure business ideas and generate diagrams using `Mermaid` syntax (Canvas/Mind maps).
* **Automatic Model Download:** If you don't have the language models downloaded, the main application (`app.py`) automatically downloads `Llama-3.2-1B-Instruct-Q4_0.gguf` and the embeddings `all-MiniLM-L6-v2.gguf2.f16.gguf` on its first run.



## 🛠️ Technologies Used

* **Backend:** Python, FastAPI, and Uvicorn.
* **AI and NLP:** LangChain, GPT4All, and Ollama (optional in the secondary script).
* **Vector Database:** ChromaDB.
* **Document Processing:** `PyPDFLoader`, `PyPDFDirectoryLoader`, `RecursiveCharacterTextSplitter`.
* **Frontend:** HTML5, CSS3, `marked.min.js` (for rendering Markdown), and `mermaid.min.js` (for diagrams).
* **Desktop Wrapper:** `pywebview`.



## ⚙️ Prerequisites

Make sure you have Python installed on your system.

## 🚀 Installation and Usage

**1. Clone the repository and navigate to the project folder:**
```bash
git clone <repository-url>
cd genai-business-model-consulting
```
**2. Install dependencies:**
It is recommended to create a virtual environment first.
```Bash
pip install -r requirements.txt
```
**3. Run the Main Application:**

```Bash
python app.py
```
Note: The first time you run the application, it will take a few extra minutes while it downloads the language and embedding models into the models folder. Once completed, a desktop window with the chatbot interface will open.

## 📂 Project Structure

`app.py`: Main file that starts the FastAPI server, initializes the RAG system with GPT4All, handles PDF uploads, and opens the desktop window with pywebview.

`rag_local.py`: Alternative console script showing how to implement the same RAG system but using Ollama (llama3 and nomic-embed-text).

`requirements.txt`: List of project dependencies.

`static/`: Contains the graphical user interface files (index.html, style.css, script.js, and minified libraries to work completely offline).

`chroma_db/`: Directory (automatically generated) where the vector database persistence is stored with your PDF information.

`models/`: Directory (automatically generated) where downloaded .gguf models are saved.

## 💡 How to use the tool
1. Start a conversation: Greet the assistant or ask a direct question about business models, strategies, or action plans.

2. Generate a diagram: Ask the assistant to "create a canvas for my business" or "draw a mind map of suppliers". The system will generate the Mermaid diagram on the screen automatically.

3. Upload your documents: Click the paperclip icon 📎 to attach PDF files. Once processed, the system will use the document's information to provide more accurate and personalized answers based on your file.

## 📬 Contact
If you use or extend this project, please add a note in the README or contact:

Marco Obispo — marco.obispo.l@uni.pe

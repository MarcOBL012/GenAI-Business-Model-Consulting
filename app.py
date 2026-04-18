import os
import sys
import threading
import uvicorn
import re
import traceback
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
from pydantic import BaseModel
import webview
from datetime import datetime
from contextlib import asynccontextmanager

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# LangChain Imports
from langchain_community.document_loaders import PyPDFDirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.llms import GPT4All
from langchain_community.embeddings import GPT4AllEmbeddings
from gpt4all import GPT4All as NativeGPT4All
from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Cuando se corre desde el .exe empaquetado, los archivos están en sys._MEIPASS
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

base_path = get_base_path()

# Directorio de persistencia para ChromaDB (donde el usuario puede añadir más)
CHROMA_PERSIST_DIR = os.path.join(os.getcwd(), "chroma_db")
# Directorio de base de datos pre-construida (empaquetada en el EXE)
BUNDLED_CHROMA_DIR = os.path.join(base_path, "chroma_db")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar RAG cuando inicie el servidor FastAPI
    threading.Thread(target=initialize_rag, daemon=True).start()
    yield

app = FastAPI(title="MODELO NEGOCIOS IA", lifespan=lifespan)

# Global references
rag_chain = None
vectorstore = None

class ChatRequest(BaseModel):
    query: str
def initialize_rag():
    global rag_chain, vectorstore
    try:
        log("[RAG] Inicializando sistema RAG local 100% portable...")
        
        # Descarga automática de modelos si no existen
        model_dir = os.path.join(base_path, "models")
        os.makedirs(model_dir, exist_ok=True)
        
        llm_model_name = "Llama-3.2-1B-Instruct-Q4_0.gguf"
        llm_path = os.path.join(model_dir, llm_model_name)
        
        if not os.path.exists(llm_path):
            log(f"[RAG] Descargando modelo: {llm_model_name}...")
            NativeGPT4All.download_model(llm_model_name, model_path=model_dir)
            
        embed_model_name = "all-MiniLM-L6-v2.gguf2.f16.gguf"
        embed_path = os.path.join(model_dir, embed_model_name)
        if not os.path.exists(embed_path):
            log(f"[RAG] Descargando embedding: {embed_model_name}...")
            NativeGPT4All.download_model(embed_model_name, model_path=model_dir)

        log("[RAG] Cargando Embeddings...")
        embeddings = GPT4AllEmbeddings(
            model_name=embed_model_name,
            gpt4all_kwargs={'allow_download': False, 'model_path': model_dir}
        )
        
        target_db = None
        if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
            log("[RAG] Cargando Base de Datos local del usuario...")
            target_db = CHROMA_PERSIST_DIR
        elif os.path.exists(BUNDLED_CHROMA_DIR) and os.listdir(BUNDLED_CHROMA_DIR):
            log("[RAG] Cargando Base de Datos pre-construida (Súper Portable)...")
            target_db = BUNDLED_CHROMA_DIR

        if target_db:
            vectorstore = Chroma(persist_directory=target_db, embedding_function=embeddings)
        else:
            log("[RAG] No se encontró DB. Buscando PDFs para indexar...")
            loader = PyPDFDirectoryLoader(".")
            documentos = loader.load()
            
            if documentos:
                log(f"[RAG] Procesando {len(documentos)} páginas...")
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                fragmentos = text_splitter.split_documents(documentos)
                vectorstore = Chroma.from_documents(
                    documents=fragmentos, 
                    embedding=embeddings,
                    persist_directory=CHROMA_PERSIST_DIR
                )
            else:
                log("[RAG] No se encontraron PDFs. Creando base de datos vacía.")
                vectorstore = Chroma.from_texts(
                    texts=["Este es un chatbot de negocios."], 
                    embedding=embeddings,
                    persist_directory=CHROMA_PERSIST_DIR
                )

        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        log("[RAG] Configurando Modelo de Lenguaje...")
        llm = GPT4All(
            model=llm_path,
            max_tokens=2048,
            n_predict=2048,
            temp=0.4,
            repeat_penalty=1.18,
            stop=["<|eot_id|>", "<|reserved_special_token"]
        )

        system_prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
            "Eres un Consultor de Negocios de IA.\n"
            "Regla 1: Usa tu conocimiento general para responder. El 'Contexto' es solo un apoyo adicional.\n"
            "Regla 2: Si el usuario te saluda ('hola'), responde con un saludo amable y corto.\n"
            "Regla 3: Si el usuario te pide un Canvas o diagrama de negocios, usa SIEMPRE este formato exacto de código:\n\n"
            "```mermaid\n"
            "mindmap\n"
            "  root((Mi Negocio))\n"
            "    Asociaciones\n"
            "      Proveedores\n"
            "```\n\n"
            "Asegúrate de escribir el código `mermaid` completo y correcto.\n\n"
            "Contexto:\n{context}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
            "{input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        )
        prompt = PromptTemplate.from_template(system_prompt)

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        log("[RAG] ¡SISTEMA LISTO!")
    except Exception as e:
        log(f"[ERROR] Error crítico en inicialización: {str(e)}")
        traceback.print_exc()

@app.get("/api/status")
def get_status():
    if rag_chain is None:
        return {"status": "initializing"}
    return {"status": "ready"}

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if rag_chain is None:
        return {"error": "El sistema RAG todavía se está inicializando. Por favor, espera unos momentos."}
    
    try:
        respuesta = rag_chain.invoke({"input": req.query})
        
        # Limpiar cualquier etiqueta robótica o token especial de Llama 3 que se haya filtrado
        clean_answer = re.sub(r"<\|.*?\|>", "", respuesta["answer"]).strip()
        
        return {"answer": clean_answer}
    except Exception as e:
        return {"error": f"Error durante la consulta: {str(e)}"}

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global vectorstore
    if vectorstore is None:
        return {"error": "El sistema se está inicializando, espera un momento."}
    
    if not file.filename.endswith(".pdf"):
        return {"error": "Solo se permiten archivos PDF."}
        
    file_location = f"./{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        loader = PyPDFLoader(file_location)
        nuevos_docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        nuevos_frag = text_splitter.split_documents(nuevos_docs)
        
        vectorstore.add_documents(nuevos_frag)
        
        return {"message": f"¡PDF '{file.filename}' agregado a mi base de conocimientos!"}
    except Exception as e:
        return {"error": f"Error al procesar el PDF: {str(e)}"}

# Servir archivos estáticos (interfaz web)
# La ruta "/" devolverá el index.html
static_dir = os.path.join(base_path, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def get_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    # Iniciar el servidor FastAPI en un hilo separado
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Crear la ventana nativa tipo 'exe' con pywebview
    # Apuntamos a la URL donde corre nuestro FastAPI
    window = webview.create_window(
        'MODELO NEGOCIOS IA', 
        'http://127.0.0.1:8000',
        width=1000,
        height=800,
        min_size=(600, 500),
        text_select=True
    )
    
    # Iniciar el loop de la interfaz gráfica
    webview.start()

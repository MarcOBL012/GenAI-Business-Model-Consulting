import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv


# Cargar variables del archivo .env
load_dotenv()

def crear_sistema_rag():
    """
    Inicializa y configura el sistema RAG completamente local.
    """
    
    # 1. Carga de datos
    # Utilizamos PyPDFLoader para extraer el texto de un archivo PDF local.
    # El archivo "documento.pdf" debe existir en la misma ruta donde se ejecuta el script.
    print("Cargando el documento PDF...")
    loader = PyPDFLoader("documento.pdf")
    documentos = loader.load()

    # 2. Chunking (División de texto)
    # Dividimos los documentos grandes en fragmentos más pequeños para que 
    # se ajusten a la ventana de contexto del LLM y mejorar la precisión de búsqueda.
    print("Dividiendo el texto en fragmentos (chunking)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    fragmentos = text_splitter.split_documents(documentos)

    # 3. Embeddings Locales
    # Usamos OllamaEmbeddings con el modelo nomic-embed-text para convertir los 
    # fragmentos de texto en vectores numéricos 100%. Todo ocurre localmente.
    print("Inicializando embeddings locales (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # 4. Base de Datos Vectorial
    # Almacenamos los vectores en una instancia de Chroma en memoria. 
    # Esto servirá como motor de búsqueda semántica.
    print("Creando base de datos vectorial Chroma en memoria...")
    vectorstore = Chroma.from_documents(documents=fragmentos, embedding=embeddings)
    
    # Configuramos el recuperador (retriever) para extraer la información relevante.
    retriever = vectorstore.as_retriever()

    # 5. LLM Local
    # Usamos ChatOllama para conectarnos al modelo llama3 local. 
    # Usamos temperature=0 para que las respuestas sean deterministas, precisas y evitar alucinaciones.
    print("Configurando LLM local (llama3)...")
    llm = ChatOllama(model="llama3", temperature=0)

    # 6. Prompt Engineering
    # Diseñamos un prompt específico que instruye al modelo a utilizar estrictamente el contexto.
    system_prompt = (
        "Eres un asistente útil que responde preguntas basadas únicamente en el contexto proporcionado. "
        "Si no sabes la respuesta o la información no se encuentra en el contexto, debes decir "
        "estrictamente: 'No tengo esa información'. No inventes respuestas.\n\n"
        "Contexto:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 7. Cadenas (Chains)
    # Creamos una cadena para combinar los documentos recuperados pasándolos al prompt y al LLM.
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    
    # Creamos la cadena RAG completa, la cual primero recupera documentos y luego genera la respuesta.
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain


if __name__ == "__main__":
    print("--- Sistema RAG Local con LangChain y Ollama ---")
    
    # Verificamos si el archivo PDF existe antes de intentar cargarlo
    if not os.path.exists("documento.pdf"):
        print("\n[ERROR] No se encontró el archivo 'documento.pdf' en el directorio actual.")
        print("Por favor, coloca un archivo PDF con ese nombre en la misma carpeta e intenta de nuevo.")
    else:
        try:
            # Inicializamos el sistema RAG
            cadena_rag = crear_sistema_rag()
            
            # Pregunta de prueba
            pregunta = "¿Cuál es el tema principal del documento?"
            print(f"\n[Usuario]: {pregunta}")
            
            # Ejecutamos la consulta pasándole la pregunta de prueba
            respuesta = cadena_rag.invoke({"input": pregunta})
            
            # Printeamos la respuesta generada por el LLM en la consola
            print(f"\n[Asistente]: {respuesta['answer']}")
            
        except Exception as e:
            print(f"\n[ERROR] Ocurrió un error durante la ejecución: {e}")

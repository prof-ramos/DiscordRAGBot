import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

DATA_DIR = "data"
INDEX_DIR = "vectorstore"

def load_documents():
    """Carrega todos os PDFs da pasta data/"""
    print("[INFO] Carregando documentos...")
    
    if not os.path.exists(DATA_DIR):
        print(f"[❌] Diretório '{DATA_DIR}' não encontrado!")
        print(f"[💡] Crie a pasta '{DATA_DIR}' e adicione seus arquivos PDF.")
        return []
    
    pdf_files = list(Path(DATA_DIR).glob("*.pdf"))
    
    if not pdf_files:
        print(f"[❌] Nenhum arquivo PDF encontrado em '{DATA_DIR}'")
        print(f"[💡] Adicione arquivos .pdf na pasta '{DATA_DIR}'")
        return []
    
    print(f"[✅] Encontrados {len(pdf_files)} arquivos PDF")
    
    loader = DirectoryLoader(
        DATA_DIR,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True
    )
    
    documents = loader.load()
    print(f"[✅] {len(documents)} páginas carregadas")
    
    return documents


def split_documents(documents):
    """Divide documentos em chunks menores"""
    print("[INFO] Dividindo documentos em chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"[✅] {len(chunks)} chunks criados")
    
    return chunks


def create_embeddings():
    """Cria modelo de embeddings usando OpenAI API"""
    print("[INFO] Configurando OpenAI embeddings...")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY não encontrada no .env")
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )
    
    print("[✅] OpenAI embeddings configurado")
    return embeddings


def create_vectorstore(chunks, embeddings):
    """Cria e salva Chroma vectorstore"""
    print("[INFO] Criando vectorstore Chroma...")
    print("[⏳] Isso pode levar alguns minutos...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=INDEX_DIR
    )
    
    print(f"[✅] Vectorstore salvo em '{INDEX_DIR}'")
    
    return vectorstore


def main():
    """Pipeline completo de indexação"""
    print("\n" + "="*60)
    print("🚀 INDEXAÇÃO DE DOCUMENTOS - RAG PT-BR")
    print("="*60 + "\n")
    
    documents = load_documents()
    
    if not documents:
        print("\n[❌] Processo interrompido: nenhum documento para indexar")
        return
    
    chunks = split_documents(documents)
    
    if not chunks:
        print("\n[❌] Processo interrompido: nenhum chunk criado")
        return
    
    embeddings = create_embeddings()
    
    vectorstore = create_vectorstore(chunks, embeddings)
    
    num_vectors = len(chunks)
    
    print("\n" + "="*60)
    print("✅ INDEXAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*60)
    print(f"📊 Total de vetores: {num_vectors}")
    print(f"📁 Localização: {INDEX_DIR}/")
    print("\n💡 Próximo passo: Execute 'python bot.py' para iniciar o bot")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PDF Ingestion Script for Knowledge Base
Ingere PDFs na base de conhecimento com controle de duplicatas.
"""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pypdf import PdfReader
import tiktoken
from tiktoken.core import Encoding
from openai import OpenAI
from supabase import create_client, Client

# ============================================================
# Configuração básica
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY não definido.")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não definidos.")

# Cliente OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# Utilitários
# ============================================================

def calculate_file_hash(file_path: str) -> str:
    """Calcula SHA256 hash do arquivo para detectar mudanças."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_tokenizer(model: str = EMBEDDING_MODEL) -> Encoding:
    """Retorna um tokenizer compatível com o modelo de embedding.

    Args:
        model: Nome do modelo de embedding

    Returns:
        Encoding do tiktoken
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return enc


def count_tokens(text: str, tokenizer: Encoding) -> int:
    """Conta tokens em um texto.

    Args:
        text: Texto para contar tokens
        tokenizer: Tokenizer tiktoken

    Returns:
        Número de tokens
    """
    return len(tokenizer.encode(text))


def chunk_text(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
    tokenizer: Optional[Encoding] = None
) -> List[Dict[str, Any]]:
    """
    Divide o texto em chunks de até max_tokens, com overlap entre eles.
    Retorna uma lista de dicts: { "content": str, "token_count": int, "index": int }

    Args:
        text: Texto a ser dividido em chunks
        max_tokens: Tamanho máximo de cada chunk em tokens
        overlap_tokens: Número de tokens de overlap entre chunks
        tokenizer: Tokenizer a ser usado (opcional)

    Returns:
        Lista de dicts com content, token_count e index

    Raises:
        ValueError: Se overlap_tokens >= max_tokens
    """
    if tokenizer is None:
        tokenizer = get_tokenizer()

    # CRITICAL: Prevenir infinite loop validando overlap
    if overlap_tokens >= max_tokens:
        raise ValueError(
            f"overlap_tokens ({overlap_tokens}) must be less than max_tokens ({max_tokens}). "
            f"Recommended: overlap_tokens <= max_tokens * 0.2"
        )

    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    idx = 0

    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text_str = tokenizer.decode(chunk_tokens)
        chunks.append({
            "index": idx,
            "content": chunk_text_str,
            "token_count": len(chunk_tokens)
        })
        idx += 1
        start = end - overlap_tokens
        if start >= len(tokens):
            break

    return chunks


# ============================================================
# Leitura de PDF
# ============================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrai texto de todas as páginas do PDF."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text)

    if not pages_text:
        raise RuntimeError(f"❌ Nenhum texto extraído do PDF: {pdf_path}")

    full_text = "\n\n".join(pages_text)
    return full_text


# ============================================================
# OpenAI Embeddings (com retry)
# ============================================================

def get_embedding(text: str, model: str = EMBEDDING_MODEL, max_retries: int = 3) -> List[float]:
    """Gera embedding com retry em caso de falha transiente.

    Args:
        text: Texto para gerar embedding
        model: Modelo de embedding a usar
        max_retries: Número máximo de tentativas

    Returns:
        Lista de floats representando o embedding (nunca None)

    Raises:
        RuntimeError: Se todas as tentativas falharem ou embedding for inválido
    """
    text = text.replace("\n", " ").strip()

    if not text:
        raise ValueError("❌ Texto vazio fornecido para geração de embedding")

    for attempt in range(max_retries):
        try:
            response = openai_client.embeddings.create(
                input=[text],
                model=model
            )

            # CRITICAL: Validar resposta antes de retornar
            if not response or not response.data or len(response.data) == 0:
                raise ValueError("❌ Resposta da API OpenAI vazia ou inválida")

            embedding = response.data[0].embedding

            if embedding is None:
                raise ValueError("❌ API OpenAI retornou embedding=None")

            if not isinstance(embedding, list) or len(embedding) == 0:
                raise ValueError(
                    f"❌ Embedding inválido: esperado lista não-vazia, "
                    f"recebido {type(embedding).__name__}"
                )

            return embedding

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️  Erro ao gerar embedding (tentativa {attempt + 1}/{max_retries}): {e}")
                print(f"   Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(
                    f"❌ Falha ao gerar embedding após {max_retries} tentativas: {e}\n"
                    f"   Texto (primeiros 100 chars): {text[:100]}..."
                )


# ============================================================
# Supabase – inserção nas tabelas kb_*
# ============================================================

def get_or_create_collection(
    name: str, description: str = "", metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Retorna o id da collection. Se não existir, cria."""
    metadata = metadata or {}

    res = supabase.table("kb_collections") \
                  .select("*") \
                  .eq("name", name) \
                  .limit(1) \
                  .execute()

    if res.data:
        print(f"✅ Coleção '{name}' encontrada (id: {res.data[0]['id']})")
        return res.data[0]["id"]

    print(f"✨ Criando nova coleção '{name}'...")
    insert_res = supabase.table("kb_collections").insert({
        "name": name,
        "description": description,
        "metadata": metadata
    }).execute()

    if not insert_res.data:
        raise RuntimeError("❌ Falha ao criar kb_collections.")

    print(f"✅ Coleção criada (id: {insert_res.data[0]['id']})")
    return insert_res.data[0]["id"]


def find_existing_document(
    collection_id: str,
    external_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Retorna o documento existente (se houver) para a combinação
    (collection_id, external_id).
    """
    res = (
        supabase.table("kb_documents")
        .select("id, title, is_indexed, content_hash, metadata")
        .eq("collection_id", collection_id)
        .eq("external_id", external_id)
        .limit(1)
        .execute()
    )

    if res.data:
        return res.data[0]
    return None


def create_document(
    collection_id: str,
    title: str,
    doc_type: str = "pdf",
    source_url: Optional[str] = None,
    external_id: Optional[str] = None,
    content_hash: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Cria um novo documento na base."""
    metadata = metadata or {}

    insert_res = supabase.table("kb_documents").insert({
        "collection_id": collection_id,
        "title": title,
        "doc_type": doc_type,
        "source_url": source_url,
        "external_id": external_id,
        "content_hash": content_hash,
        "metadata": metadata,
        "is_active": True,
        "is_indexed": False,
    }).execute()

    if not insert_res.data:
        raise RuntimeError("❌ Falha ao criar kb_documents.")

    return insert_res.data[0]["id"]


def insert_chunks(
    document_id: str,
    chunks: List[Dict[str, Any]],
    batch_size: int = 10,
) -> None:
    """Insere chunks na tabela kb_chunks (com embedding).

    Raises:
        RuntimeError: Se qualquer embedding falhar ou for None
        ValueError: Se embeddings inválidos forem detectados
    """
    total_chunks = len(chunks)
    print(f"💾 Inserindo {total_chunks} chunks em lotes de {batch_size}...")

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        rows = []

        for ch in batch:
            content = ch["content"]
            token_count = ch["token_count"]
            index = ch["index"]

            # Gera embedding com retry automático
            try:
                embedding = get_embedding(content)
            except Exception as e:
                raise RuntimeError(
                    f"❌ Falha crítica ao gerar embedding para chunk {index}: {e}\n"
                    f"   Documento não será marcado como indexado."
                )

            # CRITICAL: Validar que embedding foi gerado com sucesso
            if embedding is None:
                raise ValueError(
                    f"❌ Embedding retornou None para chunk {index}.\n"
                    f"   Isso pode indicar rate-limit ou erro silencioso da OpenAI.\n"
                    f"   Documento não será marcado como indexado."
                )

            if not isinstance(embedding, list) or len(embedding) == 0:
                raise ValueError(
                    f"❌ Embedding inválido para chunk {index}: "
                    f"esperado lista não-vazia, recebido {type(embedding).__name__}.\n"
                    f"   Documento não será marcado como indexado."
                )

            rows.append({
                "document_id": document_id,
                "chunk_index": index,
                "content": content,
                "token_count": token_count,
                "embedding": embedding,
                "metadata": {},
            })

        insert_res = supabase.table("kb_chunks").insert(rows).execute()

        if insert_res.error:
            raise RuntimeError(f"❌ Erro ao inserir chunks (lote {i // batch_size + 1}): {insert_res.error}")

        print(f"   ✅ Lote {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size} inserido ({len(rows)} chunks)")


def mark_document_indexed(document_id: str, content_hash: str, total_chunks: int) -> None:
    """Marca documento como indexado e atualiza metadata."""
    existing = supabase.table("kb_documents").select("metadata").eq("id", document_id).single().execute()
    current_meta = existing.data.get("metadata", {}) if existing.data else {}

    supabase.table("kb_documents") \
            .update({
                "is_indexed": True,
                "content_hash": content_hash,
                "indexed_at": "now()",
                "metadata": {
                    **current_meta,
                    "total_chunks": total_chunks,
                    "embedding_model": EMBEDDING_MODEL,
                }
            }) \
            .eq("id", document_id) \
            .execute()


# ============================================================
# Função principal de ingestão
# ============================================================

def ingest_pdf(
    pdf_path: str,
    collection_name: str,
    collection_description: Optional[str] = None,
    document_title: Optional[str] = None,
    document_type: str = "pdf",
    document_metadata: Optional[Dict[str, Any]] = None,
    chunk_max_tokens: int = 500,
    chunk_overlap_tokens: int = 50,
    force_reindex: bool = False,
) -> str:
    """Ingere PDF na base de conhecimento com controle de duplicatas."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"❌ PDF não encontrado: {pdf_path}")

    external_id = os.path.abspath(pdf_path)

    print(f"🔍 Calculando hash do arquivo...")
    file_hash = calculate_file_hash(pdf_path)
    print(f"   Hash: {file_hash[:16]}...")

    print(f"📄 Lendo PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    print(f"   ✅ {len(text)} caracteres extraídos")

    print("✂️  Gerando chunks...")
    tokenizer = get_tokenizer()
    chunks = chunk_text(
        text,
        max_tokens=chunk_max_tokens,
        overlap_tokens=chunk_overlap_tokens,
        tokenizer=tokenizer
    )
    print(f"   ✅ {len(chunks)} chunks gerados")

    coll_desc = collection_description or f"Coleção gerada automaticamente para {collection_name}"
    collection_id = get_or_create_collection(
        name=collection_name,
        description=coll_desc,
        metadata={}
    )

    existing_doc = find_existing_document(collection_id, external_id)

    should_reindex = False
    document_id = None

    if existing_doc:
        document_id = existing_doc["id"]
        existing_hash = existing_doc.get("content_hash")
        is_indexed = existing_doc.get("is_indexed", False)

        if is_indexed and existing_hash == file_hash and not force_reindex:
            print(f"✅ Documento já indexado e sem alterações. Pulando ingestão.")
            print(f"   Document ID: {document_id}")
            print(f"   Título: {existing_doc['title']}")
            return document_id

        elif is_indexed and existing_hash != file_hash:
            print(f"⚠️  Arquivo modificado detectado!")
            print(f"   Hash antigo: {existing_hash[:16] if existing_hash else 'N/A'}...")
            print(f"   Hash novo:   {file_hash[:16]}...")
            should_reindex = True

        elif not is_indexed:
            print(f"⚠️  Documento existente não indexado completamente. Reprocessando.")
            should_reindex = True

        elif force_reindex:
            print(f"🔄 Reindexação forçada solicitada.")
            should_reindex = True

        if should_reindex:
            print(f"🗑️  Apagando chunks antigos (document_id={document_id})...")
            delete_res = supabase.table("kb_chunks").delete().eq("document_id", document_id).execute()
            chunks_deleted = len(delete_res.data) if delete_res.data else 0
            print(f"   ✅ {chunks_deleted} chunks removidos")
    else:
        print("✨ Criando novo documento...")
        title = document_title or os.path.basename(pdf_path)
        doc_meta = document_metadata or {}
        document_id = create_document(
            collection_id=collection_id,
            title=title,
            doc_type=document_type,
            source_url=None,
            external_id=external_id,
            content_hash=file_hash,
            metadata=doc_meta
        )
        print(f"   ✅ Documento criado (id: {document_id})")

    # CRITICAL: Só marcar como indexado se TODOS os embeddings forem gerados com sucesso
    try:
        insert_chunks(document_id, chunks)
    except (RuntimeError, ValueError) as e:
        print(f"\n❌ ERRO CRÍTICO durante geração de embeddings:")
        print(f"   {e}")
        print(f"\n⚠️  Documento NÃO foi marcado como indexado (is_indexed=False)")
        print(f"   Chunks podem estar parcialmente inseridos no banco.")
        print(f"   Para reprocessar, execute novamente com o mesmo PDF.")
        print(f"   Document ID: {document_id}")
        raise  # Re-raise para interromper execução

    print("✅ Marcando documento como indexado...")
    mark_document_indexed(document_id, file_hash, len(chunks))

    print(f"\n🎉 Ingestão concluída com sucesso!")
    print(f"   Document ID: {document_id}")
    print(f"   Total de chunks: {len(chunks)}")
    print(f"   Modelo de embedding: {EMBEDDING_MODEL}")

    return document_id


# ============================================================
# CLI
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingestão de PDF para Supabase (RAG) com controle de duplicatas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Indexar PDF básico
  python ingest_pdf.py --pdf ./materiais/lei_8112.pdf --collection "INSS 2024"

  # Indexar com metadata customizada
  python ingest_pdf.py \\
    --pdf ./materiais/lei_8112.pdf \\
    --collection "INSS 2024" \\
    --title "Lei 8.112/90 Atualizada" \\
    --doc-type "lei" \\
    --metadata '{"materia": "Dir. Administrativo", "banca": "CESPE"}'

  # Forçar reindexação
  python ingest_pdf.py --pdf ./materiais/lei_8112.pdf --collection "INSS 2024" --force
        """
    )

    parser.add_argument("--pdf", required=True, help="Caminho do arquivo PDF.")
    parser.add_argument("--collection", required=True, help="Nome da coleção (kb_collections.name).")
    parser.add_argument("--collection-description", default=None, help="Descrição da coleção.")
    parser.add_argument("--title", default=None, help="Título do documento (padrão: nome do arquivo).")
    parser.add_argument("--doc-type", default="pdf", help="Tipo do documento (ex.: 'lei', 'apostila').")
    parser.add_argument(
        "--metadata",
        default=None,
        help='Metadados do documento em JSON (ex.: \'{"materia": "Dir. Adm", "banca": "CESPE"}\')'
    )
    parser.add_argument("--chunk-max-tokens", type=int, default=500, help="Tamanho máximo de tokens por chunk.")
    parser.add_argument("--chunk-overlap-tokens", type=int, default=50, help="Overlap de tokens entre chunks.")
    parser.add_argument("--force", action="store_true", help="Forçar reindexação mesmo se já indexado.")

    args = parser.parse_args()

    doc_metadata = None
    if args.metadata:
        try:
            doc_metadata = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear metadata JSON: {e}")
            return 1

    try:
        ingest_pdf(
            pdf_path=args.pdf,
            collection_name=args.collection,
            collection_description=args.collection_description,
            document_title=args.title,
            document_type=args.doc_type,
            document_metadata=doc_metadata,
            chunk_max_tokens=args.chunk_max_tokens,
            chunk_overlap_tokens=args.chunk_overlap_tokens,
            force_reindex=args.force
        )
        return 0
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

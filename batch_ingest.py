#!/usr/bin/env python3
"""
Batch PDF Ingestion Script
Processa múltiplos PDFs em um diretório e ingere na base de conhecimento.
"""

import os
import glob
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importar funções do ingest_pdf.py
from ingest_pdf import ingest_pdf

# Para barra de progresso
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️  Instale 'tqdm' para barra de progresso: pip install tqdm")


class IngestionReport:
    """Relatório de ingestão em lote."""

    def __init__(self):
        self.total_files = 0
        self.successful = []
        self.skipped = []
        self.failed = []
        self.start_time = datetime.now()
        self.end_time = None

    def add_success(self, file_path: str, document_id: str, chunks: int):
        """Adiciona arquivo processado com sucesso ao relatório.

        Args:
            file_path: Caminho do arquivo processado
            document_id: ID do documento criado no banco
            chunks: Número de chunks gerados
        """
        self.successful.append({
            "file": file_path,
            "document_id": document_id,
            "chunks": chunks,
            "status": "success"
        })

    def add_skipped(self, file_path: str, reason: str):
        """Adiciona arquivo pulado ao relatório.

        Args:
            file_path: Caminho do arquivo pulado
            reason: Motivo pelo qual foi pulado
        """
        self.skipped.append({
            "file": file_path,
            "reason": reason,
            "status": "skipped"
        })

    def add_failed(self, file_path: str, error: str):
        """Adiciona arquivo com falha ao relatório.

        Args:
            file_path: Caminho do arquivo que falhou
            error: Mensagem de erro
        """
        self.failed.append({
            "file": file_path,
            "error": str(error),
            "status": "failed"
        })

    def finalize(self):
        """Finaliza o relatório marcando timestamp de término."""
        self.end_time = datetime.now()

    def print_summary(self):
        """Imprime resumo no terminal."""
        duration = (self.end_time - self.start_time).total_seconds()

        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DE INGESTÃO EM LOTE")
        print("=" * 70)
        print(f"⏱️  Duração total: {duration:.2f}s")
        print(f"📁 Total de arquivos processados: {self.total_files}")
        print(f"✅ Sucessos: {len(self.successful)}")
        print(f"⏭️  Pulados: {len(self.skipped)}")
        print(f"❌ Falhas: {len(self.failed)}")
        print("=" * 70)

        if self.successful:
            print("\n✅ Arquivos processados com sucesso:")
            for item in self.successful:
                print(f"   • {Path(item['file']).name} → {item['chunks']} chunks (ID: {item['document_id'][:8]}...)")

        if self.skipped:
            print("\n⏭️  Arquivos pulados:")
            for item in self.skipped:
                print(f"   • {Path(item['file']).name} → {item['reason']}")

        if self.failed:
            print("\n❌ Arquivos com falha:")
            for item in self.failed:
                print(f"   • {Path(item['file']).name}")
                print(f"     Erro: {item['error'][:100]}...")

        print("\n" + "=" * 70)

    def save_json(self, output_path: str):
        """Salva relatório em JSON."""
        report_data = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            "total_files": self.total_files,
            "summary": {
                "successful": len(self.successful),
                "skipped": len(self.skipped),
                "failed": len(self.failed),
            },
            "details": {
                "successful": self.successful,
                "skipped": self.skipped,
                "failed": self.failed,
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Relatório salvo em: {output_path}")


def find_pdf_files(directory: str, recursive: bool = True, pattern: str = "*.pdf") -> List[str]:
    """Encontra todos os arquivos PDF em um diretório."""
    if recursive:
        pdf_files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
    else:
        pdf_files = glob.glob(os.path.join(directory, pattern))

    pdf_files = [os.path.abspath(f) for f in pdf_files]
    return sorted(pdf_files)


def process_single_pdf(
    pdf_path: str,
    collection_name: str,
    collection_description: str | None,
    document_type: str,
    metadata_template: dict | None,
    chunk_max_tokens: int,
    chunk_overlap_tokens: int,
    force_reindex: bool,
    extract_metadata_from_path: bool
) -> Dict[str, Any]:
    """Processa um único PDF e retorna resultado."""
    try:
        doc_metadata = metadata_template.copy() if metadata_template else {}

        if extract_metadata_from_path:
            path_parts = Path(pdf_path).parts[:-1]
            if len(path_parts) > 1:
                doc_metadata["directory"] = path_parts[-1]
                doc_metadata["path_parts"] = list(path_parts)

        document_title = Path(pdf_path).stem

        document_id = ingest_pdf(
            pdf_path=pdf_path,
            collection_name=collection_name,
            collection_description=collection_description,
            document_title=document_title,
            document_type=document_type,
            document_metadata=doc_metadata,
            chunk_max_tokens=chunk_max_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
            force_reindex=force_reindex
        )

        from ingest_pdf import supabase
        chunks_res = supabase.table("kb_chunks").select("id", count="exact").eq("document_id", document_id).execute()
        chunks_count = chunks_res.count or 0

        return {
            "status": "success",
            "document_id": document_id,
            "chunks": chunks_count,
            "file": pdf_path
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "file": pdf_path
        }


def batch_ingest(
    directory: str,
    collection_name: str,
    collection_description: str | None = None,
    document_type: str = "pdf",
    metadata_template: dict | None = None,
    chunk_max_tokens: int = 500,
    chunk_overlap_tokens: int = 50,
    force_reindex: bool = False,
    recursive: bool = True,
    pattern: str = "*.pdf",
    extract_metadata_from_path: bool = True,
    max_workers: int = 1,
    report_output: str | None = None
) -> IngestionReport:
    """Processa múltiplos PDFs em lote."""
    report = IngestionReport()

    print(f"🔍 Procurando PDFs em: {directory}")
    print(f"   Padrão: {pattern}")
    print(f"   Recursivo: {recursive}")

    pdf_files = find_pdf_files(directory, recursive=recursive, pattern=pattern)
    report.total_files = len(pdf_files)

    if not pdf_files:
        print(f"⚠️  Nenhum PDF encontrado em {directory}")
        report.finalize()
        return report

    print(f"📁 {len(pdf_files)} PDFs encontrados\n")

    if max_workers == 1:
        iterator = tqdm(pdf_files, desc="Processando PDFs") if HAS_TQDM else pdf_files

        for pdf_path in iterator:
            if not HAS_TQDM:
                print(f"\n📄 Processando: {Path(pdf_path).name}")

            result = process_single_pdf(
                pdf_path=pdf_path,
                collection_name=collection_name,
                collection_description=collection_description,
                document_type=document_type,
                metadata_template=metadata_template,
                chunk_max_tokens=chunk_max_tokens,
                chunk_overlap_tokens=chunk_overlap_tokens,
                force_reindex=force_reindex,
                extract_metadata_from_path=extract_metadata_from_path
            )

            if result["status"] == "success":
                report.add_success(result["file"], result["document_id"], result["chunks"])
            elif result["status"] == "skipped":
                report.add_skipped(result["file"], result.get("reason", "Unknown"))
            else:
                report.add_failed(result["file"], result.get("error", "Unknown error"))
    else:
        print(f"⚡ Processamento paralelo com {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    process_single_pdf,
                    pdf_path=pdf_path,
                    collection_name=collection_name,
                    collection_description=collection_description,
                    document_type=document_type,
                    metadata_template=metadata_template,
                    chunk_max_tokens=chunk_max_tokens,
                    chunk_overlap_tokens=chunk_overlap_tokens,
                    force_reindex=force_reindex,
                    extract_metadata_from_path=extract_metadata_from_path
                ): pdf_path
                for pdf_path in pdf_files
            }

            iterator = tqdm(as_completed(futures), total=len(futures), desc="Processando PDFs") if HAS_TQDM else as_completed(futures)

            for future in iterator:
                result = future.result()

                if result["status"] == "success":
                    report.add_success(result["file"], result["document_id"], result["chunks"])
                elif result["status"] == "skipped":
                    report.add_skipped(result["file"], result.get("reason", "Unknown"))
                else:
                    report.add_failed(result["file"], result.get("error", "Unknown error"))

    report.finalize()

    if report_output:
        report.save_json(report_output)

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Ingestão em lote de PDFs para Supabase Knowledge Base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Processar todos os PDFs de um diretório
  python batch_ingest.py --dir ./materiais --collection "INSS 2024"

  # Processar sem recursão
  python batch_ingest.py --dir ./materiais --collection "INSS 2024" --no-recursive

  # Processamento paralelo (3 workers)
  python batch_ingest.py --dir ./materiais --collection "INSS 2024" --workers 3

  # Salvar relatório JSON
  python batch_ingest.py --dir ./materiais --collection "INSS 2024" --report report.json
        """
    )

    parser.add_argument("--dir", required=True, help="Diretório contendo PDFs")
    parser.add_argument("--collection", required=True, help="Nome da coleção")
    parser.add_argument("--collection-description", default=None, help="Descrição da coleção")
    parser.add_argument("--doc-type", default="pdf", help="Tipo dos documentos")
    parser.add_argument(
        "--metadata",
        default=None,
        help='Metadata base em JSON (ex.: \'{"banca": "CESPE", "ano": 2024}\')'
    )
    parser.add_argument("--chunk-max-tokens", type=int, default=500)
    parser.add_argument("--chunk-overlap-tokens", type=int, default=50)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-recursive", action="store_true")
    parser.add_argument("--pattern", default="*.pdf")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--report", default=None)

    args = parser.parse_args()

    metadata_template = None
    if args.metadata:
        try:
            metadata_template = json.loads(args.metadata)
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear metadata JSON: {e}")
            return 1

    if not os.path.isdir(args.dir):
        print(f"❌ Diretório não encontrado: {args.dir}")
        return 1

    try:
        report = batch_ingest(
            directory=args.dir,
            collection_name=args.collection,
            collection_description=args.collection_description,
            document_type=args.doc_type,
            metadata_template=metadata_template,
            chunk_max_tokens=args.chunk_max_tokens,
            chunk_overlap_tokens=args.chunk_overlap_tokens,
            force_reindex=args.force,
            recursive=not args.no_recursive,
            pattern=args.pattern,
            extract_metadata_from_path=True,
            max_workers=args.workers,
            report_output=args.report
        )

        report.print_summary()

        if report.failed:
            return 1
        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        return 130
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

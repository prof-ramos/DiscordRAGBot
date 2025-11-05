"""Document Control Service - Manages document processing tracking.

This service prevents reprocessing of documents and provides
knowledge base management capabilities.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from supabase import Client

from src.config import Settings
from src.exceptions import DocumentLoadError, SupabaseError
from src.logging_config import BotLogger


class DocumentControlService:
    """Manages document processing control and knowledge base.

    This service provides:
    - Document deduplication (hash-based)
    - Processing status tracking
    - Token usage monitoring
    - Knowledge base statistics
    - Document versioning

    Attributes:
        settings: Application settings
        logger: Logger instance
        client: Supabase client
    """

    def __init__(
        self,
        settings: Settings,
        logger: BotLogger,
        client: Client,
    ) -> None:
        """Initialize document control service.

        Args:
            settings: Application settings
            logger: Logger instance
            client: Supabase client
        """
        self.settings = settings
        self.logger = logger
        self.client = client

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            SHA-256 hash as hex string

        Raises:
            DocumentLoadError: If file cannot be read
        """
        try:
            sha256 = hashlib.sha256()

            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)

            return sha256.hexdigest()

        except Exception as e:
            raise DocumentLoadError(
                f"Failed to calculate hash for {file_path}",
                original_error=e,
            ) from e

    def is_document_processed(self, file_hash: str) -> bool:
        """Check if document has already been processed.

        Args:
            file_hash: SHA-256 hash of file

        Returns:
            True if document was already processed

        Raises:
            SupabaseError: If database query fails
        """
        try:
            result = self.client.rpc(
                "is_document_processed",
                {"p_file_hash": file_hash},
            ).execute()

            return result.data if result.data is not None else False

        except Exception as e:
            self.logger.error(
                "Failed to check if document is processed",
                action="ERROR",
                file_hash=file_hash[:8],
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to check document status",
                operation="is_document_processed",
                original_error=e,
            ) from e

    def get_document_by_hash(self, file_hash: str) -> Optional[dict[str, Any]]:
        """Get document information by hash.

        Args:
            file_hash: SHA-256 hash of file

        Returns:
            Document information or None if not found

        Raises:
            SupabaseError: If database query fails
        """
        try:
            result = self.client.rpc(
                "get_document_by_hash",
                {"p_file_hash": file_hash},
            ).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            self.logger.error(
                "Failed to get document by hash",
                action="ERROR",
                file_hash=file_hash[:8],
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to retrieve document",
                operation="get_document_by_hash",
                original_error=e,
            ) from e

    def start_processing(
        self,
        file_path: Path,
        file_hash: str,
    ) -> int:
        """Start document processing.

        Args:
            file_path: Path to file
            file_hash: SHA-256 hash of file

        Returns:
            Source ID for tracking

        Raises:
            SupabaseError: If database operation fails
        """
        try:
            file_size = file_path.stat().st_size
            file_type = file_path.suffix[1:].lower()  # Remove dot

            self.logger.info(
                "Starting document processing",
                action="LOADING",
                file_name=file_path.name,
                file_size=file_size,
                file_hash=file_hash[:8],
            )

            result = self.client.rpc(
                "start_document_processing",
                {
                    "p_file_name": file_path.name,
                    "p_file_path": str(file_path),
                    "p_file_hash": file_hash,
                    "p_file_size": file_size,
                    "p_file_type": file_type,
                },
            ).execute()

            source_id = result.data

            self.logger.info(
                "Document processing started",
                action="SUCCESS",
                source_id=source_id,
            )

            return source_id

        except Exception as e:
            self.logger.error(
                "Failed to start document processing",
                action="ERROR",
                file_name=file_path.name,
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to start processing",
                operation="start_document_processing",
                original_error=e,
            ) from e

    def complete_processing(
        self,
        source_id: int,
        chunks_created: int,
        total_tokens: int,
        processing_duration_ms: int,
    ) -> None:
        """Mark document processing as completed.

        Args:
            source_id: Source ID from start_processing
            chunks_created: Number of chunks created
            total_tokens: Approximate tokens consumed
            processing_duration_ms: Processing duration in milliseconds

        Raises:
            SupabaseError: If database operation fails
        """
        try:
            self.logger.info(
                "Completing document processing",
                action="LOADING",
                source_id=source_id,
                chunks=chunks_created,
                tokens=total_tokens,
            )

            self.client.rpc(
                "complete_document_processing",
                {
                    "p_source_id": source_id,
                    "p_chunks_created": chunks_created,
                    "p_total_tokens": total_tokens,
                    "p_processing_duration_ms": processing_duration_ms,
                },
            ).execute()

            self.logger.info(
                "Document processing completed",
                action="SUCCESS",
                source_id=source_id,
            )

        except Exception as e:
            self.logger.error(
                "Failed to complete document processing",
                action="ERROR",
                source_id=source_id,
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to complete processing",
                operation="complete_document_processing",
                original_error=e,
            ) from e

    def fail_processing(
        self,
        source_id: int,
        error_message: str,
        error_details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Mark document processing as failed.

        Args:
            source_id: Source ID from start_processing
            error_message: Error message
            error_details: Additional error details

        Raises:
            SupabaseError: If database operation fails
        """
        try:
            self.logger.warning(
                "Marking document processing as failed",
                action="WARNING",
                source_id=source_id,
                error=error_message,
            )

            self.client.rpc(
                "fail_document_processing",
                {
                    "p_source_id": source_id,
                    "p_error_message": error_message,
                    "p_error_details": error_details,
                },
            ).execute()

        except Exception as e:
            self.logger.error(
                "Failed to mark processing as failed",
                action="ERROR",
                source_id=source_id,
                exc_info=True,
            )
            # Don't raise here - we're already handling an error

    def deactivate_document(self, source_id: int) -> int:
        """Deactivate document and remove its chunks.

        Args:
            source_id: Source ID to deactivate

        Returns:
            Number of chunks deleted

        Raises:
            SupabaseError: If database operation fails
        """
        try:
            self.logger.info(
                "Deactivating document",
                action="LOADING",
                source_id=source_id,
            )

            result = self.client.rpc(
                "deactivate_document",
                {"p_source_id": source_id},
            ).execute()

            chunks_deleted = result.data

            self.logger.info(
                "Document deactivated",
                action="SUCCESS",
                source_id=source_id,
                chunks_deleted=chunks_deleted,
            )

            return chunks_deleted

        except Exception as e:
            self.logger.error(
                "Failed to deactivate document",
                action="ERROR",
                source_id=source_id,
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to deactivate document",
                operation="deactivate_document",
                original_error=e,
            ) from e

    def get_knowledge_base_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Dictionary with statistics:
            - total_sources: Total number of documents
            - active_sources: Number of active documents
            - total_chunks: Total number of chunks
            - total_tokens: Total tokens consumed
            - total_size_mb: Total size in MB
            - last_update: Last update timestamp

        Raises:
            SupabaseError: If database query fails
        """
        try:
            result = self.client.rpc("get_knowledge_base_stats").execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            return {
                "total_sources": 0,
                "active_sources": 0,
                "total_chunks": 0,
                "total_tokens": 0,
                "total_size_mb": 0.0,
                "last_update": None,
            }

        except Exception as e:
            self.logger.error(
                "Failed to get knowledge base stats",
                action="ERROR",
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to get statistics",
                operation="get_knowledge_base_stats",
                original_error=e,
            ) from e

    def get_active_documents(self) -> list[dict[str, Any]]:
        """Get list of active documents.

        Returns:
            List of active documents with metadata

        Raises:
            SupabaseError: If database query fails
        """
        try:
            result = (
                self.client.table("document_sources")
                .select("*")
                .eq("is_active", True)
                .eq("status", "completed")
                .order("processed_at", desc=True)
                .execute()
            )

            return result.data

        except Exception as e:
            self.logger.error(
                "Failed to get active documents",
                action="ERROR",
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to get active documents",
                operation="get_active_documents",
                original_error=e,
            ) from e

    def should_process_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """Check if file should be processed.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (should_process, message)
            - should_process: True if file should be processed
            - message: Reason message

        Raises:
            DocumentLoadError: If file cannot be read
            SupabaseError: If database query fails
        """
        # Calculate hash
        file_hash = self.calculate_file_hash(file_path)

        # Check if already processed
        if self.is_document_processed(file_hash):
            doc_info = self.get_document_by_hash(file_hash)
            if doc_info:
                return (
                    False,
                    f"Já processado: {doc_info['file_name']} "
                    f"({doc_info['total_chunks']} chunks, "
                    f"processado em {doc_info['processed_at']})",
                )
            return False, "Documento já processado"

        return True, "Novo documento - pronto para processar"

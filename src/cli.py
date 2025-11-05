"""Command-line interface for Discord RAG Bot.

This module provides CLI commands that can be run independently
from the main bot. These are exposed as console scripts via pyproject.toml.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

from src.config import get_settings
from src.logging_config import get_logger

# Load environment variables
load_dotenv()


def main() -> None:
    """Main entry point for the bot CLI.

    This is the primary command to run the bot.
    Called via: discord-rag-bot
    """
    try:
        # Import here to avoid circular imports
        from src.bot.client import DiscordRAGBot
        from src.bot.commands import setup_commands
        from src.bot.handlers import setup_handlers
        from src.exceptions import BotError, ConfigurationError

        # Load settings
        settings = get_settings()
        logger = get_logger(settings)

        logger.info(
            "Starting Discord RAG Bot",
            action="STARTUP",
            version="2.0.0",
        )

        # Create and configure bot
        bot = DiscordRAGBot(settings=settings, logger=logger)
        setup_commands(bot)
        setup_handlers(bot)

        # Run bot
        bot.run_bot()

    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Please check your .env file")
        sys.exit(1)
    except BotError as e:
        print(f"❌ Bot Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def load_documents() -> None:
    """Load documents into the vector store.

    This command processes PDF files from the data directory
    and indexes them into the Supabase vector store.

    Called via: rag-bot-load
    """
    try:
        import asyncio

        from src.exceptions import DocumentLoadError, VectorStoreError
        from src.services import SupabaseService
        from src.services.document_control_service import DocumentControlService

        # Load settings
        settings = get_settings()
        logger = get_logger(settings)

        print("\n" + "=" * 60)
        print("🚀 DOCUMENT LOADING - RAG")
        print("=" * 60 + "\n")

        # Initialize services
        supabase_service = SupabaseService(settings, logger)
        doc_control = DocumentControlService(
            settings,
            logger,
            supabase_service.client,
        )

        # Check for PDF files
        pdf_files = list(settings.data_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"❌ No PDF files found in {settings.data_dir}")
            print("\n💡 Add PDF files to the data/ directory and try again")
            sys.exit(1)

        print(f"📁 Found {len(pdf_files)} PDF files\n")

        # Process each file
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")

            # Check if already processed
            should_process, message = doc_control.should_process_file(pdf_file)

            if not should_process:
                print(f"   ⏭️  Skipping: {message}\n")
                continue

            print(f"   ⏳ Processing new file...")

            # Import processing here to avoid loading heavy dependencies early
            from load import DocumentIndexer

            indexer = DocumentIndexer()

            async def process_file() -> None:
                """Process a single file."""
                try:
                    # Load and process
                    documents = indexer.load_documents()
                    chunks = indexer.split_documents(documents)
                    await indexer.index_documents(chunks)

                    print(f"   ✅ Processed: {len(chunks)} chunks\n")
                except (DocumentLoadError, VectorStoreError) as e:
                    print(f"   ❌ Failed: {e}\n")

            # Run async processing
            asyncio.run(process_file())

        print("=" * 60)
        print("✅ LOADING COMPLETE!")
        print("=" * 60)
        print("\n💡 Next step: Run 'discord-rag-bot' to start the bot")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def show_stats() -> None:
    """Show knowledge base statistics.

    This command displays information about the indexed documents.

    Called via: rag-bot-stats
    """
    try:
        from src.services import SupabaseService
        from src.services.document_control_service import DocumentControlService

        # Load settings
        settings = get_settings()
        logger = get_logger(settings)

        # Initialize services
        supabase_service = SupabaseService(settings, logger)
        doc_control = DocumentControlService(
            settings,
            logger,
            supabase_service.client,
        )

        # Get statistics
        stats = doc_control.get_knowledge_base_stats()

        print("\n" + "=" * 60)
        print("📊 KNOWLEDGE BASE STATISTICS")
        print("=" * 60)
        print(f"\n📚 Total Documents:    {stats['active_sources']}")
        print(f"📦 Total Chunks:       {stats['total_chunks']:,}")
        print(f"💰 Total Tokens:       {stats['total_tokens']:,}")
        print(f"💾 Total Size:         {stats['total_size_mb']:.2f} MB")

        if stats['last_update']:
            print(f"🕐 Last Update:        {stats['last_update']}")

        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Allow running as: python -m src.cli
    main()

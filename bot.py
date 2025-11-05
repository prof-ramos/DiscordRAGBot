#!/usr/bin/env python3
"""Discord RAG Bot - Entry Point.

A production-ready Discord bot with RAG (Retrieval-Augmented Generation)
capabilities, featuring modular architecture, dependency injection,
caching, and comprehensive error handling.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from src.bot.client import DiscordRAGBot
from src.bot.commands import setup_commands
from src.bot.handlers import setup_handlers
from src.config import get_settings
from src.exceptions import BotError, ConfigurationError
from src.logging_config import get_logger

# Load environment variables
load_dotenv()


def main() -> None:
    """Main entry point for the bot."""
    try:
        # Load settings (validates all required env vars)
        settings = get_settings()
        logger = get_logger(settings)

        logger.info(
            "Starting Discord RAG Bot",
            action="STARTUP",
            version="2.0.0",
        )

        # Create bot instance with dependency injection
        bot = DiscordRAGBot(settings=settings, logger=logger)

        # Register commands and handlers
        setup_commands(bot)
        setup_handlers(bot)

        # Run bot
        logger.info(
            "Connecting to Discord...",
            action="LOADING",
        )

        bot.run_bot()

    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Please check your .env file and ensure all required variables are set.")
        print("   See .env.example for reference.")
        sys.exit(1)

    except BotError as e:
        print(f"❌ Bot Error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

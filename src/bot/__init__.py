"""Discord bot components."""

from src.bot.client import DiscordRAGBot
from src.bot.commands import setup_commands
from src.bot.handlers import setup_handlers

__all__ = [
    "DiscordRAGBot",
    "setup_commands",
    "setup_handlers",
]

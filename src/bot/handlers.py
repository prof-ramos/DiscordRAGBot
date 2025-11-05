"""Discord event handlers for messages and mentions."""

from typing import TYPE_CHECKING

import discord

from src.models import QueryRequest

if TYPE_CHECKING:
    from src.bot.client import DiscordRAGBot


async def send_long_message(
    channel: discord.abc.Messageable,
    content: str,
    max_length: int = 2000,
) -> None:
    """Send long message by splitting into chunks.

    Args:
        channel: Channel to send to
        content: Message content
        max_length: Maximum message length
    """
    if len(content) <= max_length:
        await channel.send(content)
        return

    # Split into chunks
    chunks = [
        content[i : i + max_length] for i in range(0, len(content), max_length)
    ]

    for chunk in chunks:
        await channel.send(chunk)


def setup_handlers(bot: "DiscordRAGBot") -> None:
    """Register all event handlers.

    Args:
        bot: Bot instance
    """

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """Handle incoming messages.

        Args:
            message: Discord message
        """
        # Ignore bot's own messages
        if message.author == bot.user:
            return

        # Process commands first
        await bot.process_commands(message)

        # Handle mentions
        if bot.user and bot.user.mentioned_in(message) and not message.mention_everyone:
            await handle_mention(message)
            return

        # Handle DMs
        if isinstance(message.channel, discord.DMChannel):
            await handle_dm(message)

    async def handle_mention(message: discord.Message) -> None:
        """Handle bot mentions.

        Args:
            message: Discord message with mention
        """
        # Extract question (remove mention)
        question = message.content.replace(f"<@{bot.user.id}>", "").strip()

        if not question:
            await message.channel.send("❓ Faça uma pergunta após me mencionar!")
            return

        guild_id = message.guild.id if message.guild else None
        user_id = str(message.author.id)

        bot.logger.info(
            "Mention received",
            action="MENTION",
            guild_id=guild_id or "DM",
            user_id=user_id,
        )

        async with message.channel.typing():
            await process_message_query(
                message=message,
                question=question,
                guild_id=guild_id,
                user_id=user_id,
                query_type="Menção",
            )

    async def handle_dm(message: discord.Message) -> None:
        """Handle direct messages.

        Args:
            message: Discord DM message
        """
        if not message.content.strip():
            await message.channel.send("❓ Envie sua pergunta!")
            return

        user_id = str(message.author.id)

        bot.logger.info(
            "DM received",
            action="DM",
            user_id=user_id,
        )

        async with message.channel.typing():
            await process_message_query(
                message=message,
                question=message.content,
                guild_id=None,
                user_id=user_id,
                query_type="DM",
            )

    async def process_message_query(
        message: discord.Message,
        question: str,
        guild_id: int | None,
        user_id: str,
        query_type: str,
    ) -> None:
        """Process a query from a message.

        Args:
            message: Discord message to reply to
            question: User question
            guild_id: Guild ID (None for DMs)
            user_id: User ID
            query_type: Type of query (Menção, DM, etc.)
        """
        try:
            # Get filter level
            filter_level = bot.config_service.get_filter_level(guild_id)

            # Create request
            request = QueryRequest(
                question=question,
                guild_id=str(guild_id) if guild_id else None,
                user_id=user_id,
                query_type=query_type,
            )

            # Process query
            result = await bot.llm_service.process_query(request, filter_level)

            # Send response
            await send_long_message(message.channel, result.answer)

            # Send sources if available
            if result.sources:
                sources_text = "\n\n**📚 Fontes:**\n"
                source_names = result.get_source_names(max_sources=3)

                for i, source in enumerate(source_names, 1):
                    sources_text += f"{i}. `{source}`\n"

                if len(sources_text) <= 2000:
                    await message.channel.send(sources_text)

        except Exception as e:
            error_msg = str(e) if isinstance(e, Exception) else "Erro desconhecido"
            await message.channel.send(f"❌ {error_msg}")

    bot.logger.info("Event handlers registered", action="SUCCESS")

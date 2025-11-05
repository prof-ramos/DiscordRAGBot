"""Discord slash commands."""

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from src.config import FilterLevel
from src.models import QueryRequest

if TYPE_CHECKING:
    from src.bot.client import DiscordRAGBot


def setup_commands(bot: "DiscordRAGBot") -> None:
    """Register all slash commands.

    Args:
        bot: Bot instance
    """

    @bot.tree.command(
        name="ask",
        description="Faz uma pergunta ao RAG",
    )
    @app_commands.describe(pergunta="Sua pergunta")
    async def ask(
        interaction: discord.Interaction,
        pergunta: str,
    ) -> None:
        """Handle /ask command.

        Args:
            interaction: Discord interaction
            pergunta: User question
        """
        await interaction.response.defer(thinking=True)

        guild_id = interaction.guild_id if interaction.guild else None
        user_id = str(interaction.user.id)

        bot.logger.info(
            "Command received",
            action="COMMAND",
            command="ask",
            guild_id=guild_id or "DM",
            user_id=user_id,
        )

        try:
            # Get filter level
            filter_level = bot.config_service.get_filter_level(guild_id)

            # Create request
            request = QueryRequest(
                question=pergunta,
                guild_id=str(guild_id) if guild_id else None,
                user_id=user_id,
                query_type="CMD /ask",
            )

            # Process query
            result = await bot.llm_service.process_query(request, filter_level)

            # Send response
            await interaction.followup.send(result.answer)

            # Send sources if available
            if result.sources:
                sources_text = "\n**📚 Fontes:**\n"
                source_names = result.get_source_names(max_sources=3)

                for i, source in enumerate(source_names, 1):
                    sources_text += f"{i}. `{source}`\n"

                if len(sources_text) <= 2000:
                    await interaction.followup.send(sources_text)

        except Exception as e:
            error_msg = str(e) if isinstance(e, Exception) else "Erro desconhecido"
            await interaction.followup.send(f"❌ {error_msg}")

    @bot.tree.command(
        name="config",
        description="Configura o nível de filtro de conteúdo do bot",
    )
    @app_commands.describe(
        nivel="Escolha o nível: conservador, moderado ou liberal"
    )
    @app_commands.choices(
        nivel=[
            app_commands.Choice(
                name="🔒 Conservador (Formal e profissional)",
                value="conservador",
            ),
            app_commands.Choice(
                name="⚖️ Moderado (Equilibrado - padrão)",
                value="moderado",
            ),
            app_commands.Choice(
                name="🔓 Liberal (Casual e descontraído)",
                value="liberal",
            ),
        ]
    )
    async def config(
        interaction: discord.Interaction,
        nivel: app_commands.Choice[str],
    ) -> None:
        """Handle /config command.

        Args:
            interaction: Discord interaction
            nivel: Filter level choice
        """
        guild_id = interaction.guild_id if interaction.guild else None
        user_id = str(interaction.user.id)

        bot.logger.info(
            "Config command received",
            action="COMMAND",
            guild_id=guild_id or "DM",
            user_id=user_id,
            requested_level=nivel.value,
        )

        # Check permissions (only admins in guilds)
        if interaction.guild and isinstance(interaction.user, discord.Member):
            if not interaction.user.guild_permissions.administrator:
                bot.logger.warning(
                    "Access denied - not admin",
                    action="WARNING",
                    guild_id=guild_id,
                    user_id=user_id,
                )

                await interaction.response.send_message(
                    "❌ Apenas administradores podem alterar as configurações do bot!",
                    ephemeral=True,
                )
                return

        # Set filter level
        filter_level = FilterLevel(nivel.value)
        bot.config_service.set_filter_level(guild_id, filter_level)

        # Emoji mapping
        emojis = {
            "conservador": "🔒",
            "moderado": "⚖️",
            "liberal": "🔓",
        }

        await interaction.response.send_message(
            f"✅ Nível de filtro atualizado para **{emojis[nivel.value]} {nivel.value.upper()}**!\n\n"
            f"O bot agora responderá com personalidade **{nivel.value}** neste servidor."
        )

    @bot.tree.command(
        name="status",
        description="Mostra as configurações atuais do bot",
    )
    async def status(interaction: discord.Interaction) -> None:
        """Handle /status command.

        Args:
            interaction: Discord interaction
        """
        guild_id = interaction.guild_id if interaction.guild else None
        user_id = str(interaction.user.id)

        bot.logger.info(
            "Status command received",
            action="COMMAND",
            guild_id=guild_id or "DM",
            user_id=user_id,
        )

        # Get current configuration
        filter_level = bot.config_service.get_filter_level(guild_id)

        # Emoji and description mapping
        emojis = {
            FilterLevel.CONSERVATIVE: "🔒",
            FilterLevel.MODERATE: "⚖️",
            FilterLevel.LIBERAL: "🔓",
        }

        descriptions = {
            FilterLevel.CONSERVATIVE: "Formal, profissional e respeitoso",
            FilterLevel.MODERATE: "Equilibrado e empático (padrão)",
            FilterLevel.LIBERAL: "Casual, descontraído e autêntico",
        }

        # Build embed
        local = "DMs" if not interaction.guild else f"servidor **{interaction.guild.name}**"

        embed = discord.Embed(
            title="⚙️ Configurações do Bot",
            description=f"Configurações atuais para {local}",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Nível de Filtro",
            value=f"{emojis[filter_level]} **{filter_level.value.upper()}**\n{descriptions[filter_level]}",
            inline=False,
        )

        embed.add_field(
            name="Modelo LLM",
            value=f"`{bot.settings.openrouter_model}`",
            inline=True,
        )

        embed.add_field(
            name="RAG Status",
            value="✅ Ativo" if bot.vectorstore_service.is_loaded else "⚠️ Inativo",
            inline=True,
        )

        # Add cache stats if enabled
        if bot.settings.cache_enabled:
            from src.cache import get_cache

            cache = get_cache()
            stats = cache.stats

            embed.add_field(
                name="Cache",
                value=f"📊 {stats['size']}/{stats['max_size']} | Hit rate: {stats['hit_rate']}",
                inline=True,
            )

        embed.set_footer(text="Use /config para alterar o nível (apenas admins)")

        await interaction.response.send_message(embed=embed)

    bot.logger.info("Commands registered", action="SUCCESS")

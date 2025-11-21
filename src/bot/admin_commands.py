"""
Admin Commands for Knowledge Base Management
Comandos administrativos para gerenciar a base de conhecimento.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from postgrest import CountMethod

from src.config import get_settings
from src.logging_config import get_logger


# Lista de IDs de usuários admin
def get_admin_user_ids() -> set[int]:
    """Obtém lista de IDs de usuários admin.

    Lê a configuração ADMIN_USER_IDS do .env e retorna como conjunto.

    Returns:
        Conjunto de IDs de usuários Discord com permissões admin.
        Retorna conjunto vazio se nenhum admin estiver configurado.
    """
    settings = get_settings()
    return set(settings.admin_user_ids)


def is_admin(user_id: int) -> bool:
    """Verifica se usuário é admin.

    Args:
        user_id: ID do usuário Discord

    Returns:
        True se o usuário está na lista de admins, False caso contrário.
    """
    return user_id in get_admin_user_ids()


async def check_admin_permission(interaction: discord.Interaction) -> bool:
    """Verifica permissão de admin antes de executar comando.

    Envia mensagem de erro efêmera ao usuário se não tiver permissão.

    Args:
        interaction: Interação Discord do comando

    Returns:
        True se usuário tem permissão admin, False caso contrário.
    """
    if not is_admin(interaction.user.id):
        await interaction.response.send_message(
            "❌ Você não tem permissão para usar este comando.",
            ephemeral=True
        )
        return False
    return True


class AdminCommands(commands.Cog):
    """Cog com comandos administrativos.

    Fornece comandos Discord para gerenciar a base de conhecimento,
    incluindo listagem de coleções, estatísticas e reindexação.
    """

    def __init__(self, bot: commands.Bot):
        """Inicializa o cog de comandos administrativos.

        Args:
            bot: Instância do bot Discord
        """
        self.bot = bot
        self.settings = get_settings()
        self.logger = get_logger()

        # Importar services
        from src.services import SupabaseService
        self.supabase_service = SupabaseService(settings=self.settings, logger=self.logger)

    @app_commands.command(
        name="admin_list_collections",
        description="[ADMIN] Listar todas as coleções da base de conhecimento"
    )
    async def list_collections(self, interaction: discord.Interaction) -> None:
        """Lista todas as coleções disponíveis.

        Exibe um embed com todas as coleções da base de conhecimento,
        mostrando nome, descrição, número de documentos e ID.

        Args:
            interaction: Interação Discord do comando
        """
        if not await check_admin_permission(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        try:
            result = self.supabase_service.client.table("kb_collections")\
                .select("id, name, description, created_at, metadata")\
                .order("created_at", desc=True)\
                .execute()

            if not result.data:
                await interaction.followup.send(
                    "📂 Nenhuma coleção encontrada na base de conhecimento.",
                    ephemeral=True
                )
                return

            collections_data = []
            for coll in result.data:
                docs_res = self.supabase_service.client.table("kb_documents")\
                    .select("id", count=CountMethod.exact)\
                    .eq("collection_id", coll["id"])\
                    .eq("is_active", True)\
                    .execute()

                doc_count = docs_res.count or 0

                collections_data.append({
                    "id": coll["id"],
                    "name": coll["name"],
                    "description": coll.get("description", "Sem descrição"),
                    "doc_count": doc_count,
                    "created_at": coll["created_at"]
                })

            embed = discord.Embed(
                title="📚 Coleções da Base de Conhecimento",
                description=f"Total de {len(collections_data)} coleção(ões) encontrada(s)",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            for coll_data in collections_data[:25]:
                embed.add_field(
                    name=f"📁 {coll_data['name']}",
                    value=f"{coll_data['description'][:100]}\n"
                          f"📄 **{coll_data['doc_count']}** documento(s)\n"
                          f"🆔 `{coll_data['id'][:8]}...`",
                    inline=False
                )

            if len(collections_data) > 25:
                embed.set_footer(text=f"Mostrando 25 de {len(collections_data)} coleções")

            await interaction.followup.send(embed=embed, ephemeral=True)

            self.logger.info(
                "Admin listed collections",
                action="ADMIN",
                user_id=interaction.user.id,
                collections_count=len(collections_data)
            )

        except Exception as e:
            self.logger.error(
                "Error listing collections",
                action="ERROR",
                exc_info=True,
                user_id=interaction.user.id
            )
            await interaction.followup.send(
                f"❌ Erro ao listar coleções: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="admin_stats",
        description="[ADMIN] Estatísticas de uma coleção"
    )
    @app_commands.describe(colecao="Nome da coleção")
    async def collection_stats(
        self,
        interaction: discord.Interaction,
        colecao: str
    ) -> None:
        """Mostra estatísticas detalhadas de uma coleção.

        Exibe informações como número de documentos, chunks, tokens,
        custo estimado de embeddings e top 10 documentos.

        Args:
            interaction: Interação Discord do comando
            colecao: Nome da coleção para exibir estatísticas
        """
        if not await check_admin_permission(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        try:
            coll_res = self.supabase_service.client.table("kb_collections")\
                .select("*")\
                .eq("name", colecao)\
                .limit(1)\
                .execute()

            if not coll_res.data:
                await interaction.followup.send(
                    f"❌ Coleção '{colecao}' não encontrada.",
                    ephemeral=True
                )
                return

            collection = coll_res.data[0]
            collection_id = collection["id"]

            docs_res = self.supabase_service.client.table("kb_documents")\
                .select("*")\
                .eq("collection_id", collection_id)\
                .execute()

            documents = docs_res.data
            active_docs = [d for d in documents if d.get("is_active", False)]
            indexed_docs = [d for d in documents if d.get("is_indexed", False)]

            # Guard against empty document list to prevent PostgreSQL error
            if documents:
                chunks_res = self.supabase_service.client.table("kb_chunks")\
                    .select("id, document_id, token_count", count=CountMethod.exact)\
                    .in_("document_id", [d["id"] for d in documents])\
                    .execute()
                total_chunks = chunks_res.count or 0
                chunks_data = chunks_res.data or []
                total_tokens = sum(chunk.get("token_count", 0) for chunk in chunks_data)

                # Build document_id -> chunk count mapping to avoid N+1 queries
                from collections import defaultdict
                doc_chunk_counts: dict[str, int] = defaultdict(int)
                for chunk in chunks_data:
                    doc_chunk_counts[chunk["document_id"]] += 1
            else:
                total_chunks = 0
                total_tokens = 0
                doc_chunk_counts = {}

            embedding_cost = (total_tokens / 1_000_000) * 0.02

            embed = discord.Embed(
                title=f"📊 Estatísticas: {collection['name']}",
                description=collection.get("description", "Sem descrição"),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="📄 Documentos",
                value=f"**Total:** {len(documents)}\n"
                      f"**Ativos:** {len(active_docs)}\n"
                      f"**Indexados:** {len(indexed_docs)}",
                inline=True
            )

            embed.add_field(
                name="📦 Chunks",
                value=f"**Total:** {total_chunks:,}\n"
                      f"**Tokens:** {total_tokens:,}\n"
                      f"**Custo embedding:** ${embedding_cost:.4f}",
                inline=True
            )

            embed.add_field(
                name="📈 Médias",
                value=f"**Chunks/doc:** {total_chunks // len(documents) if documents else 0}\n"
                      f"**Tokens/chunk:** {total_tokens // total_chunks if total_chunks else 0}",
                inline=True
            )

            if documents:
                # Use pre-fetched chunk counts to avoid N+1 queries
                docs_with_chunks = [
                    {
                        "title": doc["title"],
                        "chunks": doc_chunk_counts.get(doc["id"], 0),
                        "indexed": doc.get("is_indexed", False)
                    }
                    for doc in documents
                ]

                docs_with_chunks.sort(key=lambda x: x["chunks"], reverse=True)

                top_docs_text = "\n".join([
                    f"{'✅' if d['indexed'] else '⏳'} **{d['title'][:40]}** - {d['chunks']} chunks"
                    for d in docs_with_chunks[:10]
                ])

                embed.add_field(
                    name="📚 Top 10 Documentos",
                    value=top_docs_text or "Nenhum documento",
                    inline=False
                )

            embed.set_footer(text=f"ID da coleção: {collection_id}")

            await interaction.followup.send(embed=embed, ephemeral=True)

            self.logger.info(
                "Admin viewed collection stats",
                action="ADMIN",
                user_id=interaction.user.id,
                collection=colecao
            )

        except Exception as e:
            self.logger.error(
                "Error getting collection stats",
                action="ERROR",
                exc_info=True,
                user_id=interaction.user.id,
                collection=colecao
            )
            await interaction.followup.send(
                f"❌ Erro ao obter estatísticas: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="admin_reindex",
        description="[ADMIN] Forçar reindexação de um documento"
    )
    @app_commands.describe(
        documento_id="ID do documento (primeiros 8 caracteres são suficientes)"
    )
    async def reindex_document(
        self,
        interaction: discord.Interaction,
        documento_id: str
    ) -> None:
        """Força reindexação de um documento específico.

        Remove chunks antigos e marca documento como não indexado,
        fornecendo comando para reprocessamento manual.

        Args:
            interaction: Interação Discord do comando
            documento_id: ID do documento (primeiros 8 caracteres são suficientes)
        """
        if not await check_admin_permission(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        try:
            docs_res = self.supabase_service.client.table("kb_documents")\
                .select("id, title, external_id, collection_id")\
                .like("id", f"{documento_id}%")\
                .limit(1)\
                .execute()

            if not docs_res.data:
                await interaction.followup.send(
                    f"❌ Documento com ID '{documento_id}*' não encontrado.",
                    ephemeral=True
                )
                return

            document = docs_res.data[0]
            doc_id = document["id"]
            doc_title = document["title"]
            external_id = document.get("external_id")

            if not external_id:
                await interaction.followup.send(
                    f"❌ Documento '{doc_title}' não possui `external_id`. Não é possível reindexar.",
                    ephemeral=True
                )
                return

            import os
            if not os.path.exists(external_id):
                await interaction.followup.send(
                    f"❌ Arquivo fonte não encontrado: `{external_id}`\n"
                    f"O documento não pode ser reindexado sem o arquivo original.",
                    ephemeral=True
                )
                return

            delete_res = self.supabase_service.client.table("kb_chunks")\
                .delete()\
                .eq("document_id", doc_id)\
                .execute()

            chunks_deleted = len(delete_res.data) if delete_res.data else 0

            self.supabase_service.client.table("kb_documents")\
                .update({"is_indexed": False})\
                .eq("id", doc_id)\
                .execute()

            await interaction.followup.send(
                f"🔄 Reindexação preparada para **{doc_title}**\n\n"
                f"✅ {chunks_deleted} chunks antigos removidos\n"
                f"⏳ Execute o script de ingestão para reprocessar:\n"
                f"```bash\n"
                f"python ingest_pdf.py --pdf \"{external_id}\" --collection \"<nome_colecao>\" --force\n"
                f"```",
                ephemeral=True
            )

            self.logger.info(
                "Admin triggered document reindex",
                action="ADMIN",
                user_id=interaction.user.id,
                document_id=doc_id,
                document_title=doc_title,
                chunks_deleted=chunks_deleted
            )

        except Exception as e:
            self.logger.error(
                "Error reindexing document",
                action="ERROR",
                exc_info=True,
                user_id=interaction.user.id,
                document_id=documento_id
            )
            await interaction.followup.send(
                f"❌ Erro ao reindexar documento: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Setup function para adicionar cog."""
    await bot.add_cog(AdminCommands(bot))

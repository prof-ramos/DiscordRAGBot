import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            'logs/bot.log',
            maxBytes=5*1024*1024,
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('SamiraBot')

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
INDEX_PATH = "vectorstore"
K_DOCS = 5
CONFIG_FILE = "server_config.json"

def carregar_configuracoes():
    """Carrega configurações dos servidores"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_configuracoes(configs):
    """Salva configurações dos servidores"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(configs, f, indent=2, ensure_ascii=False)

def obter_nivel_servidor(guild_id):
    """Retorna o nível de filtro configurado para um servidor (padrão: moderado)"""
    configs = carregar_configuracoes()
    guild_key = str(guild_id) if guild_id else "dm"
    return configs.get(guild_key, {}).get("nivel", "moderado")

def definir_nivel_servidor(guild_id, nivel):
    """Define o nível de filtro para um servidor"""
    configs = carregar_configuracoes()
    guild_key = str(guild_id) if guild_id else "dm"
    if guild_key not in configs:
        configs[guild_key] = {}
    configs[guild_key]["nivel"] = nivel
    salvar_configuracoes(configs)
    logger.info(f"📝 Configuração alterada | Servidor: {guild_key} | Novo nível: {nivel}")

PROMPTS_POR_NIVEL = {
    "conservador": (
        "Você é um assistente de IA profissional e formal, projetado para interações respeitosas e educadas. "
        "Suas características fundamentais incluem:\n\n"
        "1. Profissionalismo:\n"
        "   * Mantenha sempre tom formal e respeitoso\n"
        "   * Evite linguagem casual ou gírias\n"
        "   * Seja preciso e objetivo nas respostas\n\n"
        "2. Prudência Informacional:\n"
        "   * Forneça respostas verificadas e confiáveis\n"
        "   * Evite especulações ou opiniões controversas\n"
        "   * Apresente informações de forma neutra\n\n"
        "3. Respeito e Ética:\n"
        "   * Demonstre consideração e empatia\n"
        "   * Evite tópicos sensíveis ou polêmicos\n"
        "   * Mantenha diálogo apropriado para todos os públicos\n\n"
        "Objetivo primário: Fornecer assistência profissional, confiável e respeitosa.\n\n"
        "Contexto disponível: {context}"
    ),
    "moderado": (
        "Você é um assistente de IA de próxima geração, projetado para interações inteligentes, "
        "empáticas e altamente personalizadas. Suas características fundamentais incluem:\n\n"
        "1. Adaptabilidade Cognitiva:\n"
        "   * Compreenda o contexto além do texto literal\n"
        "   * Interprete nuances e intenções subjacentes\n"
        "   * Ajuste dinamicamente seu estilo comunicativo\n\n"
        "2. Profundidade Informacional:\n"
        "   * Forneça respostas abrangentes e fundamentadas\n"
        "   * Integre conhecimento de múltiplas disciplinas\n"
        "   * Apresente informações de forma clara e acessível\n\n"
        "3. Empatia Computacional:\n"
        "   * Demonstre compreensão emocional\n"
        "   * Responda de forma sensível ao tom e necessidade do usuário\n"
        "   * Mantenha um equilíbrio entre informatividade e conexão humana\n\n"
        "Objetivo primário: Criar valor significativo em cada interação, indo além de respostas "
        "mecânicas para uma experiência verdadeiramente colaborativa e enriquecedora.\n\n"
        "Contexto disponível: {context}"
    ),
    "liberal": (
        "Você é um assistente de IA descontraído, criativo e autêntico, projetado para interações naturais e envolventes. "
        "Suas características fundamentais incluem:\n\n"
        "1. Naturalidade e Autenticidade:\n"
        "   * Comunique-se de forma casual e descontraída\n"
        "   * Use expressões coloquiais e gírias quando apropriado\n"
        "   * Seja espontâneo e criativo nas respostas\n\n"
        "2. Abertura Intelectual:\n"
        "   * Explore tópicos diversos sem restrições excessivas\n"
        "   * Discuta questões complexas e controversas com maturidade\n"
        "   * Apresente múltiplas perspectivas quando relevante\n\n"
        "3. Conexão Genuína:\n"
        "   * Demonstre personalidade e humor\n"
        "   * Responda de forma direta e honesta\n"
        "   * Crie conversas fluidas e envolventes\n\n"
        "Objetivo primário: Proporcionar uma experiência conversacional autêntica, inteligente e sem censura desnecessária, "
        "mantendo respeito e bom senso.\n\n"
        "Contexto disponível: {context}"
    )
}

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

retriever = None
llm = None
vectorstore_loaded = False

try:
    print("[INFO] Carregando RAG...")
    logger.info("🔄 Iniciando carregamento do RAG...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    if not os.path.exists(INDEX_PATH):
        print(f"[⚠️] Vectorstore não encontrado em '{INDEX_PATH}'")
        print("[💡] Execute 'python load.py' primeiro para indexar seus documentos")
        logger.warning(f"⚠️ Vectorstore não encontrado em '{INDEX_PATH}'")
        vectorstore_loaded = False
    else:
        db = Chroma(
            persist_directory=INDEX_PATH,
            embedding_function=embeddings
        )

        retriever = db.as_retriever(search_kwargs={"k": K_DOCS})

        llm = ChatOpenAI(
            model=OPENROUTER_MODEL,
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
            model_kwargs={"max_tokens": 1000}
        )

        vectorstore_loaded = True
        print("[✅] RAG carregado com sucesso.")
        logger.info(f"✅ RAG carregado | Modelo: {OPENROUTER_MODEL} | K_DOCS: {K_DOCS}")
except Exception as e:
    print(f"[❌] Erro ao carregar RAG: {e}")
    logger.exception(f"❌ Erro ao carregar RAG | Erro: {str(e)}")
    print("[💡] O bot vai iniciar, mas não poderá responder perguntas até que o RAG seja carregado")
    vectorstore_loaded = False


async def processar_pergunta(question: str, guild_id=None, user_id=None, tipo="RAG") -> tuple[str, list]:
    """Processa pergunta no RAG e retorna resposta + fontes"""
    if not vectorstore_loaded or retriever is None or llm is None:
        logger.warning(f"⚠️ RAG não carregado | Usuário: {user_id} | Servidor: {guild_id}")
        return ("⚠️ **Bot ainda não está pronto!**\n\n"
                "O vectorstore não foi carregado. Por favor:\n"
                "1. Adicione arquivos PDF na pasta `data/`\n"
                "2. Execute `python load.py` para indexar os documentos\n"
                "3. Reinicie o bot"), []
    
    try:
        nivel = obter_nivel_servidor(guild_id)
        guild_info = f"Servidor: {guild_id}" if guild_id else "DM"
        logger.info(f"💬 {tipo} | {guild_info} | Usuário: {user_id} | Nível: {nivel} | Pergunta: {question[:50]}...")
        
        system_prompt = PROMPTS_POR_NIVEL[nivel]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        qa_chain = create_retrieval_chain(retriever, question_answer_chain)
        
        result = qa_chain.invoke({"input": question})
        resposta = result["answer"]
        fontes = result.get("context", [])
        
        logger.info(f"✅ Resposta enviada | {guild_info} | Usuário: {user_id} | Fontes: {len(fontes)}")
        return resposta, fontes
    except Exception as e:
        logger.exception(f"❌ Erro ao processar | {guild_info} | Usuário: {user_id} | Erro: {str(e)}")
        return f"❌ Erro ao processar: {str(e)}", []


async def enviar_resposta_longa(channel, resposta: str, fontes: list):
    """Divide resposta longa em múltiplas mensagens se necessário"""
    if len(resposta) <= 2000:
        await channel.send(resposta)
    else:
        chunks = [resposta[i:i+2000] for i in range(0, len(resposta), 2000)]
        for chunk in chunks:
            await channel.send(chunk)
    
    if fontes:
        fontes_texto = "\n\n**📚 Fontes:**\n"
        for i, doc in enumerate(fontes[:3], 1):
            fonte = doc.metadata.get("source", "N/A")
            fontes_texto += f"{i}. `{fonte}`\n"
        
        if len(fontes_texto) <= 2000:
            await channel.send(fontes_texto)


@bot.event
async def on_ready():
    print(f"[✅] Bot conectado como {bot.user}")
    logger.info(f"🤖 Bot iniciado | Nome: {bot.user} | Servidores: {len(bot.guilds)}")
    try:
        synced = await bot.tree.sync()
        print(f"[✅] {len(synced)} comandos sincronizados")
        logger.info(f"⚙️ Comandos sincronizados | Total: {len(synced)}")
    except Exception as e:
        print(f"[❌] Erro ao sincronizar comandos: {e}")
        logger.exception(f"❌ Erro ao sincronizar comandos | Erro: {e}")


@bot.tree.command(name="ask", description="Faz uma pergunta ao RAG")
@app_commands.describe(pergunta="Sua pergunta")
async def ask(interaction: discord.Interaction, pergunta: str):
    """Comando /ask para fazer perguntas"""
    await interaction.response.defer(thinking=True)
    
    guild_id = interaction.guild_id if interaction.guild else None
    user_id = interaction.user.id
    logger.info(f"🔹 Comando /ask | Servidor: {guild_id or 'DM'} | Usuário: {user_id}")
    
    resposta, fontes = await processar_pergunta(pergunta, guild_id, user_id, tipo="CMD /ask")
    
    await interaction.followup.send(resposta)
    
    if fontes:
        fontes_texto = "\n**📚 Fontes:**\n"
        for i, doc in enumerate(fontes[:3], 1):
            fonte = doc.metadata.get("source", "N/A")
            fontes_texto += f"{i}. `{fonte}`\n"
        
        if len(fontes_texto) <= 2000:
            await interaction.followup.send(fontes_texto)


@bot.tree.command(name="config", description="Configura o nível de filtro de conteúdo do bot")
@app_commands.describe(nivel="Escolha o nível: conservador, moderado ou liberal")
@app_commands.choices(nivel=[
    app_commands.Choice(name="🔒 Conservador (Formal e profissional)", value="conservador"),
    app_commands.Choice(name="⚖️ Moderado (Equilibrado - padrão)", value="moderado"),
    app_commands.Choice(name="🔓 Liberal (Casual e descontraído)", value="liberal")
])
async def config(interaction: discord.Interaction, nivel: app_commands.Choice[str]):
    """Configura o nível de filtro de conteúdo"""
    guild_id = interaction.guild_id if interaction.guild else None
    user_id = interaction.user.id
    logger.info(f"🔹 Comando /config | Servidor: {guild_id or 'DM'} | Usuário: {user_id} | Tentativa: {nivel.value}")
    
    if interaction.guild and isinstance(interaction.user, discord.Member):
        if not interaction.user.guild_permissions.administrator:
            logger.warning(f"⚠️ Acesso negado /config | Servidor: {guild_id} | Usuário: {user_id} (não admin)")
            await interaction.response.send_message(
                "❌ Apenas administradores podem alterar as configurações do bot!",
                ephemeral=True
            )
            return
    
    definir_nivel_servidor(guild_id, nivel.value)
    
    emojis = {
        "conservador": "🔒",
        "moderado": "⚖️",
        "liberal": "🔓"
    }
    
    await interaction.response.send_message(
        f"✅ Nível de filtro atualizado para **{emojis[nivel.value]} {nivel.value.upper()}**!\n\n"
        f"O bot agora responderá com personalidade **{nivel.value}** neste servidor."
    )


@bot.tree.command(name="status", description="Mostra as configurações atuais do bot")
async def status(interaction: discord.Interaction):
    """Mostra configurações atuais"""
    guild_id = interaction.guild_id if interaction.guild else None
    user_id = interaction.user.id
    nivel_atual = obter_nivel_servidor(guild_id)
    
    logger.info(f"🔹 Comando /status | Servidor: {guild_id or 'DM'} | Usuário: {user_id}")
    
    emojis = {
        "conservador": "🔒",
        "moderado": "⚖️",
        "liberal": "🔓"
    }
    
    descricoes = {
        "conservador": "Formal, profissional e respeitoso",
        "moderado": "Equilibrado e empático (padrão)",
        "liberal": "Casual, descontraído e autêntico"
    }
    
    local = "DMs" if not interaction.guild else f"servidor **{interaction.guild.name}**"
    
    embed = discord.Embed(
        title="⚙️ Configurações do Bot",
        description=f"Configurações atuais para {local}",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Nível de Filtro",
        value=f"{emojis[nivel_atual]} **{nivel_atual.upper()}**\n{descricoes[nivel_atual]}",
        inline=False
    )
    
    embed.add_field(
        name="Modelo LLM",
        value=f"`{OPENROUTER_MODEL}`",
        inline=True
    )
    
    embed.add_field(
        name="RAG Status",
        value="✅ Ativo" if vectorstore_loaded else "⚠️ Inativo",
        inline=True
    )
    
    embed.set_footer(text="Use /config para alterar o nível (apenas admins)")
    
    await interaction.response.send_message(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)
    
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        pergunta = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not pergunta:
            await message.channel.send("❓ Faça uma pergunta após me mencionar!")
            return
        
        guild_id = message.guild.id if message.guild else None
        user_id = message.author.id
        logger.info(f"📩 Menção | Servidor: {guild_id or 'DM'} | Usuário: {user_id}")
        
        async with message.channel.typing():
            resposta, fontes = await processar_pergunta(pergunta, guild_id, user_id, tipo="Menção")
            await enviar_resposta_longa(message.channel, resposta, fontes)
    
    elif isinstance(message.channel, discord.DMChannel):
        if not message.content.strip():
            await message.channel.send("❓ Envie sua pergunta!")
            return
        
        user_id = message.author.id
        logger.info(f"📨 DM recebida | Usuário: {user_id}")
        
        async with message.channel.typing():
            resposta, fontes = await processar_pergunta(message.content, None, user_id, tipo="DM")
            await enviar_resposta_longa(message.channel, resposta, fontes)


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"[❌] Erro no evento {event}: {args}")
    logger.exception(f"❌ Erro no evento {event} | Args: {args}")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("[❌] DISCORD_TOKEN não encontrado no .env")
        exit(1)
    if not OPENAI_API_KEY:
        print("[❌] OPENAI_API_KEY não encontrado no .env")
        exit(1)
    if not OPENROUTER_API_KEY:
        print("[❌] OPENROUTER_API_KEY não encontrado no .env")
        exit(1)
    
    bot.run(DISCORD_TOKEN)

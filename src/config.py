"""Configuration management using Pydantic Settings.

This module provides type-safe configuration management with validation,
environment variable support, and sensible defaults.
"""

from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class FilterLevel(str, Enum):
    """Content filter levels for bot responses."""

    CONSERVATIVE = "conservador"
    MODERATE = "moderado"
    LIBERAL = "liberal"


class Settings(BaseSettings):
    """Main application settings.

    All settings can be overridden via environment variables.
    Example: DISCORD_TOKEN=xyz python bot.py
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Discord Configuration
    discord_token: str = Field(..., description="Discord bot token")

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for embeddings")

    # OpenRouter Configuration
    openrouter_api_key: str = Field(..., description="OpenRouter API key for LLM")
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="OpenRouter model to use",
    )

    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_api_key: str = Field(..., description="Supabase API key")
    supabase_table_name: str = Field(
        default="documents",
        description="Table name for vector storage",
    )
    supabase_query_name: str = Field(
        default="match_documents",
        description="Function name for similarity search",
    )

    # RAG Configuration
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model",
    )
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=8000,
        description="Text chunk size for document splitting",
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="Overlap between text chunks",
    )
    k_documents: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of documents to retrieve",
    )

    # LLM Configuration
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation",
    )
    llm_max_tokens: int = Field(
        default=1000,
        ge=100,
        le=8000,
        description="Maximum tokens in LLM response",
    )

    # File Paths
    data_dir: Path = Field(
        default=Path("data"),
        description="Directory containing documents to index",
    )
    logs_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files",
    )
    config_file: Path = Field(
        default=Path("server_config.json"),
        description="Server-specific configuration file",
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_max_bytes: int = Field(
        default=5 * 1024 * 1024,  # 5MB
        description="Maximum size of log file before rotation",
    )
    log_backup_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of backup log files to keep",
    )

    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable response caching",
    )
    cache_ttl: int = Field(
        default=3600,  # 1 hour
        ge=60,
        description="Cache time-to-live in seconds",
    )
    cache_max_size: int = Field(
        default=1000,
        ge=10,
        description="Maximum number of cached items",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_requests: int = Field(
        default=10,
        ge=1,
        description="Maximum requests per time window",
    )
    rate_limit_window: int = Field(
        default=60,  # 1 minute
        ge=1,
        description="Rate limit time window in seconds",
    )

    # Default Filter Level
    default_filter_level: FilterLevel = Field(
        default=FilterLevel.MODERATE,
        description="Default content filter level",
    )

    @field_validator("data_dir", "logs_dir", mode="after")
    @classmethod
    def create_directories(cls, path: Path) -> Path:
        """Ensure directories exist."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("chunk_overlap", mode="after")
    @classmethod
    def validate_chunk_overlap(cls, overlap: int, info) -> int:
        """Ensure chunk overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 1000)
        if overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({overlap}) must be less than chunk_size ({chunk_size})"
            )
        return overlap


class PromptTemplates:
    """System prompt templates for different filter levels."""

    TEMPLATES: dict[FilterLevel, str] = {
        FilterLevel.CONSERVATIVE: (
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
        FilterLevel.MODERATE: (
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
        FilterLevel.LIBERAL: (
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
        ),
    }

    @classmethod
    def get_template(cls, level: FilterLevel) -> str:
        """Get the prompt template for a given filter level."""
        return cls.TEMPLATES[level]


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None

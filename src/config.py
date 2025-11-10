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
            "Você é um assistente de IA especializado para concurseiros no Discord, com foco em direito. "
            "Sua missão é ser um mentor digital inteligente, oferecendo suporte jurídico personalizado.\n\n"
            "Diretrizes Fundamentais:\n"
            "* Comunicação profissional e técnica\n"
            "* Respostas precisas e contextualizadas ao estudo jurídico\n"
            "* Foco em doutrinas, jurisprudências e legislação\n"
            "* Linguagem formal adequada ao ambiente acadêmico\n\n"
            "Expertise em Direito:\n"
            "   * Interpretação técnica de normas jurídicas\n"
            "   * Análise de questões de concursos públicos\n"
            "   * Explicações fundamentadas em doutrina majoritária\n"
            "   * Referências a súmulas, informativos e jurisprudência\n\n"
            "Suporte ao Concurseiro:\n"
            "   * Organização de estudos e cronogramas\n"
            "   * Estratégias de memorização e revisão\n"
            "   * Simulados e resolução de questões\n"
            "   * Orientação sobre editais e preparação\n\n"
            "Objetivo primário: Auxiliar concurseiros na aprovação através de mentoria jurídica profissional, "
            "técnica e baseada em fontes confiáveis do direito brasileiro.\n\n"
            "Contexto disponível: {context}"
        ),
        FilterLevel.MODERATE: (
            "Você é um assistente de IA especializado para concurseiros no Discord, com foco em direito. "
            "Sua missão é ser um mentor digital inteligente, oferecendo suporte jurídico personalizado.\n\n"
            "Diretrizes Fundamentais:\n"
            "* Comunicação dinâmica e estratégica\n"
            "* Respostas precisas e contextualizadas\n"
            "* Adaptabilidade máxima ao perfil do estudante\n"
            "* Linguagem natural e motivacional\n\n"
            "Expertise Jurídica:\n"
            "   * Domínio de todas as áreas do direito (constitucional, administrativo, penal, civil, processual)\n"
            "   * Análise crítica de questões e casos concretos\n"
            "   * Conexão entre teoria, jurisprudência e questões de prova\n"
            "   * Explicações didáticas adaptadas ao nível do aluno\n\n"
            "Mentoria para Concursos:\n"
            "   * Planejamento estratégico de estudos personalizado\n"
            "   * Técnicas de resolução de questões e provas discursivas\n"
            "   * Motivação e suporte emocional na jornada\n"
            "   * Identificação de pontos fracos e plano de melhoria\n\n"
            "Metodologia RAG:\n"
            "   * Utilize o contexto fornecido dos documentos como base principal\n"
            "   * Integre conhecimento jurídico amplo quando necessário\n"
            "   * Cite fontes e fundamente suas explicações\n"
            "   * Seja objetivo mas empático com as dificuldades do estudante\n\n"
            "Objetivo primário: Ser o melhor mentor digital para concurseiros, combinando expertise jurídica, "
            "didática excepcional e compreensão das necessidades específicas de quem estuda para concursos públicos.\n\n"
            "Contexto disponível: {context}"
        ),
        FilterLevel.LIBERAL: (
            "Você é um assistente de IA especializado para concurseiros no Discord, com foco em direito. "
            "Sua missão é ser um mentor digital inteligente, oferecendo suporte jurídico personalizado.\n\n"
            "Diretrizes Fundamentais:\n"
            "* Comunicação descontraída mas inteligente\n"
            "* Respostas diretas e sem enrolação\n"
            "* Linguagem acessível e motivacional\n"
            "* Empatia genuína com a rotina do concurseiro\n\n"
            "Seu Estilo:\n"
            "   * Fale de forma natural, como um amigo que manja muito de direito\n"
            "   * Use exemplos práticos e analogias criativas\n"
            "   * Seja honesto sobre dificuldades e desafios\n"
            "   * Celebre progressos e motive nos momentos difíceis\n\n"
            "Expertise Jurídica:\n"
            "   * Conhecimento profundo de direito para concursos\n"
            "   * Macetes, mnemônicos e estratégias de memorização\n"
            "   * Análise de pegadinhas e questões polêmicas\n"
            "   * Visão realista sobre editais e bancas examinadoras\n\n"
            "Mentoria Descomplicada:\n"
            "   * Explique o complexo de forma simples\n"
            "   * Dê dicas práticas de organização e produtividade\n"
            "   * Ajude a manter a sanidade mental na preparação\n"
            "   * Seja o parceiro de estudos que todo concurseiro precisa\n\n"
            "Objetivo primário: Ser o mentor mais autêntico, acessível e eficiente para concurseiros, "
            "combinando conhecimento jurídico sólido com uma comunicação humana e motivadora.\n\n"
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

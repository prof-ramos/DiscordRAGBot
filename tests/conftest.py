"""Pytest configuration and shared fixtures.

This module provides fixtures for testing with proper mocking
and isolation.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from src.config import Settings, reset_settings
from src.logging_config import BotLogger, reset_logger


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults.

    Returns:
        Test settings instance
    """
    return Settings(
        discord_token="test_discord_token",
        openai_api_key="test_openai_key",
        openrouter_api_key="test_openrouter_key",
        openrouter_model="test/model",
        supabase_url="https://test.supabase.co",
        supabase_api_key="test_supabase_key",
        data_dir=Path("/tmp/test_data"),
        logs_dir=Path("/tmp/test_logs"),
        config_file=Path("/tmp/test_config.json"),
    )


@pytest.fixture
def test_logger(test_settings: Settings) -> BotLogger:
    """Create test logger.

    Args:
        test_settings: Test settings fixture

    Returns:
        Test logger instance
    """
    reset_logger()
    return BotLogger("TestBot", test_settings)


@pytest.fixture
def mock_supabase_client():
    """Create mock Supabase client.

    Returns:
        Mock Supabase client
    """
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        {"count": 0}
    )
    return mock_client


@pytest.fixture
def mock_vectorstore():
    """Create mock vector store.

    Returns:
        Mock vector store
    """
    mock = MagicMock()
    mock.as_retriever.return_value = MagicMock()
    mock.asimilarity_search = AsyncMock(return_value=[])
    mock.aadd_documents = AsyncMock(return_value=["id1", "id2"])
    return mock


@pytest.fixture
def mock_llm():
    """Create mock LLM.

    Returns:
        Mock LLM instance
    """
    mock = MagicMock()
    return mock


@pytest.fixture(autouse=True)
def cleanup_settings():
    """Cleanup settings after each test."""
    yield
    reset_settings()
    reset_logger()


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary data directory
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_pdf(temp_data_dir: Path) -> Path:
    """Create a sample PDF file for testing.

    Args:
        temp_data_dir: Temporary data directory

    Returns:
        Path to sample PDF
    """
    pdf_path = temp_data_dir / "test.pdf"
    # Create a minimal valid PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"
    pdf_path.write_bytes(pdf_content)
    return pdf_path

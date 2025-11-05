# Contributing to Discord RAG Bot

Thank you for your interest in contributing to Discord RAG Bot! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## 📜 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A Discord account (for testing)
- Supabase account (for database)
- OpenAI API key (for embeddings)
- OpenRouter API key (for LLM)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/DiscordRAGBot.git
cd DiscordRAGBot
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/prof-ramos/DiscordRAGBot.git
```

## 💻 Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all development dependencies
make install-dev

# Or manually:
pip install -r requirements-dev.txt
pre-commit install
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

### 4. Run Database Migrations

Follow the migration guide in [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) to set up your Supabase database.

### 5. Verify Setup

```bash
# Run tests
make test

# Check code quality
make check

# Run the bot (Ctrl+C to stop)
make run
```

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write your code
- Add or update tests
- Update documentation if needed

### 3. Run Quality Checks

```bash
# Format code
make format

# Run linters
make lint

# Run type checker
make typecheck

# Run tests
make test

# Or run everything at once
make check
```

### 4. Commit Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

# Examples:
git commit -m "feat(bot): add support for image attachments"
git commit -m "fix(cache): resolve memory leak in query cache"
git commit -m "docs: update installation instructions"
git commit -m "test: add tests for document control service"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes (dependencies, etc.)

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📏 Coding Standards

### Python Style Guide

We follow [PEP 8](https://peps.python.org/pep-0008/) with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all function signatures
- Use docstrings for all public functions, classes, and modules
- Prefer `pathlib.Path` over string paths
- Use f-strings for string formatting

### Code Formatting

We use automated formatters:

- **Black**: Code formatter
- **isort**: Import sorter
- **Ruff**: Fast linter

```bash
# Auto-format code
make format

# Check formatting
black --check src tests
isort --check src tests
```

### Type Hints

All code must include type hints:

```python
# Good ✅
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts."""
    ...

# Bad ❌
def calculate_similarity(text1, text2):
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def process_document(file_path: Path, chunk_size: int = 1000) -> list[str]:
    """Process a document and split into chunks.

    Args:
        file_path: Path to the document file
        chunk_size: Maximum size of each chunk (default: 1000)

    Returns:
        List of text chunks

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If chunk_size is invalid

    Example:
        >>> chunks = process_document(Path("doc.pdf"), chunk_size=500)
        >>> print(f"Created {len(chunks)} chunks")
        Created 42 chunks
    """
    ...
```

### Import Organization

Organize imports in this order:

1. Standard library
2. Third-party packages
3. Local imports

```python
# Standard library
import sys
from pathlib import Path
from typing import Optional

# Third-party
import discord
from pydantic import BaseModel

# Local
from src.config import Settings
from src.models import Document
```

## 🧪 Testing

### Writing Tests

- Place tests in `tests/` directory
- Mirror the structure of `src/`
- Use descriptive test names
- Aim for >80% code coverage

```python
# tests/test_document_control.py
import pytest
from pathlib import Path
from src.services.document_control_service import DocumentControlService

def test_calculate_file_hash():
    """Test file hash calculation."""
    # Arrange
    test_file = Path("tests/fixtures/sample.pdf")

    # Act
    hash_value = calculate_file_hash(test_file)

    # Assert
    assert len(hash_value) == 64  # SHA-256 hash length
    assert isinstance(hash_value, str)

@pytest.mark.asyncio
async def test_document_processing():
    """Test document processing flow."""
    ...
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_document_control.py

# Run with verbose output
make test-verbose

# Run in watch mode
make test-watch

# Generate coverage report
make coverage
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_pure_function():
    """Unit test for pure function."""
    ...

@pytest.mark.integration
def test_database_interaction():
    """Integration test with database."""
    ...

@pytest.mark.slow
def test_large_document_processing():
    """Slow test that processes large document."""
    ...
```

Run specific test categories:

```bash
# Only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

## 📚 Documentation

### Update Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update migration guides for schema changes
- Add examples for new features

### Building Docs

```bash
# Build documentation
make docs

# Serve documentation locally
make docs-serve

# Deploy to GitHub Pages
make docs-deploy
```

## 🔀 Pull Request Process

### Before Submitting

1. ✅ Code follows style guidelines
2. ✅ Tests pass locally
3. ✅ New tests added for new features
4. ✅ Documentation updated
5. ✅ Commits follow conventional format
6. ✅ No merge conflicts with main

### PR Template

When creating a PR, include:

- **Description**: What changes does this PR make?
- **Motivation**: Why are these changes needed?
- **Testing**: How was this tested?
- **Screenshots**: If applicable
- **Breaking Changes**: Any breaking changes?
- **Related Issues**: Fixes #123

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer approval required
3. All review comments addressed
4. No unresolved conversations

### After Approval

- Maintainers will merge using "Squash and Merge"
- Your commits will be combined into one
- Branch will be automatically deleted

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues
2. Try latest version
3. Verify it's not a configuration issue

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Run '....'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- Bot version: [e.g., 2.0.0]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other relevant information.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Proposed solution**
How you think this should work.

**Alternatives considered**
Other solutions you've considered.

**Additional context**
Any other relevant information.
```

## 🎯 Good First Issues

Look for issues labeled `good first issue` - these are great for newcomers!

## 📞 Getting Help

- **Discord**: Join our Discord server
- **GitHub Discussions**: Ask questions
- **Email**: prof.ramos@example.com

## 🙏 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Given credit in commits

Thank you for contributing! 🎉

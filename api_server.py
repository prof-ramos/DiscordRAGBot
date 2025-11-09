#!/usr/bin/env python3
"""API Server - Entry Point.

A REST API server for the Discord RAG Bot web interface.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.api import run_api_server

if __name__ == "__main__":
    run_api_server()

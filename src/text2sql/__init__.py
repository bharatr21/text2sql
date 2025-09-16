"""
Modern Text-to-SQL system using LangChain, LangGraph, and advanced SQL engines.
"""

__version__ = "0.1.0"
__author__ = "Bharat Raghunathan"
__email__ = "bharatraghunthan9767@gmail.com"

from .core.app import create_app
from .core.config import Settings

__all__ = ["create_app", "Settings"]
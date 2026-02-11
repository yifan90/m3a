"""
OmniParser Server - HTTP API for screen parsing.

Run on a machine with GPU to provide OmniParser as a service.
"""

from .omniparser_service import OmniParserService
from .api import app, run_server

__all__ = ["OmniParserService", "app", "run_server"]

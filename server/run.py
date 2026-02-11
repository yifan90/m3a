#!/usr/bin/env python3
"""
OmniParser Server - Run script.

Usage:
    python -m server.run --port 8000 --host 0.0.0.0

Or:
    python server/run.py --port 8000
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.api import run_server


def main():
    parser = argparse.ArgumentParser(description="OmniParser Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--omniparser-path",
        default=None,
        help="Path to OmniParser directory (default: auto-detect)"
    )
    parser.add_argument("--device", default="cuda", help="Device to use (cuda/cpu)")
    args = parser.parse_args()

    run_server(
        host=args.host,
        port=args.port,
        omniparser_path=args.omniparser_path,
        device=args.device,
    )


if __name__ == "__main__":
    main()

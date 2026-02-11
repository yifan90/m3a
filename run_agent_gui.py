#!/usr/bin/env python3
"""
Computer Use Agent - GUI Launcher.

Double-click this file to start the agent GUI.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.gui import main

if __name__ == "__main__":
    main()

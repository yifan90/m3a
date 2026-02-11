"""
PyDesktop - Cross-platform computer automation library.

Provides:
- Screen operations (resolution, screenshots)
- Mouse control (click, move, drag, scroll)
- Keyboard control (press, type, combinations)
"""

from . import screen
from . import mouse
from . import keyboard

__version__ = "0.1.0"
__all__ = ["screen", "mouse", "keyboard"]

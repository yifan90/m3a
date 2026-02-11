"""
Keyboard control: key press, type text, key combinations.

Uses `pynput` for cross-platform keyboard control.
"""

import time
from typing import Union, List, Tuple

try:
    from pynput.keyboard import Key, Controller as KeyboardController, KeyCode
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

from .common import CURRENT_PLATFORM, Platform


def _ensure_pynput():
    """Ensure pynput is available."""
    if not HAS_PYNPUT:
        raise ImportError(
            "pynput is required for keyboard control. "
            "Install it with: pip install pynput"
        )


def _get_controller() -> "KeyboardController":
    """Get keyboard controller instance."""
    _ensure_pynput()
    return KeyboardController()


# Map common key names to pynput Keys
_KEY_MAP = {
    # Modifier keys
    "ctrl": Key.ctrl,
    "control": Key.ctrl,
    "alt": Key.alt,
    "shift": Key.shift,
    "meta": Key.cmd,
    "win": Key.cmd,
    "windows": Key.cmd,
    "cmd": Key.cmd,
    "command": Key.cmd,
    "super": Key.cmd,
    
    # Function keys
    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
    
    # Special keys
    "enter": Key.enter,
    "return": Key.enter,
    "tab": Key.tab,
    "space": Key.space,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "del": Key.delete,
    "escape": Key.esc,
    "esc": Key.esc,
    
    # Navigation
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "home": Key.home,
    "end": Key.end,
    "pageup": Key.page_up,
    "page_up": Key.page_up,
    "pagedown": Key.page_down,
    "page_down": Key.page_down,
    
    # Lock keys
    "capslock": Key.caps_lock,
    "caps_lock": Key.caps_lock,
    "numlock": Key.num_lock,
    "num_lock": Key.num_lock,
    "scrolllock": Key.scroll_lock,
    "scroll_lock": Key.scroll_lock,
    
    # Other
    "insert": Key.insert,
    "printscreen": Key.print_screen,
    "print_screen": Key.print_screen,
    "pause": Key.pause,
    "menu": Key.menu,
}


def _parse_key(key: str) -> Union["Key", "KeyCode"]:
    """
    Parse a key string to a pynput key.
    
    Args:
        key: Key name like 'a', 'enter', 'ctrl', etc.
    
    Returns:
        pynput Key or KeyCode object.
    """
    _ensure_pynput()
    
    key_lower = key.lower()
    
    # Check if it's a special key
    if key_lower in _KEY_MAP:
        return _KEY_MAP[key_lower]
    
    # Single character
    if len(key) == 1:
        return KeyCode.from_char(key)
    
    # Unknown key
    raise ValueError(
        f"Unknown key: '{key}'. Use single characters or special key names "
        f"like 'enter', 'ctrl', 'shift', etc."
    )


def press(key: str):
    """
    Press and release a key.
    
    Args:
        key: Key to press. Can be:
             - Single character: 'a', 'b', '1', '!'
             - Special key name: 'enter', 'tab', 'escape'
             - Modifier: 'ctrl', 'alt', 'shift', 'cmd'
    
    Example:
        >>> press('a')      # Press 'a'
        >>> press('enter')  # Press Enter
        >>> press('f5')     # Press F5
    """
    controller = _get_controller()
    k = _parse_key(key)
    controller.press(k)
    controller.release(k)


def key_down(key: str):
    """
    Press and hold a key (without releasing).
    
    Args:
        key: Key to press.
    
    Example:
        >>> key_down('shift')
        >>> press('a')  # Types 'A'
        >>> key_up('shift')
    """
    controller = _get_controller()
    k = _parse_key(key)
    controller.press(k)


def key_up(key: str):
    """
    Release a previously pressed key.
    
    Args:
        key: Key to release.
    """
    controller = _get_controller()
    k = _parse_key(key)
    controller.release(k)


def hotkey(*keys: str):
    """
    Press a key combination (hotkey).
    
    Presses all keys in order, then releases in reverse order.
    
    Args:
        *keys: Keys to press together.
    
    Example:
        >>> hotkey('ctrl', 'c')       # Copy
        >>> hotkey('ctrl', 'v')       # Paste
        >>> hotkey('ctrl', 'shift', 'esc')  # Task manager
        >>> hotkey('alt', 'f4')       # Close window
    """
    controller = _get_controller()
    
    # Parse all keys
    parsed_keys = [_parse_key(k) for k in keys]
    
    # Press all keys
    for k in parsed_keys:
        controller.press(k)
    
    # Release all keys in reverse order
    for k in reversed(parsed_keys):
        controller.release(k)


def press_combination(*keys: str):
    """
    Alias for hotkey(). Press a key combination.
    
    Example:
        >>> press_combination('ctrl', 'a')  # Select all
    """
    hotkey(*keys)


def type_text(text: str, interval: float = 0.0):
    """
    Type a string of text.
    
    Args:
        text: Text to type.
        interval: Delay between keystrokes in seconds.
    
    Example:
        >>> type_text("Hello, World!")
        >>> type_text("Slow typing...", interval=0.1)
    """
    controller = _get_controller()
    
    if interval > 0:
        for char in text:
            controller.type(char)
            time.sleep(interval)
    else:
        controller.type(text)


def write(text: str, interval: float = 0.0):
    """
    Alias for type_text(). Type a string of text.
    """
    type_text(text, interval=interval)


# Common shortcuts
def copy():
    """Press Ctrl+C (Cmd+C on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'c')
    else:
        hotkey('ctrl', 'c')


def paste():
    """Press Ctrl+V (Cmd+V on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'v')
    else:
        hotkey('ctrl', 'v')


def cut():
    """Press Ctrl+X (Cmd+X on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'x')
    else:
        hotkey('ctrl', 'x')


def select_all():
    """Press Ctrl+A (Cmd+A on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'a')
    else:
        hotkey('ctrl', 'a')


def undo():
    """Press Ctrl+Z (Cmd+Z on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'z')
    else:
        hotkey('ctrl', 'z')


def redo():
    """Press Ctrl+Y (Cmd+Shift+Z on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'shift', 'z')
    else:
        hotkey('ctrl', 'y')


def save():
    """Press Ctrl+S (Cmd+S on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 's')
    else:
        hotkey('ctrl', 's')


def find():
    """Press Ctrl+F (Cmd+F on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'f')
    else:
        hotkey('ctrl', 'f')


def new_tab():
    """Press Ctrl+T (Cmd+T on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 't')
    else:
        hotkey('ctrl', 't')


def close_tab():
    """Press Ctrl+W (Cmd+W on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'w')
    else:
        hotkey('ctrl', 'w')


def close_window():
    """Press Alt+F4 (Cmd+Q on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'q')
    else:
        hotkey('alt', 'f4')


def switch_window():
    """Press Alt+Tab (Cmd+Tab on macOS)."""
    if CURRENT_PLATFORM == Platform.MACOS:
        hotkey('cmd', 'tab')
    else:
        hotkey('alt', 'tab')

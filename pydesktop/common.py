"""
Common utilities and platform detection for pydesktop.
"""

import sys
import platform
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple


class Platform(Enum):
    """Supported platforms."""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    UNKNOWN = "unknown"


def get_platform() -> Platform:
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "linux":
        return Platform.LINUX
    elif system == "windows":
        return Platform.WINDOWS
    elif system == "darwin":
        return Platform.MACOS
    return Platform.UNKNOWN


def is_wayland() -> bool:
    """Check if running on Wayland (Linux only)."""
    if get_platform() != Platform.LINUX:
        return False
    import os
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def is_x11() -> bool:
    """Check if running on X11 (Linux only)."""
    if get_platform() != Platform.LINUX:
        return False
    import os
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    # If not explicitly wayland, assume X11 on Linux
    return session_type != "wayland"


@dataclass
class ScreenInfo:
    """Information about a display/monitor."""
    id: int
    x: int
    y: int
    width: int
    height: int
    is_primary: bool = False
    name: str = ""
    
    def __repr__(self) -> str:
        primary = " (primary)" if self.is_primary else ""
        return f"Screen({self.name}{primary}: {self.width}x{self.height} at ({self.x}, {self.y}))"


@dataclass
class Point:
    """A 2D point."""
    x: int
    y: int
    
    def __iter__(self):
        yield self.x
        yield self.y
    
    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass 
class Rect:
    """A rectangle defined by position and size."""
    x: int
    y: int
    width: int
    height: int
    
    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)
    
    @property
    def center(self) -> Point:
        return Point(self.x + self.width // 2, self.y + self.height // 2)


# Current platform
CURRENT_PLATFORM = get_platform()

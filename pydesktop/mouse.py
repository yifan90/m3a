"""
Mouse control: click, move, drag, scroll.

Uses `pynput` for cross-platform mouse control.
"""

import time
from typing import Optional, Tuple, Literal

try:
    from pynput.mouse import Button, Controller as MouseController
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

from .common import Point, CURRENT_PLATFORM, Platform


# Button type hint
ButtonType = Literal["left", "right", "middle"]


def _ensure_pynput():
    """Ensure pynput is available."""
    if not HAS_PYNPUT:
        raise ImportError(
            "pynput is required for mouse control. "
            "Install it with: pip install pynput"
        )


def _get_button(button: ButtonType) -> "Button":
    """Convert button name to pynput Button."""
    buttons = {
        "left": Button.left,
        "right": Button.right,
        "middle": Button.middle,
    }
    if button not in buttons:
        raise ValueError(f"Unknown button: {button}. Use 'left', 'right', or 'middle'.")
    return buttons[button]


def _get_controller() -> "MouseController":
    """Get mouse controller instance."""
    _ensure_pynput()
    return MouseController()


def _to_global(x: int, y: int, screen: Optional[int]) -> Tuple[int, int]:
    """Convert screen-local coordinates to global virtual screen coordinates."""
    if screen is None:
        return x, y
    from . import screen as _screen
    offset_x, offset_y = _screen.get_screen_offset(screen)
    return x + offset_x, y + offset_y


def _from_global(gx: int, gy: int, screen: Optional[int]) -> Tuple[int, int]:
    """Convert global virtual screen coordinates to screen-local coordinates."""
    if screen is None:
        return gx, gy
    from . import screen as _screen
    offset_x, offset_y = _screen.get_screen_offset(screen)
    return gx - offset_x, gy - offset_y


def get_position(screen: Optional[int] = 0) -> Tuple[int, int]:
    """
    Get the current mouse cursor position.

    Args:
        screen: Screen index for coordinate space (0=primary, None=global).

    Returns:
        Tuple of (x, y) coordinates relative to the specified screen.

    Example:
        >>> x, y = get_position()  # Relative to primary monitor
        >>> x, y = get_position(screen=None)  # Global coordinates
    """
    controller = _get_controller()
    pos = controller.position
    gx, gy = int(pos[0]), int(pos[1])
    return _from_global(gx, gy, screen)


def move_to(x: int, y: int, screen: int = 0):
    """
    Move the mouse cursor to coordinates on a screen.

    Args:
        x: X coordinate (pixels from screen left).
        y: Y coordinate (pixels from screen top).
        screen: Screen index (0=primary, 1+=others).

    Example:
        >>> move_to(100, 200)  # Move to (100, 200) on primary
        >>> move_to(100, 200, screen=1)  # On second monitor
    """
    controller = _get_controller()
    gx, gy = _to_global(x, y, screen)
    controller.position = (gx, gy)


def move_relative(dx: int, dy: int):
    """
    Move the mouse cursor relative to its current position.

    Args:
        dx: Horizontal movement (positive = right).
        dy: Vertical movement (positive = down).

    Example:
        >>> move_relative(50, -30)  # Move 50 right, 30 up
    """
    controller = _get_controller()
    controller.move(dx, dy)


def click(
    button: ButtonType = "left",
    count: int = 1,
    x: Optional[int] = None,
    y: Optional[int] = None,
    screen: int = 0
):
    """
    Click the mouse button.

    Args:
        button: Which button to click ('left', 'right', 'middle').
        count: Number of clicks (1 = single, 2 = double, etc.).
        x: Optional X coordinate to click at.
        y: Optional Y coordinate to click at.
        screen: Screen index for coordinates (0=primary, 1+=others).

    Example:
        >>> click()  # Left click at current position
        >>> click("right")  # Right click
        >>> click(x=500, y=300)  # Click at (500, 300) on primary
        >>> click(x=500, y=300, screen=1)  # Click on second monitor
    """
    controller = _get_controller()
    btn = _get_button(button)

    # Move to position if specified
    if x is not None and y is not None:
        gx, gy = _to_global(x, y, screen)
        controller.position = (gx, gy)
    elif x is not None or y is not None:
        raise ValueError("Both x and y must be specified, or neither.")

    controller.click(btn, count)


def double_click(
    button: ButtonType = "left",
    x: Optional[int] = None,
    y: Optional[int] = None,
    screen: int = 0
):
    """
    Double-click the mouse button.

    Args:
        button: Which button to double-click.
        x: Optional X coordinate.
        y: Optional Y coordinate.
        screen: Screen index (0=primary, 1+=others).
    """
    click(button=button, count=2, x=x, y=y, screen=screen)


def right_click(x: Optional[int] = None, y: Optional[int] = None, screen: int = 0):
    """
    Right-click the mouse.

    Args:
        x: Optional X coordinate.
        y: Optional Y coordinate.
        screen: Screen index (0=primary, 1+=others).
    """
    click(button="right", x=x, y=y, screen=screen)


def middle_click(x: Optional[int] = None, y: Optional[int] = None, screen: int = 0):
    """
    Middle-click the mouse.

    Args:
        x: Optional X coordinate.
        y: Optional Y coordinate.
        screen: Screen index (0=primary, 1+=others).
    """
    click(button="middle", x=x, y=y, screen=screen)


def mouse_down(button: ButtonType = "left"):
    """
    Press and hold a mouse button.

    Args:
        button: Which button to press.

    Example:
        >>> mouse_down()  # Hold left button
        >>> move_relative(100, 0)  # Drag
        >>> mouse_up()  # Release
    """
    controller = _get_controller()
    btn = _get_button(button)
    controller.press(btn)


def mouse_up(button: ButtonType = "left"):
    """
    Release a mouse button.

    Args:
        button: Which button to release.
    """
    controller = _get_controller()
    btn = _get_button(button)
    controller.release(btn)


def drag_to(
    x: int,
    y: int,
    button: ButtonType = "left",
    duration: float = 0.0,
    steps: int = 10,
    screen: int = 0
):
    """
    Drag from current position to target position.

    Args:
        x: Target X coordinate.
        y: Target Y coordinate.
        button: Which button to use for dragging.
        duration: Time in seconds for the drag operation.
        steps: Number of intermediate steps for smooth movement.
        screen: Screen index for target coordinates (0=primary).

    Example:
        >>> move_to(100, 100)
        >>> drag_to(300, 300)  # Drag from (100,100) to (300,300)
    """
    controller = _get_controller()
    btn = _get_button(button)

    gx, gy = _to_global(x, y, screen)
    start_x, start_y = controller.position
    start_x, start_y = int(start_x), int(start_y)

    controller.press(btn)

    if duration > 0 and steps > 1:
        step_delay = duration / steps
        dx = (gx - start_x) / steps
        dy = (gy - start_y) / steps

        for i in range(1, steps + 1):
            new_x = int(start_x + dx * i)
            new_y = int(start_y + dy * i)
            controller.position = (new_x, new_y)
            time.sleep(step_delay)
    else:
        controller.position = (gx, gy)

    controller.release(btn)


def drag_relative(
    dx: int,
    dy: int,
    button: ButtonType = "left",
    duration: float = 0.0,
    steps: int = 10
):
    """
    Drag from current position by a relative amount.

    Args:
        dx: Horizontal distance to drag.
        dy: Vertical distance to drag.
        button: Which button to use.
        duration: Time in seconds for the drag.
        steps: Number of intermediate steps.

    Example:
        >>> drag_relative(100, 50)  # Drag 100 right and 50 down
    """
    controller = _get_controller()
    btn = _get_button(button)

    start_x, start_y = controller.position
    start_x, start_y = int(start_x), int(start_y)
    target_x, target_y = start_x + dx, start_y + dy

    controller.press(btn)

    if duration > 0 and steps > 1:
        step_delay = duration / steps
        step_dx = dx / steps
        step_dy = dy / steps

        for i in range(1, steps + 1):
            new_x = int(start_x + step_dx * i)
            new_y = int(start_y + step_dy * i)
            controller.position = (new_x, new_y)
            time.sleep(step_delay)
    else:
        controller.position = (target_x, target_y)

    controller.release(btn)


def scroll(dx: int = 0, dy: int = 0):
    """
    Scroll the mouse wheel.

    Args:
        dx: Horizontal scroll (positive = right, negative = left).
        dy: Vertical scroll (positive = down, negative = up).

    Example:
        >>> scroll(dy=-3)  # Scroll up 3 "clicks"
        >>> scroll(dy=3)   # Scroll down 3 "clicks"
    """
    controller = _get_controller()

    if dy != 0:
        controller.scroll(0, dy)

    if dx != 0:
        controller.scroll(dx, 0)


def scroll_up(amount: int = 3):
    """
    Scroll up.

    Args:
        amount: Number of scroll "clicks".
    """
    scroll(dy=amount)


def scroll_down(amount: int = 3):
    """
    Scroll down.

    Args:
        amount: Number of scroll "clicks".
    """
    scroll(dy=-amount)


# Convenience functions for common operations
def click_at(x: int, y: int, button: ButtonType = "left", screen: int = 0):
    """
    Click at specific coordinates.

    Args:
        x: X coordinate.
        y: Y coordinate.
        button: Which button to click.
        screen: Screen index (0=primary, 1+=others).
    """
    click(button=button, x=x, y=y, screen=screen)


def double_click_at(x: int, y: int, button: ButtonType = "left", screen: int = 0):
    """
    Double-click at specific coordinates.

    Args:
        x: X coordinate.
        y: Y coordinate.
        button: Which button to double-click.
        screen: Screen index (0=primary, 1+=others).
    """
    double_click(button=button, x=x, y=y, screen=screen)


def right_click_at(x: int, y: int, screen: int = 0):
    """
    Right-click at specific coordinates.

    Args:
        x: X coordinate.
        y: Y coordinate.
        screen: Screen index (0=primary, 1+=others).
    """
    right_click(x=x, y=y, screen=screen)

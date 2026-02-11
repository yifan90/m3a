"""
Screen operations: resolution, screenshots, display info.

Uses `mss` for cross-platform screen capture.
"""

from typing import Optional, Tuple, List, Union
from io import BytesIO

try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .common import ScreenInfo, Rect


def _ensure_mss():
    """Ensure mss is available."""
    if not HAS_MSS:
        raise ImportError(
            "mss is required for screen operations. "
            "Install it with: pip install mss"
        )


def _ensure_pil():
    """Ensure PIL is available."""
    if not HAS_PIL:
        raise ImportError(
            "Pillow is required for image operations. "
            "Install it with: pip install Pillow"
        )


def _get_monitor(screen: Optional[int], sct) -> dict:
    """
    Get mss monitor dict for a screen index.

    Args:
        screen: Screen index (0=primary, 1+=others, None=all monitors combined).
        sct: mss instance.
    """
    if screen is None:
        return sct.monitors[0]  # All monitors combined

    # screen 0 -> mss monitors[1] (primary), screen 1 -> mss monitors[2], ...
    mss_index = screen + 1
    if mss_index >= len(sct.monitors):
        raise IndexError(
            f"Screen {screen} not found. "
            f"Available screens: 0-{len(sct.monitors) - 2}"
        )
    return sct.monitors[mss_index]


def get_screen_size(screen: int = 0) -> Tuple[int, int]:
    """
    Get the size of a screen.

    Args:
        screen: Screen index (0=primary, 1+=others).

    Returns:
        Tuple of (width, height) in pixels.

    Example:
        >>> width, height = get_screen_size()
        >>> print(f"Primary: {width}x{height}")
        >>> w2, h2 = get_screen_size(1)  # Second monitor
    """
    _ensure_mss()
    with mss.mss() as sct:
        mon = _get_monitor(screen, sct)
        return (mon["width"], mon["height"])


def get_screen_offset(screen: int = 0) -> Tuple[int, int]:
    """
    Get the origin offset of a screen in virtual screen coordinates.

    Args:
        screen: Screen index (0=primary, 1+=others).

    Returns:
        Tuple of (x, y) offset in pixels.
    """
    _ensure_mss()
    with mss.mss() as sct:
        mon = _get_monitor(screen, sct)
        return (mon["left"], mon["top"])


def get_all_screens() -> List[ScreenInfo]:
    """
    Get information about all connected displays.

    Returns:
        List of ScreenInfo objects (0-indexed).

    Example:
        >>> screens = get_all_screens()
        >>> for s in screens:
        ...     print(f"{s.name}: {s.width}x{s.height}")
    """
    _ensure_mss()
    screens = []
    with mss.mss() as sct:
        # Skip monitor 0 (virtual screen containing all monitors)
        for i, mon in enumerate(sct.monitors[1:]):
            screen = ScreenInfo(
                id=i,
                x=mon["left"],
                y=mon["top"],
                width=mon["width"],
                height=mon["height"],
                is_primary=(i == 0),
                name=f"Screen {i}"
            )
            screens.append(screen)
    return screens


def get_virtual_screen_size() -> Tuple[int, int, int, int]:
    """
    Get the bounding box of all screens combined.

    Returns:
        Tuple of (x, y, width, height) for the virtual screen.
    """
    _ensure_mss()
    with mss.mss() as sct:
        mon = sct.monitors[0]
        return (mon["left"], mon["top"], mon["width"], mon["height"])


def screenshot(
    region: Optional[Union[Tuple[int, int, int, int], Rect]] = None,
    screen: Optional[int] = 0
) -> "Image.Image":
    """
    Capture a screenshot.

    Args:
        region: Optional region as (x, y, width, height) in screen-local coords.
        screen: Screen index (0=primary, 1+=others, None=all monitors combined).

    Returns:
        PIL Image object.

    Example:
        >>> img = screenshot()  # Primary monitor
        >>> img = screenshot(screen=1)  # Second monitor
        >>> img = screenshot(screen=None)  # All monitors combined
        >>> img = screenshot(region=(100, 100, 400, 300))  # Region on primary
    """
    _ensure_mss()
    _ensure_pil()

    with mss.mss() as sct:
        if region is not None:
            if isinstance(region, Rect):
                region = region.as_tuple()

            x, y, w, h = region
            # Offset region to screen's global position
            if screen is not None:
                mon = _get_monitor(screen, sct)
                x += mon["left"]
                y += mon["top"]
            monitor_dict = {
                "left": x,
                "top": y,
                "width": w,
                "height": h
            }
        else:
            mon = _get_monitor(screen, sct)
            monitor_dict = {
                "left": mon["left"],
                "top": mon["top"],
                "width": mon["width"],
                "height": mon["height"]
            }

        sct_img = sct.grab(monitor_dict)

        img = Image.frombytes(
            "RGB",
            (sct_img.width, sct_img.height),
            sct_img.rgb
        )

        return img


def screenshot_to_bytes(
    region: Optional[Union[Tuple[int, int, int, int], Rect]] = None,
    screen: Optional[int] = 0,
    format: str = "PNG"
) -> bytes:
    """
    Capture a screenshot and return as bytes.

    Args:
        region: Optional region as (x, y, width, height).
        screen: Screen index (0=primary, 1+=others, None=all monitors).
        format: Image format (PNG, JPEG, etc.).

    Returns:
        Image data as bytes.
    """
    img = screenshot(region=region, screen=screen)
    buffer = BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


def screenshot_to_file(
    filepath: str,
    region: Optional[Union[Tuple[int, int, int, int], Rect]] = None,
    screen: Optional[int] = 0
) -> str:
    """
    Capture a screenshot and save to file.

    Args:
        filepath: Path to save the screenshot.
        region: Optional region to capture.
        screen: Screen index (0=primary, 1+=others, None=all monitors).

    Returns:
        The filepath where the image was saved.
    """
    img = screenshot(region=region, screen=screen)
    img.save(filepath)
    return filepath

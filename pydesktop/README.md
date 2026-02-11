# PyDesktop

Lightweight cross-platform desktop automation library. Screen capture, mouse control, keyboard input — with multi-monitor support.

## Features

- **Screen Operations**: Get screen resolution, capture screenshots, multi-monitor support
- **Mouse Control**: Click, double-click, right-click, drag, scroll (screen-aware)
- **Keyboard Control**: Key press, key combinations, text typing

## Supported Platforms

- Linux (X11; Wayland support planned)
- Windows
- macOS

## Installation

```bash
pip install -e .
```

## Quick Start

### Screen Operations

```python
from pydesktop import screen

# Get primary screen size
width, height = screen.get_screen_size()

# Get second monitor size
w2, h2 = screen.get_screen_size(screen=1)

# List all monitors
for s in screen.get_all_screens():
    print(f"Screen {s.id}: {s.width}x{s.height} at ({s.x}, {s.y})")

# Screenshot primary monitor (default)
img = screen.screenshot()
img.save("primary.png")

# Screenshot a specific monitor
img = screen.screenshot(screen=1)

# Screenshot all monitors combined
img = screen.screenshot(screen=None)

# Screenshot a region on primary monitor (screen-local coordinates)
img = screen.screenshot(region=(100, 100, 400, 300))

# Screenshot a region on second monitor
img = screen.screenshot(region=(0, 0, 400, 300), screen=1)

# Get screen offset in virtual desktop
offset_x, offset_y = screen.get_screen_offset(1)
```

### Mouse Control

```python
from pydesktop import mouse

# Get position relative to primary screen (default)
x, y = mouse.get_position()

# Get position relative to second monitor
x, y = mouse.get_position(screen=1)

# Get global virtual desktop position
x, y = mouse.get_position(screen=None)

# Move to coordinates on primary screen
mouse.move_to(500, 300)

# Move to coordinates on second monitor
mouse.move_to(500, 300, screen=1)

# Click on primary screen
mouse.click()
mouse.click("right")
mouse.double_click()

# Click at position on a specific screen
mouse.click_at(500, 300)
mouse.click_at(500, 300, screen=1)

# Drag (screen-aware)
mouse.move_to(100, 100)
mouse.drag_to(300, 300)
mouse.drag_to(500, 500, duration=0.5)

# Relative operations (no screen param needed)
mouse.move_relative(100, 50)
mouse.drag_relative(200, 0)
mouse.scroll(dy=3)
mouse.scroll(dy=-3)
```

### Keyboard Control

```python
from pydesktop import keyboard

# Press single key
keyboard.press('a')
keyboard.press('enter')
keyboard.press('f5')

# Type text
keyboard.type_text("Hello, World!")

# Key combinations (hotkeys)
keyboard.hotkey('ctrl', 'c')  # Copy
keyboard.hotkey('ctrl', 'v')  # Paste
keyboard.hotkey('alt', 'tab')  # Switch window

# Hold and release keys
keyboard.key_down('shift')
keyboard.press('a')  # Types 'A'
keyboard.key_up('shift')

# Common shortcuts (platform-aware: Ctrl on Linux/Windows, Cmd on macOS)
keyboard.copy()
keyboard.paste()
keyboard.select_all()
keyboard.undo()
keyboard.save()
```

### Multi-Monitor Workflow

```python
from pydesktop import screen, mouse

# Enumerate monitors
screens = screen.get_all_screens()
for s in screens:
    print(f"Screen {s.id}: {s.width}x{s.height}, primary={s.is_primary}")

# Capture and analyze each screen independently
for s in screens:
    img = screen.screenshot(screen=s.id)
    img.save(f"screen_{s.id}.png")

# Move mouse between screens
mouse.move_to(960, 540, screen=0)  # Center of primary
mouse.move_to(960, 540, screen=1)  # Center of second monitor

# Coordinates are always screen-local
# (0, 0) is the top-left of the specified screen
mouse.click_at(0, 0, screen=1)  # Top-left corner of second monitor
```

## API Reference

### screen module

| Function | Description |
|----------|-------------|
| `get_screen_size(screen=0)` | Returns (width, height) of specified screen |
| `get_screen_offset(screen=0)` | Returns (x, y) offset in virtual desktop |
| `get_all_screens()` | Returns list of ScreenInfo (0-indexed) |
| `get_virtual_screen_size()` | Returns bounding box of all screens combined |
| `screenshot(region, screen=0)` | Capture screenshot, returns PIL Image |
| `screenshot_to_bytes(...)` | Capture screenshot as PNG bytes |
| `screenshot_to_file(filepath, ...)` | Save screenshot to file |

`screen` parameter: `0` = primary, `1+` = others, `None` = all monitors combined.

### mouse module

| Function | Description |
|----------|-------------|
| `get_position(screen=0)` | Returns (x, y) relative to specified screen |
| `move_to(x, y, screen=0)` | Move to screen-local coordinates |
| `move_relative(dx, dy)` | Move relative to current position |
| `click(button, count, x, y, screen=0)` | Click mouse button |
| `double_click(...)` | Double-click |
| `right_click(...)` | Right-click |
| `mouse_down(button)` | Press and hold button |
| `mouse_up(button)` | Release button |
| `drag_to(x, y, ..., screen=0)` | Drag to screen-local position |
| `drag_relative(dx, dy, ...)` | Drag by relative amount |
| `scroll(dx, dy)` | Scroll mouse wheel |

### keyboard module

| Function | Description |
|----------|-------------|
| `press(key)` | Press and release a key |
| `key_down(key)` | Press and hold a key |
| `key_up(key)` | Release a key |
| `hotkey(*keys)` | Press key combination |
| `type_text(text, interval)` | Type text string |
| `copy()`, `paste()`, etc. | Common shortcuts (platform-aware) |

## Key Names

Special keys for keyboard functions:

- Modifiers: `ctrl`, `alt`, `shift`, `meta`, `cmd`, `win`
- Function keys: `f1` - `f12`
- Navigation: `up`, `down`, `left`, `right`, `home`, `end`, `pageup`, `pagedown`
- Editing: `enter`, `tab`, `space`, `backspace`, `delete`, `insert`
- Other: `escape`, `capslock`, `numlock`, `printscreen`, `pause`

## License

MIT License

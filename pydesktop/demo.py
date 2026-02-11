#!/usr/bin/env python3
"""
Demo script for pydesktop library.

Run with: python -m pydesktop.demo
"""

import sys
import time


def demo_screen():
    """Demonstrate screen operations."""
    print("\n" + "=" * 50)
    print("SCREEN OPERATIONS DEMO")
    print("=" * 50)

    from pydesktop import screen

    # Get primary screen size
    width, height = screen.get_screen_size()
    print(f"\nPrimary screen size: {width}x{height}")

    # Get all screens
    screens = screen.get_all_screens()
    print(f"\nFound {len(screens)} monitor(s):")
    for s in screens:
        print(f"  - {s}")

    # Take a screenshot of primary monitor
    print("\nTaking screenshot of primary monitor (screen=0)...")
    img = screen.screenshot()
    filename = "/tmp/pydesktop_demo_screenshot.png"
    img.save(filename)
    print(f"  Saved to: {filename}")
    print(f"  Size: {img.width}x{img.height}")

    # Screenshot of a region on primary monitor
    print("\nTaking regional screenshot (top-left 200x200 on primary)...")
    img_region = screen.screenshot(region=(0, 0, 200, 200))
    filename_region = "/tmp/pydesktop_demo_region.png"
    img_region.save(filename_region)
    print(f"  Saved to: {filename_region}")


def demo_multiscreen():
    """Demonstrate multi-screen operations."""
    print("\n" + "=" * 50)
    print("MULTI-SCREEN DEMO")
    print("=" * 50)

    from pydesktop import screen, mouse

    screens = screen.get_all_screens()
    if len(screens) < 2:
        print("\nOnly 1 monitor detected, skipping multi-screen demo.")
        print("  Connect a second monitor to see this demo in action.")
        return

    print(f"\nDetected {len(screens)} screens:")
    for s in screens:
        offset = screen.get_screen_offset(s.id)
        print(f"  Screen {s.id}: {s.width}x{s.height}, offset={offset}, primary={s.is_primary}")

    # Screenshot each screen
    for s in screens:
        print(f"\nScreenshot of screen {s.id}...")
        img = screen.screenshot(screen=s.id)
        filename = f"/tmp/pydesktop_demo_screen{s.id}.png"
        img.save(filename)
        print(f"  Saved to: {filename} ({img.width}x{img.height})")

    # Screenshot all monitors combined
    print("\nScreenshot of all monitors combined (screen=None)...")
    img_all = screen.screenshot(screen=None)
    filename_all = "/tmp/pydesktop_demo_all_screens.png"
    img_all.save(filename_all)
    print(f"  Saved to: {filename_all} ({img_all.width}x{img_all.height})")

    # Mouse position on different screens
    gx, gy = mouse.get_position(screen=None)
    print(f"\nMouse global position: ({gx}, {gy})")
    for s in screens:
        lx, ly = mouse.get_position(screen=s.id)
        print(f"  Relative to screen {s.id}: ({lx}, {ly})")

    # Move mouse to center of each screen
    original_pos = mouse.get_position(screen=None)
    for s in screens:
        cx, cy = s.width // 2, s.height // 2
        print(f"\nMoving mouse to center of screen {s.id}: ({cx}, {cy})")
        mouse.move_to(cx, cy, screen=s.id)
        time.sleep(0.8)

    # Restore original position
    mouse.move_to(original_pos[0], original_pos[1], screen=None)
    print("\nMouse restored to original position.")


def demo_mouse():
    """Demonstrate mouse operations."""
    print("\n" + "=" * 50)
    print("MOUSE OPERATIONS DEMO")
    print("=" * 50)

    from pydesktop import mouse, screen

    # Get current position (relative to primary screen)
    x, y = mouse.get_position()
    print(f"\nCurrent mouse position (screen 0): ({x}, {y})")

    # Move mouse to center of primary screen
    print("\nMoving mouse to center of primary screen...")
    w, h = screen.get_screen_size()
    center_x, center_y = w // 2, h // 2

    original_pos = mouse.get_position()
    mouse.move_to(center_x, center_y)
    print(f"  Moved to: ({center_x}, {center_y})")

    time.sleep(0.5)

    # Move relative
    print("\nMoving mouse relative (+100, +50)...")
    mouse.move_relative(100, 50)
    new_pos = mouse.get_position()
    print(f"  New position: {new_pos}")

    time.sleep(0.5)

    # Move back to original
    print(f"\nMoving back to original position: {original_pos}")
    mouse.move_to(*original_pos)

    print("\n[Note: Click operations not demonstrated to avoid unwanted actions]")


def demo_keyboard():
    """Demonstrate keyboard operations."""
    print("\n" + "=" * 50)
    print("KEYBOARD OPERATIONS DEMO")
    print("=" * 50)

    from pydesktop import keyboard

    print("\nKeyboard module loaded successfully")
    print("\n[Note: Keyboard actions not demonstrated to avoid unwanted input]")
    print("  Available functions:")
    print("  - keyboard.press('key')           # Press single key")
    print("  - keyboard.type_text('text')      # Type text")
    print("  - keyboard.hotkey('ctrl', 'c')    # Key combination")
    print("  - keyboard.copy(), paste(), etc.  # Common shortcuts")


def main():
    """Run all demos."""
    print("=" * 50)
    print("       PyDesktop Library Demo")
    print("=" * 50)

    # Check dependencies
    print("\nChecking dependencies...")

    missing = []
    try:
        import mss
        print("  mss installed")
    except ImportError:
        missing.append("mss")
        print("  mss NOT installed")

    try:
        from pynput.mouse import Controller
        print("  pynput installed")
    except ImportError:
        missing.append("pynput")
        print("  pynput NOT installed")

    try:
        from PIL import Image
        print("  Pillow installed")
    except ImportError:
        missing.append("Pillow")
        print("  Pillow NOT installed")

    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print(f"  Install with: pip install {' '.join(missing)}")
        return 1

    # Run demos
    try:
        demo_screen()
        demo_multiscreen()
        demo_mouse()
        demo_keyboard()

        print("\n" + "=" * 50)
        print("       Demo Complete!")
        print("=" * 50)
        print("\nLibrary is ready to use. See README.md for full documentation.")
        return 0

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

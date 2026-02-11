"""
Action Executor - Execute actions using pydesktop.
"""

import time
import sys
import os
from typing import List, Tuple, Optional, Callable

# Add pydesktop to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydesktop import mouse, keyboard
from .models import Action, UIElement


class ActionExecutor:
    """Executes actions using pydesktop."""

    SCROLL_AMOUNT = 5
    WAIT_SECONDS = 1.0

    def __init__(self, screen: int = 0):
        self.screen = screen
        # Callbacks for user interaction
        self.ask_user_callback: Optional[Callable[[str], str]] = None
        self.talk_to_user_callback: Optional[Callable[[str], None]] = None

    def set_user_callbacks(
        self,
        ask_user: Optional[Callable[[str], str]] = None,
        talk_to_user: Optional[Callable[[str], None]] = None,
    ):
        """Set callbacks for user interaction.

        Args:
            ask_user: Callback that takes a question string and returns user's response
            talk_to_user: Callback that takes a message string and shows it to user
        """
        self.ask_user_callback = ask_user
        self.talk_to_user_callback = talk_to_user

    def _get_screen(self, action: Action) -> int:
        """Get screen index for an action (action override > default)."""
        return action.screen if action.screen is not None else self.screen

    def execute(self, action: Action, ui_elements: List[UIElement]) -> bool:
        """
        Execute an action.

        Returns:
            True if action was executed, False if it's a terminal action
        """
        action_type = action.action_type

        if action_type == "status":
            return False  # Terminal action

        if action_type == "answer":
            print(f"Agent answer: {action.text}")
            if self.talk_to_user_callback:
                self.talk_to_user_callback(action.text)
            return False  # Terminal action

        if action_type == "talk_to_user":
            print(f"Agent message: {action.text}")
            if self.talk_to_user_callback:
                self.talk_to_user_callback(action.text)
            return True  # Continue after showing message

        if action_type == "ask_user":
            question = action.question or "Agent needs input"
            print(f"Agent asks: {question}")
            if self.ask_user_callback:
                response = self.ask_user_callback(question)
                action.user_response = response
                print(f"User response: {response}")
            return True  # Continue after getting response

        if action_type == "wait":
            time.sleep(self.WAIT_SECONDS)
            return True

        screen = self._get_screen(action)

        if action_type == "click":
            x, y = self._get_coords(action, ui_elements)
            mouse.click_at(x, y, screen=screen)

        elif action_type == "double_click":
            x, y = self._get_coords(action, ui_elements)
            mouse.double_click_at(x, y, screen=screen)

        elif action_type == "right_click":
            x, y = self._get_coords(action, ui_elements)
            mouse.right_click_at(x, y, screen=screen)

        elif action_type == "input_text":
            # Click on element first, then type
            if action.index is not None:
                x, y = self._get_coords(action, ui_elements)
                mouse.click_at(x, y, screen=screen)
                time.sleep(0.3)
            keyboard.type_text(action.text)

        elif action_type == "type":
            keyboard.type_text(action.text)

        elif action_type == "press_key":
            keyboard.press(action.key)

        elif action_type == "hotkey":
            keyboard.hotkey(*action.keys)

        elif action_type == "scroll":
            direction = action.direction.lower()

            # Move to element if specified
            if action.index is not None:
                x, y = self._get_coords(action, ui_elements)
                mouse.move_to(x, y, screen=screen)

            if direction == "up":
                mouse.scroll_up(self.SCROLL_AMOUNT)
            elif direction == "down":
                mouse.scroll_down(self.SCROLL_AMOUNT)
            elif direction == "left":
                mouse.scroll(dx=-self.SCROLL_AMOUNT, dy=0)
            elif direction == "right":
                mouse.scroll(dx=self.SCROLL_AMOUNT, dy=0)

        elif action_type == "drag":
            x, y = self._get_coords(action, ui_elements)
            mouse.move_to(x, y, screen=screen)
            mouse.drag_to(action.x, action.y, duration=0.5, screen=screen)

        else:
            print(f"Unknown action type: {action_type}")

        return True

    def _get_coords(self, action: Action, ui_elements: List[UIElement]) -> Tuple[int, int]:
        """Get coordinates for an action."""
        if action.index is not None:
            if 0 <= action.index < len(ui_elements):
                return ui_elements[action.index].center
            else:
                raise ValueError(f"Invalid element index: {action.index}")
        elif action.x is not None and action.y is not None:
            return (action.x, action.y)
        else:
            raise ValueError("Action requires either index or x,y coordinates")

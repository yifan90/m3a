"""
Data Models - Data structures used by the agent.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

from PIL import Image


@dataclass
class UIElement:
    """Represents a UI element detected by OmniParser."""
    index: int
    type: str  # "text" or "icon"
    content: str
    bbox: Tuple[int, int, int, int]  # (x, y, width, height) in pixels
    center: Tuple[int, int]  # (x, y) center point
    is_clickable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "type": self.type,
            "content": self.content,
            "bbox": self.bbox,
            "center": self.center,
            "is_clickable": self.is_clickable,
        }


@dataclass
class Action:
    """Represents an action to be executed."""
    action_type: str
    index: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    direction: Optional[str] = None  # up, down, left, right
    key: Optional[str] = None
    keys: Optional[List[str]] = None  # for hotkey
    goal_status: Optional[str] = None  # complete, infeasible
    question: Optional[str] = None  # for ask_user
    user_response: Optional[str] = None  # response from user
    screen: Optional[int] = None  # target screen (None = use agent default)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Action":
        return cls(
            action_type=d.get("action_type"),
            index=d.get("index"),
            x=d.get("x"),
            y=d.get("y"),
            text=d.get("text"),
            direction=d.get("direction"),
            key=d.get("key"),
            keys=d.get("keys"),
            goal_status=d.get("goal_status"),
            question=d.get("question"),
            user_response=d.get("user_response"),
            screen=d.get("screen"),
        )


@dataclass
class StepResult:
    """Result of a single agent step."""
    action: Action
    reason: str
    summary: str
    before_screenshot: Image.Image
    after_screenshot: Image.Image
    ui_elements: List[UIElement]
    done: bool = False
    raw_response: str = ""

"""
Computer Use Agent - Vision-based desktop automation.

Uses OmniParser server for screen understanding and pydesktop for actions.
"""

from .core import ComputerUseAgent
from .models import Action, StepResult, UIElement
from .llm import BaseLLM, OpenAICompatibleLLM
from .omniparser import OmniParserClient

__all__ = [
    "ComputerUseAgent",
    "Action",
    "StepResult",
    "UIElement",
    "BaseLLM",
    "OpenAICompatibleLLM",
    "OmniParserClient",
]

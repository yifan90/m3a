"""
Computer Use Agent - Core agent implementation.
"""

import json
import time
import re
from typing import Optional, List, Dict, Any

from PIL import Image

from .models import UIElement, Action, StepResult
from .llm import BaseLLM
from .omniparser import OmniParserClient
from .executor import ActionExecutor
from .prompts import SYSTEM_PROMPT, SUMMARY_PROMPT


class ComputerUseAgent:
    """
    Vision-based computer automation agent.

    Similar to M3A but for desktop, using OmniParser for screen understanding.
    """

    WAIT_AFTER_ACTION = 1.5  # seconds to wait after action
    MAX_STEPS = 50

    def __init__(
        self,
        llm: BaseLLM,
        omniparser: OmniParserClient,
        additional_guidelines: str = "",
        ask_user_callback=None,
        talk_to_user_callback=None,
        screen: int = 0,
    ):
        """
        Initialize the agent.

        Args:
            llm: LLM instance for decision making
            omniparser: OmniParser client (connects to remote server)
            additional_guidelines: Extra instructions for the LLM
            ask_user_callback: Callback for asking user questions (returns response)
            talk_to_user_callback: Callback for showing messages to user
            screen: Screen index to operate on (0=primary, 1+=others)
        """
        self.llm = llm
        self.omniparser = omniparser
        self.screen = screen
        self.executor = ActionExecutor(screen=screen)
        self.additional_guidelines = additional_guidelines

        # Set user interaction callbacks
        self.executor.set_user_callbacks(
            ask_user=ask_user_callback,
            talk_to_user=talk_to_user_callback,
        )

        self.history: List[Dict[str, Any]] = []
        self.goal: str = ""

    def reset(self):
        """Reset the agent state."""
        self.history = []
        self.goal = ""

    def _get_screenshot(self) -> Image.Image:
        """Capture current screen."""
        # Import here to avoid circular dependency
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from pydesktop import screen
        return screen.screenshot(screen=self.screen)

    def _build_prompt(self, ui_elements: List[UIElement]) -> str:
        """Build the action selection prompt."""
        # Format history
        if self.history:
            history_parts = []
            for i, step in enumerate(self.history):
                part = f"Step {i+1}: {step['summary']}"
                # Include user response if available (from ask_user action)
                action = step.get('action')
                if action and action.user_response:
                    part += f" [User responded: {action.user_response}]"
                history_parts.append(part)
            history_str = "\n".join(history_parts)
        else:
            history_str = "(No actions taken yet)"

        # Format UI elements
        elements_str = "\n".join([
            f"Element {e.index}: type={e.type}, content=\"{e.content[:50]}...\", center={e.center}"
            if len(e.content) > 50 else
            f"Element {e.index}: type={e.type}, content=\"{e.content}\", center={e.center}"
            for e in ui_elements
        ])

        prompt = f"""{SYSTEM_PROMPT.format(screen=self.screen)}

CURRENT GOAL: {self.goal}

HISTORY:
{history_str}

DETECTED UI ELEMENTS:
{elements_str}

{self.additional_guidelines}

Now analyze the screenshot and choose an action.
Your Answer:
"""
        return prompt

    def _parse_response(self, response: str) -> tuple[str, Action]:
        """Parse LLM response to extract reason and action."""
        # Extract reason
        reason_match = re.search(r'Reason:\s*(.+?)(?=\nAction:|$)', response, re.DOTALL)
        reason = reason_match.group(1).strip() if reason_match else ""

        # Extract action JSON
        action_match = re.search(r'Action:\s*(\{.+?\})', response, re.DOTALL)
        if not action_match:
            # Try to find any JSON in the response
            json_match = re.search(r'\{[^{}]+\}', response)
            if json_match:
                action_dict = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not find action JSON in response: {response}")
        else:
            action_dict = json.loads(action_match.group(1))

        action = Action.from_dict(action_dict)
        return reason, action

    def _generate_summary(
        self,
        before_img: Image.Image,
        after_img: Image.Image,
        action: Action,
        reason: str,
    ) -> str:
        """Generate a summary of the step."""
        prompt = SUMMARY_PROMPT.format(
            action=json.dumps(action.__dict__),
            reason=reason,
        )

        summary, _ = self.llm.predict(prompt, images=[before_img, after_img])
        return summary.strip()

    def step(self, goal: str) -> StepResult:
        """Execute one step toward the goal."""
        self.goal = goal

        # 1. Capture screenshot and parse UI
        before_screenshot = self._get_screenshot()
        labeled_img, ui_elements = self.omniparser.parse(before_screenshot)

        # 2. Build prompt and call LLM
        prompt = self._build_prompt(ui_elements)
        response, raw = self.llm.predict(prompt, images=[labeled_img])

        # 3. Parse response
        reason, action = self._parse_response(response)
        print(f"\nReason: {reason}")
        print(f"Action: {action.action_type}")

        # 4. Execute action
        is_terminal = not self.executor.execute(action, ui_elements)

        # 5. Wait and capture after screenshot
        time.sleep(self.WAIT_AFTER_ACTION)
        after_screenshot = self._get_screenshot()

        # 6. Generate summary
        summary = self._generate_summary(before_screenshot, after_screenshot, action, reason)
        print(f"Summary: {summary}")

        # 7. Record to history
        step_data = {
            "action": action,
            "reason": reason,
            "summary": summary,
            "before_screenshot": before_screenshot,
            "after_screenshot": after_screenshot,
        }
        self.history.append(step_data)

        # 8. Check if done
        done = is_terminal or action.action_type == "status"

        return StepResult(
            action=action,
            reason=reason,
            summary=summary,
            before_screenshot=before_screenshot,
            after_screenshot=after_screenshot,
            ui_elements=ui_elements,
            done=done,
            raw_response=response,
        )

    def run(self, goal: str, max_steps: Optional[int] = None) -> List[StepResult]:
        """Run the agent until completion or max steps."""
        self.reset()
        max_steps = max_steps or self.MAX_STEPS
        results = []

        print(f"\n{'='*60}")
        print(f"Goal: {goal}")
        print(f"{'='*60}\n")

        for step_num in range(max_steps):
            print(f"\n--- Step {step_num + 1} ---")

            try:
                result = self.step(goal)
                results.append(result)

                if result.done:
                    print(f"\n{'='*60}")
                    print(f"Task completed after {step_num + 1} steps")
                    if result.action.goal_status:
                        print(f"Status: {result.action.goal_status}")
                    print(f"{'='*60}\n")
                    break

            except Exception as e:
                print(f"Error in step {step_num + 1}: {e}")
                raise
        else:
            print(f"\nMax steps ({max_steps}) reached without completion")

        return results

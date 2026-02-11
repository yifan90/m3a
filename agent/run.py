#!/usr/bin/env python3
"""
Computer Use Agent - Run script.

Usage:
    python -m agent.run "Open Firefox and search for Python"
    python -m agent.run --test http://localhost:8000
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import ComputerUseAgent, OpenAICompatibleLLM, OmniParserClient


# =============================================================================
# Configuration
# =============================================================================

LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY", "your-api-key-here")
LLM_MODEL = "qwen-plus"

OMNIPARSER_URL = "http://localhost:28256"

SYSTEM_GUIDELINES = """
- This is a Linux desktop with GNOME
- Common apps: Firefox, Files, Terminal, VS Code
- Use keyboard shortcuts when efficient (Ctrl+T for new tab, etc.)
"""


# =============================================================================
# Functions
# =============================================================================

def run_agent(goal: str, omniparser_url: str, screen: int = 0):
    """Run the agent with a goal."""
    print(f"Connecting to OmniParser: {omniparser_url}")
    omniparser = OmniParserClient(server_url=omniparser_url)

    if not omniparser.is_available():
        print("Error: OmniParser server not available")
        return

    print("Initializing LLM...")
    llm = OpenAICompatibleLLM(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        model=LLM_MODEL,
    )

    print(f"Operating on screen {screen}")
    agent = ComputerUseAgent(
        llm=llm,
        omniparser=omniparser,
        additional_guidelines=SYSTEM_GUIDELINES,
        screen=screen,
    )

    print(f"\nGoal: {goal}")
    print("Press Ctrl+C to stop.\n")

    try:
        results = agent.run(goal, max_steps=20)

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        for i, r in enumerate(results):
            print(f"  {i+1}. {r.summary}")

    except KeyboardInterrupt:
        print("\n\nInterrupted.")


def test_omniparser(server_url: str, screen_idx: int = 0):
    """Test OmniParser connection."""
    from pydesktop import screen

    print(f"Testing OmniParser at {server_url}...")

    client = OmniParserClient(server_url=server_url)
    health = client.health_check()
    print(f"Health: {health}")

    if not client.is_available():
        print("Server not available.")
        return

    print(f"Capturing screen {screen_idx}...")
    img = screen.screenshot(screen=screen_idx)
    print(f"Screenshot: {img.size}")

    labeled_img, elements = client.parse(img)
    print(f"Found {len(elements)} elements:")
    for e in elements[:10]:
        content = e.content[:40] + "..." if len(e.content) > 40 else e.content
        print(f"  [{e.index}] {e.type}: {content}")

    labeled_img.save("/tmp/agent_test.png")
    print(f"\nSaved to /tmp/agent_test.png")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Computer Use Agent")
    parser.add_argument("goal", nargs="*", help="Goal for the agent")
    parser.add_argument("--omniparser-url", default=OMNIPARSER_URL, help="OmniParser server URL")
    parser.add_argument("--screen", type=int, default=0, help="Screen index to operate on (0=primary)")
    parser.add_argument("--test", metavar="URL", nargs="?", const=OMNIPARSER_URL, help="Test OmniParser connection")
    args = parser.parse_args()

    if args.test:
        test_omniparser(args.test, screen_idx=args.screen)
    elif args.goal:
        run_agent(" ".join(args.goal), args.omniparser_url, screen=args.screen)
    else:
        print("Enter your goal:")
        goal = input("> ").strip()
        if goal:
            run_agent(goal, args.omniparser_url, screen=args.screen)


if __name__ == "__main__":
    main()

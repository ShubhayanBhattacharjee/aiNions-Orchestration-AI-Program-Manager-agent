import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

#Load .env if present 
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.models import InputMessage
from core.engine import NionOrchestrationEngine
from core.formatter import format_orchestration_map

#test cases
TEST_CASES = {
    1: {
        "name": "Simple Status Question",
        "data": {
            "message_id": "MSG-101",
            "source": "slack",
            "sender": {"name": "John Doe", "role": "Engineering Manager"},
            "content": "What's the status of the authentication feature?",
            "project": "PRJ-BETA",
        },
    },
    2: {
        "name": "Feasibility Question (New Features)",
        "data": {
            "message_id": "MSG-102",
            "source": "email",
            "sender": {"name": "Sarah Chen", "role": "Product Manager"},
            "content": "Can we add SSO integration before the December release?",
            "project": "PRJ-ALPHA",
        },
    },
    3: {
        "name": "Decision / Recommendation Request",
        "data": {
            "message_id": "MSG-103",
            "source": "email",
            "sender": {"name": "Mike Johnson", "role": "VP Engineering"},
            "content": "Should we prioritize security fixes or the new dashboard?",
            "project": "PRJ-GAMMA",
        },
    },
    4: {
        "name": "Meeting Transcript",
        "data": {
            "message_id": "MSG-104",
            "source": "meeting",
            "sender": {"name": "System", "role": "Meeting Bot"},
            "content": (
                "Dev: I'm blocked on API integration, staging is down. "
                "QA: Found 3 critical bugs in payment flow. "
                "Designer: Mobile mockups ready by Thursday. "
                "Tech Lead: We might need to refactor the auth module."
            ),
            "project": "PRJ-ALPHA",
        },
    },
    5: {
        "name": "Urgent Escalation",
        "data": {
            "message_id": "MSG-105",
            "source": "email",
            "sender": {"name": "Lisa Wong", "role": "Customer Success Manager"},
            "content": (
                "The client is asking why feature X promised for Q3 is still not delivered. "
                "They're threatening to escalate to legal. What happened?"
            ),
            "project": "PRJ-DELTA",
        },
    },
    6: {
        "name": "Ambiguous Request",
        "data": {
            "message_id": "MSG-106",
            "source": "slack",
            "sender": {"name": "Random User", "role": "Unknown"},
            "content": "We need to speed things up",
            "project": None,
        },
    },
    0: {
        "name": "Sample (from Assessment)",
        "data": {
            "message_id": "MSG-001",
            "source": "email",
            "sender": {"name": "Sarah Chen", "role": "Product Manager"},
            "content": (
                "The customer demo went great! They loved it but asked if we could add "
                "real-time notifications and a dashboard export feature. They're willing "
                "to pay 20% more and need it in the same timeline. Can we make this work?"
            ),
            "project": "PRJ-ALPHA",
        },
    },
}


def run_message(data: dict, engine: NionOrchestrationEngine, save: bool = True, test_name: str = "") -> str:
    """Process a single message and return the formatted output."""
    message = InputMessage.from_dict(data)
    result = engine.run(message)
    output = format_orchestration_map(result)
    print(output)
    if save:
        save_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
        save_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = test_name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
        filename = save_dir / f"{message.message_id}_{safe_name}_{ts}.txt"
        filename.write_text(output, encoding="utf-8")
        print(f"\n[Saved to: {filename}]")
    return output

def main():
    parser = argparse.ArgumentParser(
        description="Nion Orchestration Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", "-i", help="Path to JSON input file")
    parser.add_argument("--test", "-t", type=int, choices=list(TEST_CASES.keys()),
                        help="Run a specific test case by number (0=sample, 1-6=test cases)")
    parser.add_argument("--all", "-a", action="store_true", default=False,
                        help="Run all test cases (default if no args given)")
    parser.add_argument("--list-tests", action="store_true",
                        help="List all available test cases")
    parser.add_argument("--no-save", action="store_true",
                        help="Don't save output to files")
    parser.add_argument("--provider", "-p",
                        choices=["gemini", "groq", "openrouter", "anthropic", "openai", "mock"],
                        help="Override LLM provider from .env")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose logging")

    args = parser.parse_args()

    # Apply overrides
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.verbose:
        os.environ["VERBOSE"] = "true"

    # List tests
    if args.list_tests:
        print("\nAvailable test cases:")
        print(f"  {'#':<4} {'Message ID':<12} {'Name'}")
        print(f"  {'-'*4} {'-'*12} {'-'*40}")
        for num, tc in sorted(TEST_CASES.items()):
            mid = tc["data"]["message_id"]
            print(f"  {num:<4} {mid:<12} {tc['name']}")
        print("\nUsage: python main.py --test <number>")
        return

    save = not args.no_save
    provider = os.getenv("LLM_PROVIDER", "mock")
    print(f"\n{'='*78}")
    print(f"NION ORCHESTRATION ENGINE")
    print(f"Provider: {provider.upper()} | Save outputs: {save}")
    print(f"{'='*78}\n")

    engine = NionOrchestrationEngine()

    if args.input:
        # Run from JSON file
        path = Path(args.input)
        if not path.exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)
        data = json.loads(path.read_text(encoding="utf-8"))
        run_message(data, engine, save=save, test_name="custom")

    elif args.test is not None:
        # Run single test case
        tc = TEST_CASES[args.test]
        print(f"Running Test Case {args.test}: {tc['name']}\n")
        run_message(tc["data"], engine, save=save, test_name=tc["name"])

    else:
        # Run all test cases (default)
        cases = [0] + list(range(1, 7))  # sample + 6 test cases
        print(f"Running all {len(cases)} test cases...\n")
        for num in cases:
            tc = TEST_CASES[num]
            print(f"\n{'─'*78}")
            print(f"TEST CASE {num}: {tc['name']}")
            print(f"{'─'*78}\n")
            run_message(tc["data"], engine, save=save, test_name=tc["name"])
            print()

if __name__ == "__main__":
    main()

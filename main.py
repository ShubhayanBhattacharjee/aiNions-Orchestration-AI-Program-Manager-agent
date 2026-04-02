#!/usr/bin/env python3
# ============================================================
# main.py  –  CLI entry point
#
# Usage:
#   python main.py                          # uses default sample input
#   python main.py input.json               # reads from file
#   echo '{"message_id":...}' | python main.py   # reads from stdin
#   python main.py --all-tests              # runs all 6 test cases
# ============================================================

import json
import sys
import os

from src.engine        import NionEngine
from src.utils.renderer import render


def run_single(raw: dict, save_path: str = None) -> str:
    engine = NionEngine()
    result = engine.run(raw)
    output = render(result)
    print(output)
    if save_path:
        with open(save_path, "w") as f:
            f.write(output)
        print(f"\n[Saved to {save_path}]")
    return output


def run_all_tests():
    test_cases_dir = os.path.join(os.path.dirname(__file__), "test_cases")
    outputs_dir    = os.path.join(os.path.dirname(__file__), "sample_outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    test_files = sorted(
        [f for f in os.listdir(test_cases_dir) if f.endswith(".json")]
    )

    if not test_files:
        print("No test case JSON files found in test_cases/")
        sys.exit(1)

    for fname in test_files:
        path = os.path.join(test_cases_dir, fname)
        with open(path) as f:
            raw = json.load(f)

        print(f"\n{'#'*78}")
        print(f"# Running: {fname}")
        print(f"{'#'*78}\n")

        out_name = fname.replace(".json", ".txt")
        out_path = os.path.join(outputs_dir, out_name)
        run_single(raw, save_path=out_path)


def main():
    args = sys.argv[1:]

    if "--all-tests" in args:
        run_all_tests()
        return

    if args:
        # File path argument
        with open(args[0]) as f:
            raw = json.load(f)
        run_single(raw)
    elif not sys.stdin.isatty():
        # Piped stdin
        raw = json.load(sys.stdin)
        run_single(raw)
    else:
        # Default sample input (the assessment example)
        raw = {
            "message_id": "MSG-001",
            "source": "email",
            "sender": {
                "name": "Sarah Chen",
                "role": "Product Manager"
            },
            "content": (
                "The customer demo went great! They loved it but asked if we could add "
                "real-time notifications and a dashboard export feature. They're willing "
                "to pay 20% more and need it in the same timeline. Can we make this work?"
            ),
            "project": "PRJ-ALPHA"
        }
        run_single(raw)


if __name__ == "__main__":
    main()
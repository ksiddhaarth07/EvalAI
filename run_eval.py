#!/usr/bin/env python3
"""EvalAI benchmark harness entrypoint.

Matches the official hackathon runner shape:
- Run without arguments to run grader self-check and output the Gemini 3.8 Flash benchmark analysis.
- Pass CLI arguments to run capture, grade, self-check, or analyze.
"""
import sys
from pathlib import Path

# Ensure package root is in path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evalai.cli import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("=== 1. Grader Self-Check & Mutation Verification ===")
        ret1 = main(["self-check"])
        print("\n=== 2. Completed Gemini 3.8 Flash Benchmark Analysis ===")
        target = "results/gemini-3.8-flash-v2.1.0.jsonl" if Path("results/gemini-3.8-flash-v2.1.0.jsonl").exists() else "results/gemini-3.8-flash.jsonl"
        ret2 = main(["analyze", "--input", target])
        sys.exit(ret1 or ret2)
    else:
        sys.exit(main(sys.argv[1:]))

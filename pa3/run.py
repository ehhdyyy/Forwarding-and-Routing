#!/usr/bin/env python3
"""python run.py scenarios/s1_longest_prefix.json             run a scenario and write trace.txt
   python run.py scenarios/s1_longest_prefix.json --verbose   add '#' lines (lookups, vectors received, final tables)
   python run.py scenarios/s2_link_failure.json --dv-infinity none   run with the cap switched off
   python run.py scenarios/s2_link_failure.json --debug       also echo your log() calls to the screen
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine import check, log as logmod  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--out", default="trace.txt")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--dv-infinity", default=None, help="none, or a number such as 16")
    a = ap.parse_args()
    cap = "keep" if a.dv_infinity is None else (None if a.dv_infinity.lower() == "none" else int(a.dv_infinity))
    logmod.configure(echo=a.debug)
    lines = check.produce(a.scenario, ROOT, ROOT, verbose=a.verbose, infinity=cap)
    with open(a.out, "w") as f:
        f.write("\n".join(lines) + "\n")
    with open("debug.log", "w") as f:
        f.write("\n".join(logmod.lines()) + ("\n" if logmod.lines() else ""))
    print("wrote %s (%d lines)" % (a.out, len(lines)))


if __name__ == "__main__":
    main()

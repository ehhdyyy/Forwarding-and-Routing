#!/usr/bin/env python3
"""python ping.py scenarios/s4_net.json A 10.0.6.1 --at 30
Sends one echo request from router A at tick 30 and reports when the reply arrives.
   --to M repeats it for every tick from --at through M, one result line per tick."""
import argparse
import copy
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine import check  # noqa: E402
from engine.sim import load_scenario  # noqa: E402
from engine.tools import run_tools  # noqa: E402

TOOL = "ping"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--at", type=int, default=30)
    ap.add_argument("--to", type=int, default=None, help="last tick of a sweep that starts at --at")
    a = ap.parse_args()
    scn, topo = load_scenario(a.scenario, ROOT)
    rmod, dmod = check.load_code(ROOT)
    last = a.to if a.to is not None else a.at
    for at in range(a.at, last + 1):
        lines, _ = run_tools(copy.deepcopy(scn), topo, rmod, dmod, [{"tool": TOOL, "src": a.src, "dst": a.dst, "at": at}])
        print("\n".join(lines) if a.to is None else "at %3d:%s" % (at, lines[1]))


if __name__ == "__main__":
    main()

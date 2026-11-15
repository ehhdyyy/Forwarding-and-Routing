#!/usr/bin/env python3
"""python traceroute.py scenarios/s4_net.json A 10.0.6.1 --at 30
Sends probes with TTL 1, 2, 3 ... from router A at tick 30 and lists the router that answered each one."""
import argparse
import copy
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine import check  # noqa: E402
from engine.sim import load_scenario  # noqa: E402
from engine.tools import run_tools  # noqa: E402

TOOL = "traceroute"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--at", type=int, default=30)
    a = ap.parse_args()
    scn, topo = load_scenario(a.scenario, ROOT)
    rmod, dmod = check.load_code(ROOT)
    lines, _ = run_tools(copy.deepcopy(scn), topo, rmod, dmod, [{"tool": TOOL, "src": a.src, "dst": a.dst, "at": a.at}])
    print("\n".join(lines))


if __name__ == "__main__":
    main()

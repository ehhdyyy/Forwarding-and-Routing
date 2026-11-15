"""Shared by run.py, verify.py and the grader (GIVEN: do not edit)."""
import importlib.util
import os
import re
import sys

from .sim import Sim, load_scenario
from .tools import run_tools


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_code(code_dir):
    return (load_module("student_router", os.path.join(code_dir, "router.py")),
            load_module("student_dv", os.path.join(code_dir, "dv.py")))


def produce(scn_path, root, code_dir, verbose=False, infinity="keep"):
    """Run one scenario with the code in code_dir; return the output lines."""
    scn, topo = load_scenario(scn_path, root)
    rmod, dmod = load_code(code_dir)
    if scn.get("check") == "tool":
        return run_tools(scn, topo, rmod, dmod, scn["tool_runs"], infinity=infinity)[0]
    return Sim(scn, topo, rmod, dmod, verbose=verbose, infinity=infinity).run()


def comparable(lines, scn):
    """Drop '#' lines, apply the scenario's ignore and compare_until settings."""
    keep = [l for l in lines if not l.startswith("#")]
    if "ttl" in scn.get("ignore", []):
        keep = [re.sub(r" ttl=\d+", "", l) for l in keep]
    until = scn.get("compare_until")
    if until is not None and scn.get("check") != "tool":
        keep = [l for l in keep if int(l[:4]) < until]
    return keep


def first_difference(expected, actual):
    """(line number, expected line, actual line) of the first mismatch, or None."""
    for i in range(max(len(expected), len(actual))):
        e = expected[i] if i < len(expected) else "(no more lines)"
        a = actual[i] if i < len(actual) else "(no more lines)"
        if e != a:
            return i + 1, e, a
    return None

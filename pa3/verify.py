#!/usr/bin/env python3
"""python verify.py                        check every public scenario against its golden trace
   python verify.py step1 step2           check only those steps (step0 to step4)
   python verify.py s1_longest_prefix     check one scenario

Grading runs the same checks on the public scenarios and on hidden scenarios with other networks."""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine import check  # noqa: E402
from engine.sim import load_json  # noqa: E402

TIMEOUT = 60
ANSWER_KEYS = {
    0: ["delivery_tick", "links_crossed", "router_C_out_interface", "ttl_on_arrival", "reply_tick"],
    1: ["bug_router", "bug_chosen_prefix", "bug_correct_prefix"],
    2: ["first_tick_metric_16_or_more"],
    3: ["uncapped_highest_metric", "capped_last_change_tick"],
    4: ["ping_rtt_before_failure", "ping_rtt_after_reroute", "first_ping_lost_at", "slowest_ping_rtt",
        "traceroute_hop3_after_failure"],
}


def run_in_child(name):
    """Run one scenario in a child process with the same 60 second limit as grading."""
    path = os.path.join(ROOT, "scenarios", name + ".json")
    fd, out = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    code = ("import sys,json;sys.path.insert(0,%r);from engine import check;"
            "json.dump(check.produce(%r,%r,%r),open(%r,'w'))") % (ROOT, path, ROOT, ROOT, out)
    try:
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=TIMEOUT, cwd=ROOT)
        if p.returncode != 0:
            return None, "crashed:\n      " + "\n      ".join(p.stderr.strip().splitlines()[-6:])
        with open(out) as f:
            return json.load(f), None
    except subprocess.TimeoutExpired:
        return None, "timed out after %d seconds (an infinite loop?)" % TIMEOUT
    finally:
        if os.path.exists(out):
            os.remove(out)


def check_scenario(name):
    scn = load_json(os.path.join(ROOT, "scenarios", name + ".json"))
    lines, err = run_in_child(name)
    if err:
        return False, ["      " + err]
    with open(os.path.join(ROOT, "golden", name + ".txt")) as f:
        gold = f.read().splitlines()
    want, got = check.comparable(gold, scn), check.comparable(lines, scn)
    diff = check.first_difference(want, got)
    if diff is None:
        return True, []
    n, e, a = diff
    before = ["      line %d (same in both): %s" % (i + 1, want[i]) for i in range(max(0, n - 3), n - 1)]
    return False, ["      first difference at line %d" % n] + before + ["      expected: " + e, "      actual:   " + a]


def answers_status(step):
    keys = ANSWER_KEYS.get(step, [])
    if not keys:
        return False
    try:
        ans = load_json(os.path.join(ROOT, "answers.json"))
    except Exception as ex:
        print("  answers.json cannot be read (%s)" % ex)
        return True
    section = ans.get("step%d" % step, {})
    empty = [k for k in keys if not isinstance(section, dict) or section.get(k) in (None, "")]
    print("  answers.json step%d: %s" % (step, "all %d filled in" % len(keys) if not empty
                                        else "still empty: " + ", ".join(empty)))
    return bool(empty)


def parse_arguments(args, index):
    """Return (steps to run, scenario names to run, error message)."""
    names = {n: st["step"] for st in index["steps"] for n in st["scenarios"]}
    if not args:
        return [st["step"] for st in index["steps"]], None, None
    steps, scenario = [], None
    for a in args:
        digits = a[4:] if a.startswith("step") else a
        if digits.isdigit() and int(digits) in ANSWER_KEYS:
            steps.append(int(digits))
        elif a in names:
            scenario = a
        else:
            known = ", ".join(sorted(names))
            return None, None, 'unknown argument "%s". Use step0 to step4, or one scenario name: %s' % (a, known)
    if scenario and steps:
        return None, None, "give either steps or one scenario name, not both"
    return steps, scenario, None


def main():
    index = load_json(os.path.join(ROOT, "scenarios", "index.json"))
    steps, scenario, error = parse_arguments(sys.argv[1:], index)
    if error:
        print("verify.py: " + error)
        sys.exit(2)
    print("CS 158A PA3 self-check. Public scenarios only; grading also runs hidden scenarios.\n")
    everything = True
    unfilled = False
    for st in index["steps"]:
        wanted = [scenario] if scenario else st["scenarios"]
        if scenario and scenario not in st["scenarios"]:
            continue
        if not scenario and st["step"] not in steps:
            continue
        print("Step %d  %s" % (st["step"], st["title"]))
        for name in wanted:
            ok, detail = check_scenario(name)
            everything &= ok
            print("  %s  %s" % ("PASS" if ok else "FAIL", name))
            for d in detail:
                print(d)
        if not scenario:
            unfilled |= answers_status(st["step"])
        print()
    if not everything:
        print("Some public scenarios fail. Read the trace around the first difference.")
    elif unfilled:
        print("The public scenarios pass. Some answers in answers.json are still empty.")
    else:
        print("All public scenarios pass.")


if __name__ == "__main__":
    main()

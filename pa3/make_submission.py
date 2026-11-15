#!/usr/bin/env python3
"""python make_submission.py --name "Ada Lovelace"

Checks router.py, dv.py and answers.json, then builds pa3_ada_lovelace.zip with exactly those three files
(plus a small submission.json). Upload that zip to Canvas."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
import unicodedata
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

FILES = ("router.py", "dv.py", "answers.json")
SECTIONS = ("step0", "step1", "step2", "step3", "step4")


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def file_name_part(name):
    """'Ada  Lovelace' -> 'ada_lovelace'; accents and punctuation are simplified."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", plain.lower()).strip("_")


def problems_in_code(name, required):
    """Import a student file; return a list of error strings."""
    path = os.path.join(ROOT, name)
    try:
        spec = importlib.util.spec_from_file_location("check_" + name[:-3], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as ex:
        line = getattr(ex, "lineno", None)
        where = " (line %s)" % line if line else ""
        return ["%s cannot be loaded%s: %s: %s" % (name, where, type(ex).__name__, ex)]
    return ["%s has no %s" % (name, r) for r in required if not hasattr(mod, r)]


def problems_in_answers():
    """Return (errors, warnings)."""
    path = os.path.join(ROOT, "answers.json")
    try:
        ans = json.load(open(path))
    except json.JSONDecodeError as ex:
        return ["answers.json is not valid JSON: %s (line %d, column %d). Check quotes and commas." %
                (ex.msg, ex.lineno, ex.colno)], []
    except Exception as ex:
        return ["answers.json cannot be read: %s" % ex], []
    if not isinstance(ans, dict):
        return ["answers.json must hold one object with the sections step0 to step4"], []
    warnings = []
    for s in SECTIONS:
        sec = ans.get(s)
        if not isinstance(sec, dict):
            warnings.append("answers.json has no section %s" % s)
            continue
        empty = [k for k, v in sec.items() if v in (None, "")]
        if empty:
            warnings.append("%s: %d of %d answers still empty (%s)" % (s, len(empty), len(sec), ", ".join(empty)))
    return [], warnings


def edited_engine_files():
    try:
        manifest = json.load(open(os.path.join(ROOT, "engine", "manifest.json")))
    except Exception:
        return []
    return [rel for rel, digest in manifest.items()
            if not os.path.exists(os.path.join(ROOT, rel)) or md5(os.path.join(ROOT, rel)) != digest]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help='your name, for example "Ada Lovelace"')
    a = ap.parse_args()
    name = a.name
    if not name:
        if not sys.stdin.isatty():
            sys.exit('give your name with --name "First Last"')
        name = input("Your first and last name: ").strip()
    part = file_name_part(name)
    if not part:
        sys.exit("that name has no letters or digits. Try again with --name \"First Last\"")

    errors, warnings = [], []
    for f in FILES:
        if not os.path.exists(os.path.join(ROOT, f)):
            errors.append("%s is missing from this folder" % f)
    if not errors:
        errors += problems_in_code("router.py", ["lookup", "decrement_ttl", "time_exceeded"])
        errors += problems_in_code("dv.py", ["DistanceVector"])
        e, w = problems_in_answers()
        errors += e
        warnings += w
    if len(name.split()) < 2:
        warnings.append("you gave one name; the file name works best with first and last name")
    for rel in edited_engine_files():
        warnings.append("%s differs from the original. Changes to it have no effect on grading." % rel)

    for w in warnings:
        print("warning: " + w)
    if errors:
        for e in errors:
            print("ERROR: " + e)
        sys.exit("\nNo zip was made. Fix the errors above and run this again.")

    info = {"name": name, "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "files": {f: md5(os.path.join(ROOT, f)) for f in FILES}}
    out = os.path.join(ROOT, "pa3_%s.zip" % part)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            z.write(os.path.join(ROOT, f), f)
        z.writestr("submission.json", json.dumps(info, indent=1))
    print("\nBuilt %s with %s." % (os.path.basename(out), ", ".join(FILES)))
    print("Upload that file to Canvas.")


if __name__ == "__main__":
    main()

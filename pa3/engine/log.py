"""Debug logging for your code.

    from engine.log import log
    log("candidates", table)

Lines go to debug.log, and to the screen when you run  python run.py <scenario> --debug.
They never appear in the trace, so they cannot change what verify.py sees.
"""
import sys

_state = {"tick": 0, "node": "-", "lines": [], "echo": False}
LIMIT = 5000


def set_context(tick, node):
    _state["tick"] = tick
    _state["node"] = node


def log(*args):
    if len(_state["lines"]) >= LIMIT:
        return
    line = "[tick %04d %s] %s" % (_state["tick"], _state["node"], " ".join(str(a) for a in args))
    _state["lines"].append(line)
    if _state["echo"]:
        print(line, file=sys.stderr)


def lines():
    return _state["lines"]


def configure(echo=False):
    _state["echo"] = echo
    _state["lines"] = []

"""Tick-based network simulator (GIVEN: do not edit).

Inside one tick t, things happen in this order:
  1. link failures scheduled for t
  2. packets that routers originate at t (send events)
  3. when routing is 'dv' and t is a multiple of the period, every router (alphabetical order)
     advertises its vector out of every working interface
  4. everything that arrives at t, in the order it was sent
A packet or vector sent at tick t arrives at tick t+1.
"""
import json
import os
from collections import defaultdict

from . import log as logmod
from .util import in_prefix

MAX_HOPS = 100   # loop guard: a packet handled more than this many times is dropped


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_scenario(path, root):
    scn = load_json(path)
    return scn, load_json(os.path.join(root, scn["topology"]))


def router_of(iface):
    return iface.split("_")[0]


class Sim:
    def __init__(self, scn, topo, router_mod, dv_mod, verbose=False, infinity="keep"):
        self.scn = scn
        self.rmod = router_mod
        self.dmod = dv_mod
        self.verbose = verbose
        if infinity != "keep":
            dv_mod.INFINITY = infinity
        self.routers = topo["routers"]
        self.addr_owner = {info["addr"]: name for name, info in self.routers.items()}
        # interface -> (link number, interface at the other end)
        self.peer = {}
        self.cost = []
        self.up = []
        for n, link in enumerate(topo["links"]):
            self.peer[link["a"]] = (n, link["b"])
            self.peer[link["b"]] = (n, link["a"])
            self.cost.append(link["cost"])
            self.up.append(True)
        self.ifaces = defaultdict(list)
        for iface in sorted(self.peer):
            self.ifaces[router_of(iface)].append(iface)
        self.mode = scn.get("routing", "static")
        self.period = scn.get("dv_period", 4)
        self.out = []
        self.inbox = defaultdict(list)     # tick -> [(kind, router, iface, payload)]
        self.next_id = 1
        self.now = 0
        self.labels = {}                   # send-event label -> packet id
        self.delivered = []                # (tick, router, packet copy)
        self.dv = {}

    # ------------------------------------------------------------ output
    def emit(self, node, event, detail):
        self.out.append("%04d %-3s %-9s %s" % (self.now, node, event, detail))

    def note(self, text):
        if self.verbose:
            self.out.append("# " + text)

    def at(self, node):
        logmod.set_context(self.now, node)

    # ------------------------------------------------------------ tables
    def forwarding_table(self, r):
        if self.mode == "static":
            return [dict(e) for e in self.scn.get("static_tables", {}).get(r, [])]
        cap = self.dmod.INFINITY
        table = []
        routes = self.dv[r].routes()
        for prefix in sorted(routes):
            metric, out = routes[prefix]
            if out is None or (cap is not None and metric >= cap):
                continue
            table.append({"prefix": prefix, "out": out})
        return table

    def view(self, r):
        """{prefix: (metric, out)} as reported by router r; unreachable routes are marked."""
        cap = self.dmod.INFINITY
        seen = {}
        for prefix, (metric, out) in self.dv[r].routes().items():
            if out is not None and cap is not None and metric >= cap:
                out = "unreachable"
            seen[prefix] = (metric, out)
        return seen

    def report_changes(self, r, before):
        after = self.view(r)
        for prefix in sorted(set(before) | set(after)):
            old, new = before.get(prefix), after.get(prefix)
            if old == new:
                continue

            def word(entry, i):
                if entry is None:
                    return "none"
                if i == 1 and entry[1] is None:
                    return "local"
                return entry[i]
            self.emit(r, "TABLE", "prefix=%s metric=%s->%s out=%s->%s" %
                      (prefix, word(old, 0), word(new, 0), word(old, 1), word(new, 1)))

    @staticmethod
    def vec_text(vec):
        return ",".join("%s:%s" % (p, vec[p]) for p in sorted(vec)) or "(empty)"

    # ------------------------------------------------------------ packets
    def originate(self, r, pkt, label=None):
        pkt["id"] = self.next_id
        self.next_id += 1
        pkt.setdefault("ttl", 64)
        pkt["handled"] = 0
        if label:
            self.labels[label] = pkt["id"]
        tail = " orig=%s" % pkt["orig"] if pkt.get("orig") else ""
        self.emit(r, "ORIGINATE", "id=%d proto=%s src=%s dst=%s ttl=%d%s" %
                  (pkt["id"], pkt["proto"], pkt["src"], pkt["dst"], pkt["ttl"], tail))
        self.handle(r, pkt, None)

    def handle(self, r, pkt, came_in):
        if came_in is not None:
            self.emit(r, "RECEIVE", "id=%d in=%s ttl=%d" % (pkt["id"], came_in, pkt["ttl"]))
        if pkt["dst"] == self.routers[r]["addr"]:
            self.arrive(r, pkt)
            return
        pkt["handled"] += 1
        if pkt["handled"] > MAX_HOPS:
            self.emit(r, "DROP", "id=%d reason=loop_guard" % pkt["id"])
            return
        if came_in is not None:
            self.at(r)
            if not self.rmod.decrement_ttl(pkt):
                self.emit(r, "DROP", "id=%d reason=ttl_expired" % pkt["id"])
                if pkt["proto"] != "icmp_time_exceeded":
                    self.at(r)
                    reply = self.rmod.time_exceeded(self.routers[r]["addr"], dict(pkt))
                    if reply:
                        reply = dict(reply)
                        reply.setdefault("proto", "icmp_time_exceeded")
                        reply.setdefault("src", self.routers[r]["addr"])
                        reply.setdefault("ttl", 64)
                        reply.setdefault("orig", pkt["id"])
                        self.originate(r, reply)
                return
        table = self.forwarding_table(r)
        if self.verbose:
            hits = [e["prefix"] + ">" + e["out"] for e in table if in_prefix(pkt["dst"], e["prefix"])]
            self.note("LOOKUP %s id=%d dst=%s matching entries in table order: %s" %
                      (r, pkt["id"], pkt["dst"], ", ".join(hits) or "none"))
        self.at(r)
        entry = self.rmod.lookup(table, pkt["dst"])
        if entry is None:
            self.emit(r, "DROP", "id=%d reason=no_route" % pkt["id"])
            return
        out = entry["out"]
        if out not in self.ifaces[r]:
            self.emit(r, "DROP", "id=%d reason=bad_interface" % pkt["id"])
            return
        link, far = self.peer[out]
        if not self.up[link]:
            self.emit(r, "DROP", "id=%d reason=link_down" % pkt["id"])
            return
        self.emit(r, "FORWARD", "id=%d match=%s out=%s ttl=%d" % (pkt["id"], entry["prefix"], out, pkt["ttl"]))
        self.inbox[self.now + 1].append(("pkt", router_of(far), far, pkt))

    def arrive(self, r, pkt):
        self.emit(r, "DELIVER", "id=%d proto=%s from=%s" % (pkt["id"], pkt["proto"], pkt["src"]))
        self.delivered.append((self.now, r, dict(pkt)))
        if pkt["proto"] == "echo_request":
            self.originate(r, {"proto": "echo_reply", "src": self.routers[r]["addr"], "dst": pkt["src"],
                               "ttl": 64, "orig": pkt["id"]})

    # ------------------------------------------------------------ distance vector
    def start_dv(self):
        for r in sorted(self.routers):
            neighbors = {}
            for iface in self.ifaces[r]:
                link, far = self.peer[iface]
                neighbors[iface] = (router_of(far), self.cost[link])
            self.at(r)
            self.dv[r] = self.dmod.DistanceVector(r, self.routers[r]["prefix"], neighbors)
            self.report_changes(r, {})

    def advertise_all(self):
        for r in sorted(self.routers):
            for iface in self.ifaces[r]:
                link, far = self.peer[iface]
                if not self.up[link]:
                    continue
                self.at(r)
                vec = self.dv[r].vector(iface)
                self.emit(r, "ADVERTISE", "out=%s vec=%s" % (iface, self.vec_text(vec)))
                self.inbox[self.now + 1].append(("vec", router_of(far), far, dict(vec)))

    def fail(self, iface):
        link, far = self.peer[iface]
        self.up[link] = False
        ends = sorted([iface, far], key=lambda i: (router_of(i), i))
        for i in ends:
            self.emit(router_of(i), "LINK_DOWN", "iface=%s" % i)
        if self.mode == "dv":
            for i in ends:
                r = router_of(i)
                before = self.view(r)
                self.at(r)
                self.dv[r].on_link_down(i)
                self.report_changes(r, before)

    # ------------------------------------------------------------ main loop
    def run(self):
        events = self.scn.get("events", [])
        if self.mode == "dv":
            self.start_dv()
        for self.now in range(self.scn["ticks"] + 1):
            t = self.now
            for ev in events:
                if ev["tick"] == t and ev["type"] == "link_down":
                    self.fail(ev["iface"])
            for ev in events:
                if ev["tick"] == t and ev["type"] == "send":
                    r = ev["src"]
                    pkt = {"proto": ev.get("proto", "echo_request"), "src": self.routers[r]["addr"],
                           "dst": ev["dst"], "ttl": ev.get("ttl", 64)}
                    self.originate(r, pkt, ev.get("label"))
            if self.mode == "dv" and t % self.period == 0:
                self.advertise_all()
            for kind, r, iface, payload in self.inbox.pop(t, []):
                link, _ = self.peer[iface]
                if not self.up[link]:
                    if kind == "pkt":
                        self.emit(r, "DROP", "id=%d reason=link_down" % payload["id"])
                    continue
                if kind == "pkt":
                    self.handle(r, payload, iface)
                    continue
                before = self.view(r)
                self.note("VECTOR_IN %s in=%s vec=%s" % (r, iface, self.vec_text(payload)))
                self.at(r)
                self.dv[r].on_vector(iface, dict(payload))
                self.report_changes(r, before)
        if self.verbose and self.mode == "dv":
            for r in sorted(self.routers):
                for prefix, (metric, out) in sorted(self.view(r).items()):
                    self.note("FINAL %s %s metric=%s out=%s" % (r, prefix, metric, "local" if out is None else out))
        return self.out

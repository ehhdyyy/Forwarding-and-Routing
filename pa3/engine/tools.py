"""ping and traceroute, built on the simulator (GIVEN: do not edit)."""
import copy

from .sim import Sim

WAIT = 20        # ticks a probe waits for its answer
MAX_HOPS = 8     # traceroute stops after this many hops


def with_probes(scn, runs):
    """Copy of scn with the probe packets of each run added as send events."""
    scn = copy.deepcopy(scn)
    events = scn.setdefault("events", [])
    end = 0
    for n, run in enumerate(runs):
        end = max(end, run["at"] + WAIT + MAX_HOPS)
        ttls = [64] if run["tool"] == "ping" else range(1, MAX_HOPS + 1)
        for ttl in ttls:
            label = "run%d" % n if run["tool"] == "ping" else "run%d_%d" % (n, ttl)
            events.append({"tick": run["at"], "type": "send", "src": run["src"], "dst": run["dst"],
                           "proto": "echo_request", "ttl": ttl, "label": label})
    scn["ticks"] = max(scn.get("ticks", 0), end)
    return scn


def answer_for(sim, pid, src, kinds, at):
    """First delivery at src of a packet in kinds that answers packet pid within WAIT ticks."""
    for tick, router, pkt in sim.delivered:
        if router == src and pkt["proto"] in kinds and pkt.get("orig") == pid and tick - at <= WAIT:
            return tick, pkt
    return None


def report(sim, runs):
    lines = []
    for n, run in enumerate(runs):
        at, src = run["at"], run["src"]
        if run["tool"] == "ping":
            lines.append("PING %s -> %s at tick %d" % (src, run["dst"], at))
            got = answer_for(sim, sim.labels.get("run%d" % n), src, ("echo_reply",), at)
            lines.append("  reply from %s: %d ticks" % (got[1]["src"], got[0] - at) if got
                         else "  no reply within %d ticks" % WAIT)
            continue
        lines.append("TRACEROUTE %s -> %s at tick %d" % (src, run["dst"], at))
        for ttl in range(1, MAX_HOPS + 1):
            got = answer_for(sim, sim.labels.get("run%d_%d" % (n, ttl)), src,
                             ("icmp_time_exceeded", "echo_reply"), at)
            if got is None:
                lines.append("  %d  *" % ttl)
                continue
            who = sim.addr_owner.get(got[1]["src"], "?")
            lines.append("  %d  %s (%s)  %d ticks" % (ttl, got[1]["src"], who, got[0] - at))
            if got[1]["proto"] == "echo_reply":
                break
    return lines


def run_tools(scn, topo, rmod, dmod, runs, infinity="keep"):
    sim = Sim(with_probes(scn, runs), topo, rmod, dmod, infinity=infinity)
    sim.run()
    return report(sim, runs), sim

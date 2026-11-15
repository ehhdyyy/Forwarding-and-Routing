"""router.py  (CS 158A PA3, Chapter 4)

Edit the three functions below. The engine calls them for every packet a router handles.

A packet is a dict:
    id, proto ('echo_request', 'echo_reply' or 'icmp_time_exceeded'),
    src and dst (dotted-quad strings), ttl (int),
    orig (for ICMP messages and echo replies: the id of the packet that caused them)

A forwarding table is a list of dicts in table order:
    [{'prefix': '10.0.6.0/24', 'out': 'A_0'}, ...]
"""
from engine.util import in_prefix, prefix_len
from engine.log import log


def lookup(table, dst):
    """Return the entry (the dict) that forwards dst, or None when no entry matches."""
    longest_prefix = -1
    for entry in table:
        if in_prefix(dst, entry["prefix"]):
            if prefix_len(entry["prefix"]) > longest_prefix:
                longest_prefix = prefix_len(entry["prefix"])
                best_entry = entry
    if longest_prefix == -1:
        return None
    return best_entry


def decrement_ttl(pkt):
    """Lower pkt['ttl'] by one, in place.
    Return True when the packet may still be forwarded, False when it must be dropped."""
    pkt["ttl"] -= 1
    return pkt["ttl"] > 0


def time_exceeded(router_addr, pkt):
    """Called when this router drops pkt because its TTL ran out.
    Return the ICMP time exceeded packet (a dict) to send back toward the sender, or None."""
    return {
        "proto": "icmp_time_exceeded",
        "src" : router_addr,
        "dst" : pkt["src"],
        "ttl" : 64,
        "orig": pkt["id"],
    } or None



"""Small IPv4 helpers. Use these in router.py, or use Python's ipaddress module instead."""


def ip_to_int(ip):
    """'10.0.6.1' -> 167773697"""
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def prefix_len(prefix):
    """'10.0.6.0/24' -> 24"""
    return int(prefix.split("/")[1])


def in_prefix(ip, prefix):
    """True when the address ip falls inside the prefix 'a.b.c.d/len'."""
    net, length = prefix.split("/")
    length = int(length)
    mask = (0xFFFFFFFF << (32 - length)) & 0xFFFFFFFF if length else 0
    return (ip_to_int(ip) & mask) == (ip_to_int(net) & mask)

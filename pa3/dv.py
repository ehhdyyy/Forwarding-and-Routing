"""dv.py  (CS 158A PA3, Chapter 5)

One DistanceVector object runs inside each router.

    router_id   name of this router, e.g. 'B'
    prefix      the network attached to this router, e.g. '10.0.2.0/24' (distance 0)
    interfaces  {'B_0': ('A', 1), 'B_1': ('C', 1), ...}   interface -> (neighbor router, link cost)

The engine calls vector() every advertisement period, on_vector() when a neighbor's vector arrives and
on_link_down() when one of your interfaces fails. It reads routes() to build the forwarding table.
"""
from engine.log import log

INFINITY = 16   # Step 3: set this to 16. With --dv-infinity none it is None again, so check it before comparing


class DistanceVector:
    def __init__(self, router_id, prefix, interfaces):
        self.router_id = router_id
        self.prefix = prefix
        self.interfaces = dict(interfaces)
        self.table = {}      # prefix -> [metric, out_interface]; out_interface is None for the attached prefix
        # TODO (Step 2): put your own attached prefix in the table with metric 0
        self.table[prefix] = [0, None]
        self.vectors = {}   # neighbor router_id -> {prefix: metric}  (the last vector received from each neighbor)

    def vector(self, iface):
        """Return {prefix: metric} to advertise out of interface iface."""
        return {prefix : metric for prefix, (metric, out_iface) in self.table.items()}

    def on_vector(self, iface, vec):
        """A neighbor sent vec ({prefix: metric}) on interface iface. Update self.table."""
        self.vectors[iface] = dict(vec)

        table = {self.prefix: [0, None]}
        for nbr_iface in sorted(self.vectors):
            cost = self.interfaces[nbr_iface][1]
            for prefix, metric in self.vectors[nbr_iface].items():
                if prefix == self.prefix:
                    continue
                new = metric + cost
                if INFINITY is not None:
                    new = min(new, INFINITY)
                if prefix not in table or new < table[prefix][0]:
                    table[prefix] = [new, nbr_iface]
        self.table = table


    def on_link_down(self, iface):
        """Interface iface has failed. Update self.table."""
        self.on_vector(iface, {})

    def routes(self):
        """Used by the engine. Returns {prefix: (metric, out_interface)}. Leave this as it is."""
        return {p: (m, o) for p, (m, o) in self.table.items()}

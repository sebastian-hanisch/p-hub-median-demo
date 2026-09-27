"""Gemeinsame Hilfen der Tests: kleine Netze von Hand und Zufallsnetze."""

import hub_costs as cs
import hub_scenario as sc


def hand(pos, w, alpha=0.5):
    """Netz aus Positionen und einer symmetrischen Nachfragematrix (Liste von Listen) von Hand."""
    net = sc._build("hand", pos, w)
    return net, cs.Model(net, alpha)


def tiny(seed, n=8, alpha=0.5):
    net = sc.generate(n, seed)
    return net, cs.Model(net, alpha)

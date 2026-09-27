"""Verfahren: naive Hubwahl (p-Median auf der Gesamtnachfrage, ignoriert den Rabatt) + nächster Hub; Alternate-Location-Allocation (Zuordnung optimieren, Hubs fest); Swap-Lokalsuche über die Hub-Menge
mit mehreren Starts (die Suche kann sonst in einer Hub-Menge stecken bleiben, die eine andere, weit entfernte Menge übertrifft - dasselbe Muster wie in den Standort-Schwester-Demos).
"""

from dataclasses import dataclass
from itertools import combinations

EPS = 1e-9


@dataclass(frozen=True)
class Solution:
    hubs: tuple
    alloc: tuple
    cost: float
    moves: tuple = ()


def naive_hubs(model, p):
    """p-Median auf der Gesamtnachfrage je Knoten (Summe der Nachfrage zu allen anderen), ignoriert die Hub-zu-Hub-Interaktion; Gleichstand: kleinste Menge."""
    net = model.net
    n = net.n
    total_w = [sum(net.w[i]) for i in range(n)]
    best, best_H = None, None
    for H in combinations(range(n), p):
        c = sum(total_w[i] * min(net.d[i][h] for h in H) for i in range(n) if i not in H)
        if best is None or c < best - EPS:
            best, best_H = c, H
    return best_H


def ala(model, hubs, start=None):
    """Alternate-Location-Allocation: jeder Nicht-Hub-Knoten bekommt reihum den Hub, der seinen eigenen Kostenanteil minimiert, bis kein Knoten mehr wechseln will.
    Jeder akzeptierte Zug senkt die Gesamtkosten echt (Toleranz EPS); da es endlich viele Zuordnungen gibt, endet das Verfahren immer (keine Zyklen)."""
    n = model.n
    nearest = model.nearest(hubs)
    alloc = list(nearest) if start is None else list(start)
    for h in hubs:
        alloc[h] = h
    for i in range(n):
        if i not in hubs and alloc[i] not in hubs:
            alloc[i] = nearest[i]           # `start` stammt oft von einer anderen Hub-Menge: ein Zeiger auf einen inzwischen geschlossenen Hub ist ungültig (nicht nur bei sich selbst)
    changed = True
    while changed:
        changed = False
        for i in range(n):
            if i in hubs:
                continue
            cur_cost = model.node_cost(i, alloc)
            best_h, best_cost = alloc[i], cur_cost
            for h in hubs:
                if h == alloc[i]:
                    continue
                trial = alloc.copy()
                trial[i] = h
                c = model.node_cost(i, trial)
                if c < best_cost - EPS:
                    best_cost, best_h = c, h
            if best_h != alloc[i]:
                alloc[i] = best_h
                changed = True
    return tuple(alloc)


def solve_for(model, hubs, start=None):
    """Beste gefundene Zuordnung zu einer festen Hub-Menge (ALA) und ihre Gesamtkosten."""
    alloc = ala(model, hubs, start)
    return Solution(tuple(sorted(hubs)), alloc, model.total(alloc))


def greedy_hubs(model, p):
    """Hub für Hub: der nächste Hub ist der, der - zusammen mit den bisherigen und optimaler Zuordnung (ALA) - die Gesamtkosten am stärksten senkt; Gleichstand: kleinster Index."""
    hubs = []
    for _ in range(p):
        best, best_h = None, None
        for h in range(model.n):
            if h in hubs:
                continue
            c = solve_for(model, hubs + [h]).cost
            if best is None or c < best - EPS:
                best, best_h = c, h
        hubs.append(best_h)
    return tuple(sorted(hubs))


def local_search(model, p, start_hubs):
    """Swap-Lokalsuche: ein Hub gegen einen Nicht-Hub-Knoten tauschen, solange die Gesamtkosten (mit neu optimierter Zuordnung) sinken. Erste Verbesserung in fester Reihenfolge."""
    cur = solve_for(model, start_hubs)
    hubs, alloc, cost, moves = set(cur.hubs), cur.alloc, cur.cost, []
    improved = True
    while improved:
        improved = False
        for a in sorted(hubs):
            for b in range(model.n):
                if b in hubs:
                    continue
                cand = (hubs - {a}) | {b}
                sol = solve_for(model, cand, start=alloc)
                if sol.cost < cost - EPS:
                    hubs, alloc, cost = set(sol.hubs), sol.alloc, sol.cost
                    moves.append((a, b, sol.cost))
                    improved = True
                    break
            if improved:
                break
    return Solution(tuple(sorted(hubs)), alloc, cost, tuple(moves))


def joint(model, p):
    """Lokalsuche aus der naiven Hubwahl und aus einer gierigen Hubwahl; die bessere Lösung zählt. Gibt (Solution, Startname) zurück."""
    starts = [("naiv", naive_hubs(model, p)), ("greedy", greedy_hubs(model, p))]
    best, name = None, None
    for label, hubs in starts:
        sol = local_search(model, p, hubs)
        if best is None or sol.cost < best.cost - EPS:
            best, name = sol, label
    return best, name

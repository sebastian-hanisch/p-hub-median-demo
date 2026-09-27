"""Exakte Rechnung: das vollständige p-Hub-Median-Modell (Hubwahl UND Zuordnung gemeinsam) als gemischt-ganzzahliges Programm über HiGHS (`scipy.optimize.milp`).

Die Zielfunktion ist quadratisch in den Zuordnungsvariablen x_ik (Kosten eines Flusses hängen vom Hub BEIDER Endpunkte ab). Linearisierung (Skorin-Kapov, Kara & Tansel u. a.): eine Hilfsvariable
z_ijkm je Knotenpaar (i<j) und Hubpaar (k, m) mit z_ijkm <= x_ik, z_ijkm <= x_jm, z_ijkm >= x_ik + x_jm - 1. Da alle Kosten nichtnegativ sind, wählt die Minimierung z_ijkm = x_ik * x_jm von selbst
(kein Rundungsfehler, keine Näherung - eine exakte Umformung). x_kk = 1 bedeutet: Knoten k ist ein Hub (ersetzt eine eigene y-Variable).
"""

from itertools import combinations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


def solve_milp(model, p, time_limit=60):
    """Optimum des vollständigen Modells: (Kosten, Hubmenge, Zuordnung). `model.alpha` ist der Rabattfaktor."""
    net, alpha = model.net, model.alpha
    n = net.n
    nx = n * n                                   # x_ik = i * n + k
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if net.w[i][j]]
    npair = len(pairs)
    nz = npair * n * n                           # z_ijkm = pair_index * n*n + k*n + m

    def xi(i, k):
        return i * n + k

    def zi(p_idx, k, m):
        return nx + p_idx * n * n + k * n + m

    cost = np.zeros(nx + nz)
    for p_idx, (i, j) in enumerate(pairs):
        w = net.w[i][j]
        for k in range(n):
            for m in range(n):
                cost[zi(p_idx, k, m)] = w * (net.d[i][k] + alpha * net.d[k][m] + net.d[m][j])

    rows, cols, vals, lo, hi = [], [], [], [], []
    r = 0
    # (1) jeder Knoten genau einem Hub zugeordnet
    for i in range(n):
        for k in range(n):
            rows.append(r); cols.append(xi(i, k)); vals.append(1.0)
        lo.append(1.0); hi.append(1.0); r += 1
    # (2) genau p Hubs
    for k in range(n):
        rows.append(r); cols.append(xi(k, k)); vals.append(1.0)
    lo.append(float(p)); hi.append(float(p)); r += 1
    # (3) ein Knoten darf nur einem OFFENEN Hub zugeordnet werden: x_ik <= x_kk
    for i in range(n):
        for k in range(n):
            if i == k:
                continue
            rows += [r, r]; cols += [xi(i, k), xi(k, k)]; vals += [1.0, -1.0]
            lo.append(-np.inf); hi.append(0.0); r += 1
    # (4)-(6) Linearisierung je Paar und Hubpaar
    for p_idx in range(npair):
        for k in range(n):
            for m in range(n):
                z = zi(p_idx, k, m)
                i, j = pairs[p_idx]
                rows += [r, r]; cols += [z, xi(i, k)]; vals += [1.0, -1.0]
                lo.append(-np.inf); hi.append(0.0); r += 1                          # z <= x_ik
                rows += [r, r]; cols += [z, xi(j, m)]; vals += [1.0, -1.0]
                lo.append(-np.inf); hi.append(0.0); r += 1                          # z <= x_jm
                rows += [r, r, r]; cols += [xi(i, k), xi(j, m), z]; vals += [1.0, 1.0, -1.0]
                lo.append(-np.inf); hi.append(1.0); r += 1                          # x_ik + x_jm - z <= 1

    a = coo_matrix((vals, (rows, cols)), shape=(r, nx + nz)).tocsr()
    integrality = np.concatenate([np.ones(nx), np.zeros(nz)])
    bounds = Bounds(np.zeros(nx + nz), np.ones(nx + nz))
    res = milp(cost, constraints=LinearConstraint(a, np.array(lo), np.array(hi)), integrality=integrality, bounds=bounds,
               options={"time_limit": time_limit, "mip_rel_gap": 0.0})
    if res.status != 0:
        raise RuntimeError("MILP nicht optimal gelöst: " + str(res.message))
    x = res.x[:nx].reshape(n, n)
    hubs = tuple(k for k in range(n) if x[k][k] > 0.5)
    alloc = tuple(int(np.argmax(x[i])) for i in range(n))
    return float(res.fun), hubs, alloc


def brute_force(model, p):
    """Alle Hub-Mengen x alle Zuordnungen (nur für Kleinstnetze): (Optimalwert, Anzahl optimaler Lösungen)."""
    net = model.net
    n = net.n
    best, count = None, 0
    for hubs in combinations(range(n), p):
        others = [i for i in range(n) if i not in hubs]
        for combo in _product_over(hubs, len(others)):
            alloc = [None] * n
            for h in hubs:
                alloc[h] = h
            for idx, node in enumerate(others):
                alloc[node] = combo[idx]
            v = model.total(tuple(alloc))
            if best is None or v < best - 1e-6:
                best, count = v, 1
            elif abs(v - best) <= 1e-6:
                count += 1
    return best, count


def _product_over(hubs, k):
    from itertools import product
    return product(hubs, repeat=k)

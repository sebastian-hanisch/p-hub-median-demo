"""Orakel (anderer Rechenweg): Gesamtkosten per Tensor-Formel, Optimum per Aufzählung aller Hubmengen x Zuordnungen mit dieser Formel (nicht mit model.total), MILP und Heuristiken
dagegen; naive Hubwahl per Aufzählung des p-Medians; Alternate-Location-Allocation und Swap-Suche enden in lokalen Optima, die unabhängig nachgeprüft werden."""

import itertools

import numpy as np
import pytest

import hub_costs as cs
import hub_exact as ex
import hub_heuristics as h
import hub_scenario as sc


def _total(W, D, alpha, alloc):
    n = len(alloc)
    a = np.array(alloc)
    c = D[np.arange(n), a][:, None] + alpha * D[np.ix_(a, a)] + D[a, np.arange(n)][None, :]
    return float((np.triu(W, 1) * c).sum())


def _best_for_hubs(W, D, alpha, n, hubs):
    others = [i for i in range(n) if i not in hubs]
    best = np.inf
    for combo in itertools.product(hubs, repeat=len(others)):
        alloc = list(range(n))
        for node, hub in zip(others, combo):
            alloc[node] = hub
        best = min(best, _total(W, D, alpha, alloc))
    return best


@pytest.mark.parametrize("k", range(10))
def test_milp_heuristics_and_naive_choice_against_the_tensor_enumeration(k):
    rng = np.random.default_rng(100 + k)
    n, p = int(rng.integers(4, 7)), int(rng.integers(1, 4))
    alpha = float(rng.choice([0.0, 0.25, 0.5, 0.9, 1.0]))
    net = sc.generate(n, int(rng.integers(1, 10 ** 9)))
    W, D = np.array(net.w, float), np.array(net.d, float)
    model = cs.Model(net, alpha)
    best = min(_best_for_hubs(W, D, alpha, n, H) for H in itertools.combinations(range(n), p))
    value, _hubs, alloc = ex.solve_milp(model, p)
    assert value == pytest.approx(best, rel=1e-6) and _total(W, D, alpha, alloc) == pytest.approx(best, rel=1e-6)
    joint, _ = h.joint(model, p)
    assert joint.cost >= best - 1e-6 and joint.cost == pytest.approx(_total(W, D, alpha, joint.alloc))
    tw = W.sum(axis=1)
    naive = min(itertools.combinations(range(n), p), key=lambda H: (sum(tw[i] * D[i, list(H)].min() for i in range(n) if i not in H), H))
    assert h.naive_hubs(model, p) == naive


@pytest.mark.parametrize("k", range(6))
def test_allocation_and_swap_search_end_in_locally_optimal_solutions(k):
    rng = np.random.default_rng(300 + k)
    n, p = int(rng.integers(6, 9)), int(rng.integers(2, 4))
    alpha = float(rng.choice([0.25, 0.5, 1.0]))
    net = sc.generate(n, int(rng.integers(1, 10 ** 9)))
    W, D = np.array(net.w, float), np.array(net.d, float)
    model = cs.Model(net, alpha)
    sol = h.solve_for(model, h.naive_hubs(model, p))
    cur = _total(W, D, alpha, list(sol.alloc))
    for i in range(n):
        if i in sol.hubs:
            continue
        for hub in sol.hubs:
            trial = list(sol.alloc)
            trial[i] = hub
            assert _total(W, D, alpha, trial) >= cur - 1e-6
    ls = h.local_search(model, p, sol.hubs)
    assert ls.cost <= sol.cost + 1e-9
    for a in ls.hubs:
        for b in range(n):
            if b not in ls.hubs:
                assert h.solve_for(model, tuple(sorted((set(ls.hubs) - {a}) | {b})), start=ls.alloc).cost >= ls.cost - 1e-6

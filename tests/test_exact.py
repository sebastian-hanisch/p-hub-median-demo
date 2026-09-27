"""Exakte Rechnung: die MILP-Linearisierung gegen Brute-Force auf Kleinstnetzen, und nie schlechter als die Heuristiken."""

import pytest

import hub_exact as ex
import hub_heuristics as h
from helpers import tiny


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("p", [1, 2, 3])
@pytest.mark.parametrize("alpha", [0.2, 0.5, 0.8])
def test_milp_equals_brute_force(seed, p, alpha):
    net, model = tiny(seed, n=6, alpha=alpha)
    value, hubs, alloc = ex.solve_milp(model, p)
    best, _count = ex.brute_force(model, p)
    assert value == pytest.approx(best, abs=1e-4)
    assert model.total(alloc) == pytest.approx(value, abs=1e-4)
    assert set(alloc[i] for i in range(net.n)) <= set(hubs) and len(hubs) == p


@pytest.mark.parametrize("seed", range(4))
def test_milp_is_never_worse_than_the_heuristics(seed):
    net, model = tiny(seed, n=7, alpha=0.6)
    opt, _hubs, _alloc = ex.solve_milp(model, 2)
    naive_hubs = h.naive_hubs(model, 2)
    naive_cost = model.total(model.nearest(naive_hubs))
    joint, _name = h.joint(model, 2)
    assert opt <= joint.cost + 1e-4 <= naive_cost + 1e-4


def test_milp_with_one_hub_matches_the_naive_p_median():
    net, model = tiny(2, n=7, alpha=0.9)
    opt, hubs, _alloc = ex.solve_milp(model, 1)
    assert set(hubs) == set(h.naive_hubs(model, 1))

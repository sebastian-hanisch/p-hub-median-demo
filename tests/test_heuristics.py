"""Verfahren: Alternate-Location-Allocation verschlechtert nie, Lokalsuche und gemeinsame Optimierung sind nie schlechter als naiv; Regression für den Stale-Zuordnung-Fehler (ein Knoten, der Hub war und
es nicht mehr ist, darf nicht auf sich selbst zeigen bleiben - das täuschte Kosten von 0 vor)."""

import pytest

import hub_heuristics as h
from helpers import hand, tiny


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("p", [1, 2, 3])
def test_ala_never_raises_the_cost_and_every_node_points_to_an_open_hub(seed, p):
    net, model = tiny(seed, n=9)
    hubs = h.naive_hubs(model, p)
    start_cost = model.total(model.nearest(hubs))
    alloc = h.ala(model, hubs)
    assert model.total(alloc) <= start_cost + 1e-6
    assert all(alloc[i] in hubs for i in range(net.n)) and all(alloc[hh] == hh for hh in hubs)


def test_ala_repairs_a_stale_allocation_pointing_to_a_hub_that_is_no_longer_open():
    """Regression: ein `start`, der einen Knoten noch dem alten (jetzt geschlossenen) Hub zuordnet, darf nicht als 'Kollektionskosten 0' überleben."""
    net, model = tiny(3, n=9)
    old_hubs = (0, 1)
    old_alloc = h.ala(model, old_hubs)
    new_hubs = (2, 3)
    sol = h.solve_for(model, new_hubs, start=old_alloc)
    assert all(sol.alloc[i] in new_hubs for i in range(net.n))
    assert sol.cost == pytest.approx(model.total(h.ala(model, new_hubs)))          # dasselbe Ergebnis wie ein frischer Start


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("p", [1, 2, 3])
def test_local_search_and_joint_are_never_worse_than_naive(seed, p):
    net, model = tiny(seed, n=9)
    naive_hubs = h.naive_hubs(model, p)
    naive_cost = model.total(model.nearest(naive_hubs))
    ls = h.local_search(model, p, naive_hubs)
    joint, name = h.joint(model, p)
    assert ls.cost <= naive_cost + 1e-6 and joint.cost <= ls.cost + 1e-6
    assert name in ("naiv", "greedy") and set(joint.alloc[i] for i in range(net.n)) <= set(joint.hubs)


def test_moves_of_the_local_search_are_strictly_and_monotonically_improving():
    net, model = tiny(1, n=10)
    ls = h.local_search(model, 2, h.naive_hubs(model, 2))
    costs = [c for _a, _b, c in ls.moves]
    assert costs == sorted(costs, reverse=True) and (not costs or costs[-1] == pytest.approx(ls.cost))


def test_p_equals_one_makes_naive_hub_choice_exact_for_the_underlying_objective():
    """Bei p = 1 gibt es keine Hub-zu-Hub-Strecke: die naive p-Median-Wahl optimiert genau dasselbe Ziel wie die echten Kosten."""
    for seed in range(6):
        net, model = tiny(seed, n=9, alpha=0.9)
        naive_hubs = h.naive_hubs(model, 1)
        joint, _ = h.joint(model, 1)
        assert set(naive_hubs) == set(joint.hubs)


def test_every_node_a_hub_has_no_collection_or_distribution_leg_left():
    """Ist jeder Knoten sein eigener Hub, bleibt von jedem Fluss nur die (rabattierte) direkte Strecke übrig: keine Sammlung, keine Verteilung."""
    net, model = tiny(1, n=8)
    sol = h.solve_for(model, tuple(range(8)))
    expected = model.alpha * sum(net.w[i][j] * net.d[i][j] for i in range(8) for j in range(i + 1, 8))
    assert sol.cost == pytest.approx(expected)
    assert sol.alloc == tuple(range(8))


def test_greedy_hubs_builds_up_to_the_requested_size():
    net, model = tiny(2, n=9)
    hubs = h.greedy_hubs(model, 3)
    assert len(hubs) == 3 and len(set(hubs)) == 3

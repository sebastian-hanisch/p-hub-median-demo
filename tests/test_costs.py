"""Kostenmodell: Formel von Hand nachgerechnet, der Fall k = m (gleicher Hub) braucht keinen Sonderfall, node_cost ist konsistent mit total, nearest wählt den nächsten Hub."""

import pytest

from helpers import hand


def test_pair_cost_formula_by_hand():
    """Knoten 0 bei (0,0), Hub A bei (10,0), Hub B bei (10,10): Abstand 0->A = 100 (Zehntel), A->B = 100, B->3 (bei (0,10)) = 100. Nachfrage 0<->3 ist 4, Rabatt 0,5."""
    pos = [(0, 0), (10, 0), (10, 10), (0, 10)]
    w = [[0, 0, 0, 4], [0, 0, 0, 0], [0, 0, 0, 0], [4, 0, 0, 0]]
    net, model = hand(pos, w, alpha=0.5)
    assert model.pair_cost(0, 3, 1, 2) == pytest.approx(4 * (100 + 0.5 * 100 + 100))


def test_same_hub_needs_no_special_case_because_the_hub_hub_distance_is_zero():
    pos = [(0, 0), (10, 0), (5, 5)]
    w = [[0, 0, 3], [0, 0, 0], [3, 0, 0]]
    net, model = hand(pos, w, alpha=0.7)
    assert model.pair_cost(0, 2, 1, 1) == pytest.approx(3 * (net.d[0][1] + net.d[2][1]))          # kein Hub-zu-Hub-Anteil, da k = m = 1


def test_alpha_zero_removes_the_hub_hub_term_and_alpha_one_keeps_it_in_full():
    pos = [(0, 0), (30, 0), (30, 30), (0, 30)]
    w = [[0, 0, 5, 0], [0, 0, 0, 0], [5, 0, 0, 0], [0, 0, 0, 0]]
    net, m0 = hand(pos, w, alpha=0.0)
    _net, m1 = hand(pos, w, alpha=1.0)
    assert m0.pair_cost(0, 2, 0, 2) == pytest.approx(5 * (net.d[0][0] + net.d[2][2])) == 0.0
    assert m1.pair_cost(0, 2, 0, 2) == pytest.approx(5 * (net.d[0][0] + net.d[0][2] + net.d[2][2])) == pytest.approx(5 * net.d[0][2])


def test_total_sums_each_unordered_pair_once():
    pos = [(0, 0), (10, 0), (10, 10), (0, 10)]
    w = [[0, 2, 0, 0], [2, 0, 3, 0], [0, 3, 0, 0], [0, 0, 0, 0]]
    net, model = hand(pos, w, alpha=0.4)
    alloc = (0, 0, 1, 1)
    expected = model.pair_cost(0, 1, 0, 0) + model.pair_cost(1, 2, 0, 1)
    assert model.total(alloc) == pytest.approx(expected)


def test_node_cost_delta_matches_the_change_in_total():
    pos = [(0, 0), (20, 0), (20, 20), (0, 20), (10, 10)]
    w = [[0, 1, 2, 0, 3], [1, 0, 0, 4, 0], [2, 0, 0, 1, 0], [0, 4, 1, 0, 2], [3, 0, 0, 2, 0]]
    net, model = hand(pos, w, alpha=0.6)
    alloc = [0, 0, 1, 1, 0]
    before = model.total(alloc)
    trial = alloc.copy()
    trial[4] = 1
    after = model.total(trial)
    assert (model.node_cost(4, trial) - model.node_cost(4, alloc)) == pytest.approx(after - before)


def test_nearest_picks_the_closest_hub_with_the_smallest_index_on_ties():
    pos = [(0, 0), (20, 0), (10, 0), (10, 1)]
    w = [[0] * 4 for _ in range(4)]
    net, model = hand(pos, w)
    assert model.nearest((0, 1)) == [0, 1, 0, 0]                 # Knoten 2 liegt genau in der Mitte: kleinster Index gewinnt

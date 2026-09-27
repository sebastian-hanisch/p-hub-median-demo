"""Szenario: Zufallsnetze - ganzzahlig, deterministisch, symmetrische Nachfrage, in den erwarteten Grenzen."""

import pytest

import hub_scenario as sc


def test_distance_is_integer_euclid_in_tenths():
    assert sc.distance((0, 0), (3, 4)) == 50 and sc.distance((5, 5), (5, 5)) == 0 and sc.distance((0, 0), (1, 1)) == 14


def test_generate_is_deterministic_symmetric_and_within_bounds():
    a = sc.generate(10, 1)
    assert a == sc.generate(10, 1) and a != sc.generate(10, 2)
    assert a.n == 10 and all(0 <= x < sc.MAP_W and 0 <= y < sc.MAP_W for x, y in a.pos)
    assert all(a.w[i][j] == a.w[j][i] for i in range(10) for j in range(10)) and all(a.w[i][i] == 0 for i in range(10))
    assert all(sc.W_MIN <= a.w[i][j] <= sc.W_MAX for i in range(10) for j in range(10) if i != j)
    assert all(isinstance(v, int) for row in a.d for v in row) and all(a.d[i][i] == 0 for i in range(10))
    assert all(a.d[i][j] == a.d[j][i] for i in range(10) for j in range(10))

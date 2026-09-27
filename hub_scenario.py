"""Szenario: p-Hub-Median (Single Allocation). n Knoten, paarweise Nachfrage zwischen jedem Knotenpaar; p Knoten werden zu Hubs, jeder Knoten wird genau einem Hub zugeordnet.
Der Fluss zwischen zwei Knoten läuft über ihre Hubs; die Hub-zu-Hub-Strecke bekommt einen Rabatt (Skaleneffekt gebündelter Fernverkehrsströme).

Alles ist ganzzahlig und läuft über einen eigenen Zufallsgenerator (SplitMix64 auf Python-Ints, Kopie aus `ufl_scenario.py`) statt über `numpy.random`: numpy garantiert keine über Versionen stabilen
Zufallsströme, die CI installiert aber wöchentlich die neueste Version. Abstände sind ganzzahlig (Zehntel-Einheiten), Nachfragen ganzzahlig - Voreinstellungen, Seeds und jede im Text genannte Zahl
sind auf Windows und Linux dieselben.
"""

from dataclasses import dataclass
from math import isqrt

_MASK = (1 << 64) - 1
MAP_W = 100
W_MIN, W_MAX = 1, 9      # Nachfrage je Knotenpaar


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def below(self, n):
        """Ganzzahl in 0..n-1 (die Modulo-Verzerrung bei n <= 101 liegt um 1e-17)."""
        return self.next() % n


def distance(a, b):
    """Euklidische Entfernung in Zehntel-Einheiten, ganzzahlig (abgerundet)."""
    return isqrt(100 * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


@dataclass(frozen=True)
class Net:
    kind: str
    names: tuple
    pos: tuple           # ((x, y), ...)
    w: tuple             # w[i][j]: Nachfrage zwischen i und j (symmetrisch, w[i][i] = 0)
    d: tuple             # d[i][j] in Zehntel-Einheiten

    @property
    def n(self):
        return len(self.pos)


def _names(n):
    return tuple(f"Knoten {k + 1}" for k in range(n))


def _build(kind, pos, w):
    n = len(pos)
    d = tuple(tuple(distance(pos[i], pos[j]) for j in range(n)) for i in range(n))
    return Net(kind, _names(n), tuple(pos), tuple(tuple(row) for row in w), d)


def generate(n, seed):
    """n Knoten gleichverteilt auf 0..99; Nachfrage 1..9 je Paar (symmetrisch)."""
    rng = SplitMix64(seed)
    pos = [(rng.below(MAP_W), rng.below(MAP_W)) for _ in range(n)]
    w = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            v = W_MIN + rng.below(W_MAX - W_MIN + 1)
            w[i][j] = w[j][i] = v
    return _build("uniform", pos, w)

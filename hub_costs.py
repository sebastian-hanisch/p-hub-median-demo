"""Kostenmodell: Sammlung (Knoten zum eigenen Hub) + Hub-zu-Hub mit Rabatt + Verteilung (Hub zum Zielknoten).

Kosten des Flusses von i nach j bei Hub-Zuordnung k = hub(i), m = hub(j): w_ij * (d_ik + alpha * d_km + d_mj). Das braucht KEINEN Sonderfall für k == m: dann ist d_km = 0 (Abstand eines Knotens zu sich selbst),
die Formel liefert von selbst d_ik + d_mj - Sammlung und Verteilung über denselben Hub, ohne Hub-zu-Hub-Anteil.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    """Kosten eines Netzes bei gegebenem Rabattfaktor `alpha` (0..1): 0 = kein Rabatt beim Hub-Transport wirkt wie directer Transport, 1 = Hub-Strecke kostenlos... nein: alpha ist der Faktor auf die
    Hub-zu-Hub-Strecke (0 = Hub-Transport kostet nichts, 1 = kein Rabatt). Kleines alpha -> starker Rabatt."""

    net: object
    alpha: float

    @property
    def n(self):
        return self.net.n

    def pair_cost(self, i, j, k, m):
        """Kosten des Flusses zwischen i und j (beide Richtungen zusammen, da w symmetrisch ist) bei den Hubs k (für i) und m (für j)."""
        net = self.net
        return net.w[i][j] * (net.d[i][k] + self.alpha * net.d[k][m] + net.d[m][j])

    def total(self, alloc):
        """Gesamtkosten einer vollständigen Zuordnung `alloc` (Hub je Knoten, `alloc[i] == i` für Hubs)."""
        net = self.net
        n = net.n
        s = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if not net.w[i][j]:
                    continue
                s += self.pair_cost(i, j, alloc[i], alloc[j])
        return s

    def node_cost(self, i, alloc):
        """Kostenanteil, der von Knoten i abhängt (alle Flüsse mit i als einem Endpunkt) - für die Alternate-Location-Allocation: wie viel ändert sich, wenn nur alloc[i] wechselt."""
        net = self.net
        s = 0.0
        for j in range(net.n):
            if j == i or not net.w[i][j]:
                continue
            s += self.pair_cost(i, j, alloc[i], alloc[j])
        return s

    def nearest(self, hubs):
        """Zuordnung jedes Knotens zum nächstgelegenen Hub (ignoriert den Rabatt und alle anderen Knoten - die naive Zuordnung)."""
        return [min(hubs, key=lambda h: (self.net.d[i][h], h)) for i in range(self.n)]

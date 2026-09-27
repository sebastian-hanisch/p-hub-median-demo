"""Jede Zahl, die README und App nennen, ist hier belegt: Standardnetz und Presets (Seeds 6, 11), Verteilung über 40 feste Netze (Seeds ab 100000), Reihe über den Rabattfaktor, Vergleich mit dem
exakten Optimum. Kosten sind Gleitkommazahlen (Vergleich mit Toleranz); gezählt werden nur Größen, die nicht davon abhängen, welche von mehreren gleich guten Lösungen gewählt wird."""

import pytest

import hub_constants as C
import hub_evaluation as ev

PCT = pytest.approx


def P(**kw):
    return ev.Params(**kw)


def _preset(name):
    return ev.Params(**C.PRESETS[name])


@pytest.fixture(scope="module")
def standard():
    return ev.analyse(P())


@pytest.fixture(scope="module")
def dist_standard():
    return ev.distribution(P())


def test_standard_net_naive_against_joint(standard):
    """Standardnetz (10 Knoten, 2 Hubs, Rabattfaktor 50 %, Seed 6): naive Hubwahl (Knoten 2, 7) kostet 131 077; gemeinsam optimiert (6, 7) kostet 125 455 - 4,48 % Mehrkosten."""
    a = standard
    assert (a["naive"].hubs, a["joint"].hubs) == ((2, 7), (6, 7))
    assert (a["naive"].cost, a["joint"].cost) == (PCT(131077.0, abs=0.5), PCT(125454.5, abs=0.5)) and a["gap"] == PCT(4.482, abs=0.005)


def test_reassignment_alone_closes_little_at_the_standard_net(standard):
    """Neuzuordnung allein (dieselben Hubs, Zuordnung optimiert): 128 569 statt 131 077, noch 2,48 % über der gemeinsamen Lösung - die Hubwahl muss sich ändern."""
    a = standard
    assert a["reassign"].hubs == a["naive"].hubs and a["reassign"].cost == PCT(128569.0, abs=0.5) and a["gap_reassign"] == PCT(2.483, abs=0.005)


def test_standard_net_alpha_series():
    """Rabattfaktor 0/10/20/30/40/50/60/70/80/90/100 %: die naive Wahl kostet immer dieselben Hubs, die Mehrkosten wachsen monoton von 0 auf 12,33 % - GEGEN die naive Erwartung wächst die Lücke mit
    WENIGER Rabatt (höherem α), nicht mit mehr."""
    rows = {r["x"]: r["gap"] for r in ev.alpha_series(P())}
    assert [rows[a] for a in (0, 20, 50, 80, 100)] == PCT([0.0, 0.0, 4.482, 8.655, 12.325], abs=0.01)
    gaps = [rows[a] for a in sorted(rows)]
    assert gaps == sorted(gaps)                                            # streng monoton wachsend mit dem Rabattfaktor


def test_distribution_over_40_nets(dist_standard):
    """40 feste Netze, sonst wie das Standardnetz: die naive Wahl ist im Mittel 3,56 % teurer (Median 2,03 %, schlechtestes Netz 14,67 %); in 11 von 40 Netzen ist sie bereits optimal. Die Neuzuordnung
    allein schließt im Mittel nur 10,6 % dieser Mehrkosten (noch 3,18 % über der gemeinsamen Lösung); den besten Endpunkt lieferte der Start aus der naiven Lösung in 38 von 40 Netzen."""
    s = dist_standard["summary"]
    assert s["count"] == 40 and (s["gap_mean"], s["gap_median"], s["gap_max"]) == (PCT(3.560, abs=0.005), PCT(2.025, abs=0.005), PCT(14.667, abs=0.01))
    assert s["exact_naive"] == 11 and s["start_naiv"] == 38
    assert s["gap_reassign_mean"] == PCT(3.182, abs=0.005) and s["reassign_closed"] == PCT(0.1063, abs=0.0005)


@pytest.mark.parametrize("alpha, mean, worst, exact_naive", [(10, 0.129, 2.31, 33), (30, 1.343, 7.9, 21), (50, 3.560, 14.667, 11), (70, 6.503, 22.13, 5), (90, 9.788, 29.92, 3), (100, 11.603, 33.63, 2)])
def test_mean_extra_cost_by_discount_factor(alpha, mean, worst, exact_naive):
    """Mehrkosten der naiven Wahl über 40 Netze, Rabattfaktor 10/30/50/70/90/100 %: Mittel 0,13/1,34/3,56/6,50/9,79/11,60 %, schlechtestes Netz 2,3/7,9/14,7/22,1/29,9/33,6 %;
    bereits optimal in 33/21/11/5/3/2 von 40 Netzen - die Lücke wächst mit dem Rabattfaktor (weniger Rabatt), nicht dagegen."""
    s = ev.distribution(P(alpha=alpha))["summary"]
    assert s["gap_mean"] == PCT(mean, abs=0.01) and s["gap_max"] == PCT(worst, abs=0.05) and s["exact_naive"] == exact_naive


@pytest.mark.parametrize("label, kw, mean, closed", [("1 Hub", dict(p=1), 0.0, None), ("3 Hubs", dict(p=3), 5.108, 0.075), ("4 Hubs", dict(p=4), 4.321, 0.15),
                                                      ("8 Knoten", dict(n=8), 3.675, 0.225), ("14 Knoten", dict(n=14), 3.42, 0.108), ("16 Knoten", dict(n=16), 3.408, 0.162)])
def test_what_else_moves_the_effect(label, kw, mean, closed):
    """Ein Regler nach dem anderen (40 Netze, sonst Standard mit Mehrkosten 3,56 %): 1 Hub 0 % (Kontrolle, siehe unten); 3/4 Hubs 5,11/4,32 %; 8/14/16 Knoten 3,68/3,42/3,41 % - die Netzgröße
    ändert die relative Mehrbelastung kaum, die Hubzahl etwas stärker."""
    s = ev.distribution(P(**kw))["summary"]
    assert s["gap_mean"] == PCT(mean, abs=0.01), label
    if closed is not None:
        assert s["reassign_closed"] == PCT(closed, abs=0.01), label


def test_no_gap_with_one_hub_or_without_any_discount():
    """Kontrolle: mit nur einem Hub gibt es keine Hub-zu-Hub-Strecke, also keinen möglichen Fehler in der Hubwahl - naiv und gemeinsam sind in JEDEM der 40 Netze gleich teuer. Bei Rabattfaktor 0 %
    (kostenloser Hub-Transport) optimiert die naive p-Median-Wahl genau dasselbe Ziel wie die echten Kosten - ebenfalls in jedem Netz gleich."""
    for kw in (dict(p=1), dict(alpha=0)):
        rows = ev.distribution(P(**kw))["rows"]
        assert all(abs(r["naive"] - r["joint"]) < 1e-6 for r in rows), kw


def test_every_node_a_hub_gives_naive_and_joint_the_same_trivial_cost():
    """Kontrolle: ist jede Kandidatenmenge (p = n) erlaubt, bleibt keine Wahl übrig - naiv und gemeinsam kosten in jedem der 40 Netze dasselbe (der reine Rabatt-Term ohne Sammlung/Verteilung)."""
    rows = ev.distribution(P(n=10, p=10))["rows"]
    assert all(abs(r["naive"] - r["joint"]) < 1e-6 for r in rows)


def test_exact_comparison_on_small_nets():
    """Kleinnetze (9 Knoten, 2 Hubs, 12 feste Seeds 1-12): die Lokalsuche trifft das exakte Optimum (Mengenlinearisierung, HiGHS) in jedem Fall (Ø Lücke unter 0,001 %); die naive Wahl liegt im Mittel
    3,47 % darüber (schlechtestes Netz 18,19 %)."""
    gj, gn = [], []
    for seed in range(1, 13):
        r = ev.exact_compare(P(n=9, p=2, seed=seed))
        gj.append(r["gap_joint"]); gn.append(r["gap_naive"])
    assert max(gj) < 1e-3 and sum(gj) / len(gj) < 1e-3
    assert sum(gn) / len(gn) == PCT(3.468, abs=0.005) and max(gn) == PCT(18.19, abs=0.05)


PRESET_ROWS = [
    ("🗺️ Standardnetz", (2, 7), 131077.0, (6, 7), 125454.5, 4.482),
    ("🚫 Kein Rabatt", (2, 7), 162801.0, (4, 9), 144937.0, 12.325),
    ("💸 Starker Rabatt", (2, 7), 112042.6, (2, 7), 112042.6, 0.0),
    ("☝️ Ein Hub", (9,), 147628.0, (9,), 147628.0, 0.0),
]


@pytest.mark.parametrize("name, naive_hubs, naive_cost, joint_hubs, joint_cost, gap", PRESET_ROWS)
def test_preset_help_numbers(name, naive_hubs, naive_cost, joint_hubs, joint_cost, gap):
    """Zahlen der Preset-Hilfetexte: Hubs und Gesamtkosten der naiven und der gemeinsamen Wahl, Mehrkosten."""
    a = ev.analyse(_preset(name))
    assert (a["naive"].hubs, a["joint"].hubs) == (naive_hubs, joint_hubs)
    assert (a["naive"].cost, a["joint"].cost) == (PCT(naive_cost, abs=0.5), PCT(joint_cost, abs=0.5)) and a["gap"] == PCT(gap, abs=0.005)


def test_preset_small_net_exact():
    """Kleinnetz (9 Knoten, 2 Hubs, Seed 11): das exakte Optimum 107 179 mit den Hubs 3 und 9 (0-indiziert 2, 8); die Lokalsuche trifft es, die naive Wahl (Hubs 3, 6) ist 18,19 % darüber."""
    r = ev.exact_compare(_preset("🧮 Kleinnetz mit exaktem Optimum"))
    assert r["opt"] == PCT(107179.0, abs=0.5) and r["opt_hubs"] == (2, 8) and abs(r["gap_joint"]) < 1e-4 and r["gap_naive"] == PCT(18.191, abs=0.005)


def test_cost_breakdown_of_the_standard_net(standard):
    """Standardnetz: naiv teilt sich in 49 676 Sammlung, 31 724 Hub-zu-Hub, 49 676 Verteilung; gemeinsam optimiert in 52 144, 21 166, 52 144 - weniger Hub-zu-Hub-Kosten, dafür mehr Sammlung/Verteilung."""
    a = standard
    bn = ev.cost_breakdown(a["model"], a["naive"])
    bj = ev.cost_breakdown(a["model"], a["joint"])
    assert (bn["collect"], bn["transfer"], bn["distribute"]) == (PCT(49676, abs=1), PCT(31724, abs=1), PCT(49676, abs=1))
    assert (bj["collect"], bj["transfer"], bj["distribute"]) == (PCT(52144, abs=1), PCT(21166, abs=1), PCT(52144, abs=1))
    assert bj["transfer"] < bn["transfer"] and bj["collect"] > bn["collect"]

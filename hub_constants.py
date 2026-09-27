"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "p-Hub-Median: wer profitiert vom Rabatt?"."""

# --- Regler ---------------------------------------------------------------------------------------------------------------------
N_MIN, N_MAX, DEFAULT_N = 8, 16, 10
P_MIN, P_MAX, DEFAULT_P = 1, 4, 2
ALPHA_MIN, ALPHA_MAX, DEFAULT_ALPHA = 0, 100, 50    # Rabattfaktor in Prozent (0 = kostenloser Hub-Transport, 100 = kein Rabatt)
DEFAULT_SEED = 6
SEED_MAX = 2_000_000_000
EXACT_MAX_N = 9          # MILP-Knopf nur bis zu dieser Knotenzahl (Laufzeit waechst schnell: 9 Knoten ~15s, 10 schon ~30-55s)

# --- feste Seed-Mengen (unabhängig vom Nutzer-Seed) ---------------------------------------------------------------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
ALPHA_GRID = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)

COLORS = {"naive": "#ff7f0e", "joint": "#2ca02c", "hub": "#08519c", "node": "#1f77b4", "hubline": "#d62728", "line": "#b0b0b0", "collect": "#1f77b4", "transfer": "#d62728", "distribute": "#2ca02c"}

# --- Presets -----------------------------------------------------------------------------------------------------------------
_BASE = dict(n=DEFAULT_N, p=DEFAULT_P, alpha=DEFAULT_ALPHA, seed=DEFAULT_SEED)
PRESETS = {
    "🗺️ Standardnetz": {**_BASE},
    "🚫 Kein Rabatt": {**_BASE, "alpha": 100},
    "💸 Starker Rabatt": {**_BASE, "alpha": 20},
    "🧮 Kleinnetz mit exaktem Optimum": {**_BASE, "n": 9, "p": 2, "seed": 11},
    "☝️ Ein Hub": {**_BASE, "p": 1},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py belegt.
PRESET_HELP = {
    "🗺️ Standardnetz": "10 Knoten, 2 Hubs, Rabatt 50 %: die naive Hubwahl (Knoten 2, 7) kostet 131 077, die gemeinsam optimierte (6, 7) nur 125 455 - 4,48 % Mehrkosten. Die reine Neuzuordnung schließt davon nur 2,48 Punkte, den Rest holt erst die andere Hubwahl.",
    "🚫 Kein Rabatt": "Rabattfaktor 100 % (kein Rabatt): dieselben Knoten, aber die naive Wahl ist jetzt 12,33 % teurer statt 4,48 % - ohne Rabatt kostet eine falsche Hubwahl mehr, nicht weniger.",
    "💸 Starker Rabatt": "Rabattfaktor 20 % (starker Rabatt): naiv und gemeinsam optimiert wählen dieselben Hubs (2, 7) - bei starkem Rabatt ist die Hub-zu-Hub-Strecke so billig, dass die Hubwahl kaum noch etwas kostet.",
    "🧮 Kleinnetz mit exaktem Optimum": "9 Knoten, 2 Hubs, Seed 11: das exakte Optimum (Knopf im Abschnitt 'Wie weit ist die Lokalsuche vom Optimum?') liegt bei 107 179 mit den Hubs 2 und 8; die Lokalsuche trifft es, die naive Wahl (2, 5) ist 18,19 % teurer.",
    "☝️ Ein Hub": "Nur 1 Hub: naive und gemeinsame Wahl sind immer identisch - ohne einen zweiten Hub gibt es keine Hub-zu-Hub-Strecke und keinen Rabatt-Effekt, der eine falsche Wahl bestrafen könnte.",
}

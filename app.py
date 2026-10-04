"""p-Hub-Median - wer profitiert vom Rabatt? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo EIN Modell - p-Hub-Median mit Single Allocation - und lässt stattdessen das Beispiel wachsen.
Letztes Stück der Standortplanungs-Linie der "Konzepte"-Reihe, Kind des Standortproblems ohne Kapazität (Wurzel): p Knoten werden zu Hubs, jeder übrige Knoten wird genau einem Hub zugeordnet, und die
Hub-zu-Hub-Strecke bekommt einen Rabatt. Siehe README für die Einordnung.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import hub_constants as C
import hub_evaluation as ev
from hub_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from hub_visualization import build_alpha_series, build_costs, build_dist, build_map

st.set_page_config(page_title="p-Hub-Median – Sebastian Hanisch", layout="wide")


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _int(x):
    return "–" if x is None else f"{int(round(x)):,}".replace(",", " ")


def _pct(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f} %".replace(".", ",")


def _nodes(hubs):
    return ", ".join(str(i + 1) for i in hubs) if hubs else "–"


@st.cache_resource(show_spinner=False, max_entries=32)
def _analysis(p):
    return ev.analyse(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _alpha_series(p):
    return ev.alpha_series(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _dist(p):
    return ev.distribution(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _exact(p):
    return ev.exact_compare(p)


st.title("🌐 p-Hub-Median – wer profitiert vom Rabatt?")
st.markdown(
    """
$p$ von $n$ Knoten werden zu **Hubs**; jeder übrige Knoten wird **genau einem** Hub zugeordnet (Single Allocation). Der Fluss zwischen zwei Knoten läuft über ihre Hubs: Sammlung zum eigenen Hub,
dann die Hub-zu-Hub-Strecke mit einem **Rabatt α** (Skaleneffekt gebündelter Fernverkehrsströme, kleines α = starker Rabatt), dann Verteilung zum Ziel. Wer die Hubs **ohne Rücksicht auf den Rabatt**
wählt (klassischer p-Median auf der Gesamtnachfrage je Knoten) zahlt drauf – und **gegen die naive Erwartung wächst die Lücke mit weniger Rabatt**, nicht mit mehr.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren vergleichen, zeigt diese Demo - letztes Stück der Standortplanungs-Linie der \"Konzepte\"-Reihe - **ein** Modell an einem wachsenden Beispiel. "
    "Verwandt: das Standortproblem ohne Kapazität (ein Hub-Knoten pro Kunde ist dort nicht vorgesehen), der Wettbewerbsstandort (Führer/Folger statt Kooperation) und die Hauptlauf-Demo (ein einzelner Hub im Netzdesign, kein Rabattfaktor)."
)

with st.expander("So funktioniert das Modell", expanded=True):
    st.markdown(
        r"""
1. **Kosten eines Flusses** zwischen $i$ und $j$ bei Hubs $k=\text{hub}(i)$, $m=\text{hub}(j)$: $w_{ij}\,(d_{ik}+\alpha\, d_{km}+d_{mj})$. Ist $k=m$ (beide am selben Hub), ist $d_{km}=0$ – die Formel braucht keinen Sonderfall.
2. **Naiv:** Hubs per gewichtetem p-Median (Summe der Nachfrage je Knoten, der Rabatt bleibt unberücksichtigt) + **nächster Hub** als Zuordnung.
3. **Zuordnung optimieren** (Alternate-Location-Allocation): bei gleichen Hubs bekommt jeder Knoten reihum den Hub, der seinen eigenen Kostenanteil minimiert, bis sich nichts mehr ändert.
4. **Gemeinsam:** Swap-Lokalsuche über die Hub-Menge (mit optimierter Zuordnung je Kandidatenmenge), zwei Starts (naiv und gierig). **Exakt** (Kleinnetz): vollständiges Modell als gemischt-ganzzahliges Programm.
        """
    )

st.caption("🎯 Schnellstart – ein Beispiel laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_nodes = st.slider("Knoten", *bounds("n_slider"), key="n_slider", help="Wie viele Knoten das Netz hat; jeder ist Kandidat für einen Hub und hat mit jedem anderen eine Nachfrage.")
    p_val = st.slider("Hubs (p)", *bounds("p_slider"), key="p_slider", help="Wie viele Knoten zu Hubs werden.")
    alpha = st.slider("Rabattfaktor α (in %)", *bounds("alpha_slider"), step=10, key="alpha_slider",
                      help="Kosten der Hub-zu-Hub-Strecke als Prozent der normalen Entfernung: 0 = kostenlos (starker Rabatt), 100 = kein Rabatt.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neues Netz generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Zufalls-Seed. Die Verteilungen über feste Netze weiter unten ändern sich dabei nicht.")

sync_query_params({"n_slider": int(n_nodes), "p_slider": int(p_val), "alpha_slider": int(alpha), "seed_input": int(seed)})

params = ev.Params(int(n_nodes), int(p_val), int(alpha), int(seed))
with st.spinner("Rechne..."):
    a = _analysis(params)
net, model, naive, reassign, joint = a["net"], a["model"], a["naive"], a["reassign"], a["joint"]

# --- Naiv gegen gemeinsam ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🌐 Naiv geplant gegen gemeinsam geplant")
st.markdown(
    f"Das Netz hat **{net.n} Knoten**, gesucht sind **{params.p}** Hubs bei Rabattfaktor **{params.alpha} %**. Die naive Hubwahl (Knoten {_nodes(naive.hubs)}) kostet mit der nächsten-Hub-Zuordnung "
    f"**{_int(naive.cost)}**; die gemeinsam optimierte Lösung (Hubs {_nodes(joint.hubs)}) kostet **{_int(joint.cost)}** – die naive Planung ist um **{_pct(a['gap'])}** teurer."
)
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**Naiv**: Hubs {_nodes(naive.hubs)}")
    st.plotly_chart(build_map(net, naive), width="stretch", key="map_naive")
with c2:
    st.markdown(f"**Gemeinsam**: Hubs {_nodes(joint.hubs)}")
    st.plotly_chart(build_map(net, joint), width="stretch", key="map_joint")
st.caption("Quadrate: Hubs; gepunktete rote Linien: Hub-zu-Hub-Strecken; graue Linien: Knoten zu ihrem Hub.")

cost_rows = [("Naiv (nächster Hub)", ev.cost_breakdown(model, naive)), ("Naiv, Zuordnung optimiert", ev.cost_breakdown(model, reassign)), ("Gemeinsam optimiert", ev.cost_breakdown(model, joint))]
st.plotly_chart(build_costs(cost_rows), width="stretch", key="cost_bars")
st.table({"Lösung": ["Naiv (nächster Hub)", "Naiv, nur die Zuordnung optimiert", "Gemeinsam optimiert (Hubs und Zuordnung)"],
          "Hubs": [_nodes(naive.hubs), _nodes(reassign.hubs), _nodes(joint.hubs)],
          "Gesamtkosten": [_int(s.cost) for s in (naive, reassign, joint)],
          "Mehrkosten gegenüber gemeinsam": [_pct(ev.gap_pct(s.cost, joint.cost), 2) for s in (naive, reassign, joint)]})
st.caption(f"Die reine Neuzuordnung (gleiche Hubs, bessere Zuordnung) schließt {_pct(100 * (1 - a['gap_reassign'] / a['gap']) if a['gap'] > 1e-9 else 0, 0)} der Mehrkosten - den Rest holt erst die andere Hubwahl. "
           f"Start der gemeinsamen Lokalsuche: '{a['start']}'.")

st.markdown("---")

# --- Selbst probieren ---------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🌐 Selbst probieren: welche Knoten werden Hubs?")
if st.session_state.get("hub_pick_owner") != params:
    st.session_state["pick_multi"] = list(naive.hubs)
    st.session_state["hub_pick_owner"] = params
chosen = st.multiselect(f"Ihre {params.p} Hub{'s' if params.p > 1 else ''}", list(range(net.n)), key="pick_multi", format_func=lambda i: net.names[i], max_selections=params.p,
                        help="Jeder übrige Knoten wird bestmöglich (Alternate-Location-Allocation) einem der gewählten Hubs zugeordnet.")
cl, cr = st.columns([3, 2])
if len(chosen) == params.p:
    trial = ev.try_hubs(model, tuple(sorted(chosen)))
    with cl:
        st.plotly_chart(build_map(net, trial, height=420), width="stretch", key="pick_map")
    with cr:
        st.metric("Gesamtkosten", _int(trial.cost), delta=f"{_f(ev.gap_pct(trial.cost, joint.cost), 2)} % gegenüber gemeinsam" if trial.cost > joint.cost + 1e-6 else "so gut wie die Lokalsuche",
                  delta_color="inverse" if trial.cost > joint.cost + 1e-6 else "off")
        if trial.cost < joint.cost - 1e-6:
            st.success("🎉 Besser als die Lokalsuche – die Heuristik war hier nicht optimal.")
else:
    with cl:
        st.info(f"Wählen Sie genau {params.p} Knoten ({len(chosen)} von {params.p} gewählt).")

st.markdown("---")

# --- Wovon hängt es ab? ---------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wovon hängt es ab? Der Rabattfaktor")
st.caption("Für das eingestellte Netz: Gesamtkosten und Mehrkosten der naiven Lösung über den Rabattfaktor (die naive Hubwahl hängt vom Rabatt nicht ab).")
if st.button("Reihe über den Rabattfaktor durchrechnen", key="alpha_start"):
    st.session_state["alpha_on"] = True
if st.session_state.get("alpha_on"):
    with st.spinner("Rechne 11 Rabattfaktoren..."):
        rows = _alpha_series(params)
    st.plotly_chart(build_alpha_series(rows), width="stretch", key="alpha_chart")
    st.caption("Bei kleinem α (starkem Rabatt) ist die Hub-zu-Hub-Strecke ohnehin billig, ein falscher Hub kostet wenig; bei α nahe 100 % (kein Rabatt) wird derselbe Fehler teuer - gegen die naive Erwartung wächst die Lücke also mit WENIGER Rabatt.")

st.subheader("🔬 Gilt das in jedem Netz?")
st.caption("40 feste Netze mit den eingestellten Reglern (nur die Karte ist eine andere): Mehrkosten der naiven Lösung gegenüber der gemeinsam optimierten.")
if st.button("40 Netze durchrechnen (dauert einige Sekunden)", key="dist_start"):
    st.session_state["dist_on"] = True
if st.session_state.get("dist_on"):
    with st.spinner("Rechne 40 Netze..."):
        dist = _dist(params)
    s = dist["summary"]
    st.plotly_chart(build_dist([r["gap"] for r in dist["rows"]]), width="stretch", key="dist_chart")
    st.table({"Größe": ["Mehrkosten der naiven Lösung, Mittel", "Median", "schlechtestes Netz", "naiv bereits optimal in", "Neuzuordnung allein (Mittel)"],
              "Wert": [_pct(s["gap_mean"], 2), _pct(s["gap_median"], 2), _pct(s["gap_max"], 1), f"{s['exact_naive']} von {s['count']}", _pct(s["gap_reassign_mean"], 2)]})
    if s["reassign_closed"] is not None:
        st.caption(f"Die bloße Neuzuordnung der Kunden schließt im Mittel nur {_pct(100 * s['reassign_closed'], 0)} der Mehrkosten - den Rest holt erst die andere Hubwahl. "
                   f"Der Start aus der naiven Lösung lieferte in {s['start_naiv']} von {s['count']} Netzen den besten Endpunkt.")

st.subheader("🔬 Wie weit ist die Lokalsuche vom Optimum?")
allowed = ev.exact_allowed(params)
st.caption(f"Für kleine Netze (höchstens {C.EXACT_MAX_N} Knoten) rechnet ein gemischt-ganzzahliges Programm (Linearisierung der Hub-zu-Hub-Kopplung) das exakte Optimum nach (dauert einige Sekunden bis knapp eine halbe Minute).")
if st.button("Exakt nachrechnen", key="exact_start", disabled=not allowed, help=None if allowed else f"Nur bis {C.EXACT_MAX_N} Knoten (dieses Netz: {net.n})."):
    st.session_state["exact_on"] = True
if st.session_state.get("exact_on") and allowed:
    with st.spinner("Rechne exakt (bis zu einer halben Minute)..."):
        ex_res = _exact(params)
    st.table({"Lösung": ["Optimum (exakt)", "Gemeinsam optimiert (Lokalsuche)", "Naiv (nächster Hub)"],
              "Hubs": [_nodes(ex_res["opt_hubs"]), _nodes(joint.hubs), _nodes(naive.hubs)],
              "Kosten": [_int(ex_res["opt"]), _int(ex_res["joint"]), _int(ex_res["naive"])],
              "Mehrkosten gegenüber dem Optimum": ["–", _pct(ex_res["gap_joint"], 3), _pct(ex_res["gap_naive"], 2)]})
    if ex_res["gap_joint"] > 1e-6:
        st.warning(f"⚠️ Die Lokalsuche endet hier {_pct(ex_res['gap_joint'], 2)} über dem Optimum.")
    else:
        st.success("✅ Die Lokalsuche trifft das Optimum.")

st.markdown("---")

# --- Grenzen ----------------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist - und wer ansetzt |
|---|---|
| **Ein Rabattfaktor für alle Hub-Paare** | Reale Netze haben unterschiedliche Auslastung je Verbindung; ein einheitliches α ist eine Vereinfachung. |
| **Single Allocation** | Jeder Knoten hängt an genau einem Hub; Multiple Allocation (verschiedene Hubs je Zielrichtung) ist nicht gebaut und meist noch schwerer zu lösen. |
| **Keine Kapazität** | Hubs haben unbegrenzte Durchsatzmenge; mit Kapazität greift die Lagrange-Relaxation aus dem Stück zur kapazitierten Standortplanung. |
| **Luftlinie, ganzzahlige Abstände** | Straßennetze und Fahrzeiten sind nicht gebaut. |
| **Aufzählung/MILP nur bis Kleinnetzgröße** | Die Linearisierung wächst mit der vierten Potenz der Knotenzahl; für größere Netze braucht es spezialisierte Verfahren (Branch-and-Cut, Benders). |
| **Erzeugte Netze** | Gleichverteilte Punkte, erfundene Nachfrage, keine Fremddaten. |
"""
)
st.caption("Die Standortplanungs-Linie ist damit vollständig: das Standortproblem ohne Kapazität als Wurzel, kapazitierte Standortplanung, p-Center, Standort mit Bestand, Wettbewerbsstandort und dieses Stück (Hub-Standorte).")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Knoten $V$, $|V|=n$, Nachfrage $w_{ij}$, Abstände $d_{ij}$. $x_{ik}\in\{0,1\}$ ordnet $i$ dem Hub $k$ zu ($x_{kk}=1$ heißt: $k$ ist Hub); $\sum_kx_{ik}=1$, $x_{ik}\le x_{kk}$, $\sum_kx_{kk}=p$.
$$\min\ \sum_{i<j}\sum_{k,m}w_{ij}\big(d_{ik}+\alpha d_{km}+d_{mj}\big)\,x_{ik}x_{jm}.$$

**Linearisierung** (Skorin-Kapov u. a.): $z_{ijkm}\in[0,1]$ mit $z_{ijkm}\le x_{ik}$, $z_{ijkm}\le x_{jm}$, $z_{ijkm}\ge x_{ik}+x_{jm}-1$; da alle Kosten nichtnegativ sind, wählt die Minimierung $z_{ijkm}=x_{ik}x_{jm}$ von selbst - eine exakte Umformung, kein Näherungsschritt.

**Naiv:** $\arg\min_{|H|=p}\sum_{i\notin H}\Big(\sum_jw_{ij}\Big)\min_{k\in H}d_{ik}$ (p-Median auf der Gesamtnachfrage) + nächster Hub. **Alternate-Location-Allocation:** bei fester Hub-Menge $H$ bekommt jeder Knoten reihum den Hub, der seinen eigenen Kostenanteil minimiert, bis Konvergenz (endliche, streng fallende Kostenfolge). **Gemeinsam:** Swap-Lokalsuche über $H$ (zwei Starts: naiv und gierig), je Kandidatenmenge die ALA-Zuordnung.

Implementiert in `hub_scenario.py` (Netze, Zufallsgenerator), `hub_costs.py` (Kostenmodell), `hub_heuristics.py` (naiv, ALA, Lokalsuche), `hub_exact.py` (MILP-Linearisierung, Brute-Force), `hub_evaluation.py` (Reihen, Verteilungen, Zerlegung, Exakt-Vergleich).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Standortplanung: von der Wahl zum Wettbewerb](https://sebastianhanisch.net/konzepte-standortplanung.html)."
)

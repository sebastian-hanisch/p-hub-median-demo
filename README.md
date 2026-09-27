# p-Hub-Median – wer profitiert vom Rabatt? – Streamlit-Demo

Sechstes und letztes Stück der **Standortplanungs-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind von [standortplanung-demo](https://github.com/sebastian-hanisch/standortplanung-demo) (Standortproblem ohne Kapazität):
anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Modell – **p-Hub-Median mit Single Allocation** – an einem wachsenden Beispiel. $p$ von $n$ Knoten werden zu **Hubs**; jeder übrige Knoten wird **genau einem** Hub zugeordnet. Der Fluss zwischen zwei Knoten läuft über ihre Hubs: Sammlung zum eigenen Hub, dann die Hub-zu-Hub-Strecke mit einem **Rabatt α** (Skaleneffekt gebündelter Fernverkehrsströme), dann Verteilung zum Ziel.
Wer die Hubs **ohne Rücksicht auf den Rabatt** wählt (klassischer p-Median auf der Gesamtnachfrage je Knoten), zahlt drauf – und **gegen die naive Erwartung wächst die Lücke mit weniger Rabatt**, nicht mit mehr.

**Einordnung in die Reihe (die Kanten des Graphen):** Kind von `standortplanung-demo` (dieselben Knoten als Kandidaten, aber ein Knoten ist jetzt "Zwischenstation" für andere statt eigener Zielstandort). Zur Abgrenzung: [linehaul-demo](https://github.com/sebastian-hanisch/linehaul-demo) ist Fixed-Charge-Multicommodity-Netzdesign mit **einem** Hub (Best-of-n-Suche, kein Rabattfaktor, keine Zuordnungsentscheidung je Knoten) – klar etwas anderes als der klassische p-Hub-Median mit mehreren Hubs, Single Allocation und Rabattfaktor. `wettbewerbsstandort-demo` zeigt das Gegenteil: zwei Spieler im Wettbewerb statt einer kooperativen Standortwahl.
```
standortplanung-demo (UFL, Wurzel: Fixkosten + Transport)                               [gebaut]
  ├─ kapazitierte-standortplanung-demo (Kapazität + Single-Sourcing, Lagrange)           [gebaut]
  ├─ p-center-demo (Maximum statt Summe: Farthest-first, exakt per Überdeckung)          [gebaut]
  ├─ standort-bestand-demo (Bestandskosten je Lager, Risk Pooling)                       [gebaut]
  ├─ wettbewerbsstandort-demo (Führer und Folger, (r|p)-Centroid)                        [gebaut]
  └─ p-hub-median-demo (Hub-Standorte mit Rabatt, Single Allocation)                     [dieses Stück - LETZTES]
```

## Modell

Kosten eines Flusses zwischen $i$ und $j$ bei Hub-Zuordnung $k=\text{hub}(i)$, $m=\text{hub}(j)$: $w_{ij}\,(d_{ik}+\alpha\, d_{km}+d_{mj})$ – ist $k=m$ (beide am selben Hub), ist $d_{kk}=0$ und die Formel liefert von selbst nur Sammlung + Verteilung, **ohne Sonderfall**. Verglichen werden: die **naive Hubwahl** (gewichteter p-Median auf der Gesamtnachfrage je Knoten, der Rabatt bleibt unberücksichtigt) mit **nächstem Hub** als Zuordnung; **Neuzuordnung** (gleiche Hubs, aber die Zuordnung mit Alternate-Location-Allocation optimiert); **gemeinsame Optimierung** (Swap-Lokalsuche über die Hub-Menge, zwei Starts); und – für kleine Netze – das **exakte Optimum** (gemischt-ganzzahliges Programm mit linearisierter Hub-zu-Hub-Kopplung, HiGHS).

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` belegt: Standardnetz und Beispielnetze über ihre Seeds, Verteilung über 40 feste Netze (Seeds ab 100000), Vergleich mit dem exakten Optimum auf Kleinnetzen. Standard: 10 Knoten, 2 Hubs, Rabattfaktor 50 %, Seed 6.

**Standardnetz.** Die naive Hubwahl kostet **131 077**, die gemeinsam optimierte **125 455** – die naive Planung ist um **4,48 %** teurer. Die reine Neuzuordnung (gleiche Hubs, bessere Zuordnung) schließt davon nur 2,48 Punkte (128 569) – den Rest holt erst die andere Hubwahl. Die Kostenaufteilung verschiebt sich von Hub-zu-Hub (31 724 → 21 166) zu Sammlung/Verteilung (je 49 676 → 52 144).

**Über 40 Netze:** die naive Wahl ist im Mittel **3,56 %** teurer (Median 2,03 %, schlechtestes Netz 14,67 %); in **11 von 40** Netzen ist sie bereits optimal. Die Neuzuordnung allein schließt im Mittel nur **10,6 %** dieser Mehrkosten.

**Gegen die naive Erwartung: die Lücke wächst mit WENIGER Rabatt.** Über den Rabattfaktor 10/30/50/70/90/100 % (40 Netze je Wert): Mehrkosten im Mittel **0,13 / 1,34 / 3,56 / 6,50 / 9,79 / 11,60 %**, bereits optimal in 33/21/11/5/3/2 von 40 Netzen – die Reihe wächst **streng monoton** mit dem Rabattfaktor. Bei kleinem Rabatt (α klein) ist die Hub-zu-Hub-Strecke ohnehin billig, ein falscher Hub kostet wenig; ohne Rabatt (α = 100 %) wird derselbe Fehler teuer.

**Was sonst den Effekt bewegt** (40 Netze, ein Regler geändert, Standard 3,56 %): 3 Hubs → **5,11 %**, 4 Hubs → 4,32 %; 8/14/16 Knoten → 3,68/3,42/3,41 % (die Netzgröße ändert die relative Mehrbelastung kaum, die Hubzahl etwas stärker).

**Kontrollen bestätigt:** Mit nur **einem** Hub gibt es keine Hub-zu-Hub-Strecke – naiv und gemeinsam kosten in **jedem** der 40 Netze gleich viel (die naive p-Median-Wahl ist für p = 1 exakt das richtige Ziel). Bei Rabattfaktor **0 %** optimiert die naive Wahl ebenfalls genau dasselbe Ziel wie die echten Kosten – auch hier in jedem Netz gleich.

**Lokalsuche gegen das exakte Optimum** (Kleinnetze, 9 Knoten, 2 Hubs, 12 feste Seeds): die gemeinsame Optimierung (zwei Starts: naiv und gierig) trifft das exakte Optimum in **jedem** der 12 Fälle; die naive Wahl liegt im Mittel 3,47 % darüber (schlechtestes Netz **18,19 %**, Seed 11 – siehe Preset). Die MILP-Laufzeit wächst schnell mit der Netzgröße: 9 Knoten ~15 s, 10 Knoten schon 30–55 s – deshalb ist der Exakt-Knopf auf 9 Knoten begrenzt.

## Was nicht funktioniert hat / Vorab-Hypothesen

Vor dem Bau standen mehrere Vermutungen im Plan (Modellprüfung der Erweiterung E3). Gemessen:

- **„Mehr Rabatt macht eine falsche Hubwahl teurer“ – widerlegt, es ist umgekehrt.** Die Mehrkosten der naiven Wahl wachsen streng monoton mit dem Rabattfaktor (0,13 % bei starkem Rabatt bis 11,60 % ohne Rabatt): bei starkem Rabatt kostet ein Fehler in der Hubwahl wenig, weil die Hub-zu-Hub-Strecke ohnehin billig ist.
- **„Die naive p-Median-Wahl liegt ungefähr richtig“ – nur bei starkem Rabatt.** Bei Rabattfaktor 100 % ist sie nur in 2 von 40 Netzen optimal; bei 10 % in 33 von 40.
- **„Eine bessere Zuordnung bei gleichen Hubs reicht“ – widerlegt.** Sie schließt im Mittel nur 10,6 % der Mehrkosten; die Hubwahl selbst muss sich ändern.
- **„Ein exaktes Verfahren für p-Hub-Median ist auf kleinen Netzen leicht zu haben“ – nur mit der richtigen Formulierung.** Eine reine Aufzählung (Hub-Mengen × Zuordnungen) skaliert extrem schlecht; erst die MILP-Linearisierung (Skorin-Kapov u. a.) macht den Kleinnetz-Vergleich praktikabel, und selbst die wächst schnell (9 Knoten ~15 s, 10 Knoten 30–55 s).
- **Bestätigt:** die zwei Kontrollfälle (ein Hub; kein Rabatt) zeigen exakt 0 % Lücke in jedem Netz – wie das Modell es verlangt.

## Grenzen (was die Demo nicht zeigt)

Ein Rabattfaktor für alle Hub-Paare (reale Netze haben unterschiedliche Auslastung je Verbindung), Single Allocation (kein Multiple Allocation), keine Kapazität, Luftlinie mit ganzzahligen Abständen, Aufzählung/MILP nur bis Kleinnetzgröße (die Linearisierung wächst mit der vierten Potenz der Knotenzahl), erzeugte Netze ohne Fremddaten.

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Naiv gegen gemeinsam, Selbst probieren, Reihe über den Rabattfaktor, Verteilung über 40 Netze, Exakt-Vergleich |
| `hub_scenario.py` | Netze (Zufallskarte, paarweise Nachfrage), SplitMix64-Zufallsstrom (Kopie aus den Vorgängern) |
| `hub_costs.py` | Kostenmodell: Sammlung, Hub-zu-Hub mit Rabatt, Verteilung; nächster Hub |
| `hub_heuristics.py` | naive Hubwahl (p-Median), Alternate-Location-Allocation, Swap-Lokalsuche mit zwei Starts |
| `hub_exact.py` | MILP-Linearisierung der Hub-zu-Hub-Kopplung (HiGHS), Brute-Force für Tests |
| `hub_evaluation.py`, `hub_visualization.py` | Analyse, Reihe über α, Verteilung, Kostenaufteilung, Exakt-Vergleich; Karte, Kostenbalken, Reihe |
| `hub_presets.py`, `hub_constants.py` | Presets, Permalink, Regler-Grenzen, feste Seeds |
| `tests/` | 175 Tests: Szenario, Kostenformel von Hand, ALA/Lokalsuche (keine Verschlechterung, Regression für eine gefundene Stale-Zuordnung), MILP gegen Brute-Force, Presets, Zahlen (`test_claims.py`), App |

Lokal starten: `pip install -r requirements.txt`, dann `streamlit run app.py`; Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests`.

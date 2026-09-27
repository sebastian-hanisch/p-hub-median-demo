"""Auswertungen: eine Analyse für das eingestellte Netz, Reihe über den Rabattfaktor, Verteilung über 40 feste Netze, Zerlegung Hub-Wahl gegen Zuordnung, Vergleich mit dem exakten Optimum."""

import statistics
from dataclasses import dataclass

import hub_constants as C
import hub_costs as cs
import hub_exact as ex
import hub_heuristics as h
import hub_scenario as sc


@dataclass(frozen=True)
class Params:
    n: int = C.DEFAULT_N
    p: int = C.DEFAULT_P
    alpha: int = C.DEFAULT_ALPHA        # Prozent
    seed: int = C.DEFAULT_SEED

    def model(self, net):
        return cs.Model(net, self.alpha / 100)


def build(params, seed=None):
    net = sc.generate(params.n, params.seed if seed is None else seed)
    return net, params.model(net)


def gap_pct(value, base):
    return 100 * (value - base) / base if base > 1e-9 else 0.0


def _raw(model, hubs):
    """Ganz naiv: nächster Hub, keine Verbesserung (Alternate-Location-Allocation läuft nicht)."""
    alloc = model.nearest(hubs)
    return h.Solution(tuple(sorted(hubs)), tuple(alloc), model.total(alloc))


def analyse(params):
    net, model = build(params)
    naive_hubs = h.naive_hubs(model, params.p)
    naive = _raw(model, naive_hubs)                                  # Hubs ignorieren den Rabatt, Zuordnung = nächster Hub, keine Optimierung
    reassign = h.solve_for(model, naive_hubs)                        # gleiche Hubs, aber die Zuordnung mit Alternate-Location-Allocation optimiert
    joint, start = h.joint(model, params.p)
    gap = gap_pct(naive.cost, joint.cost)
    gap_reassign = gap_pct(reassign.cost, joint.cost)
    return {"net": net, "model": model, "naive": naive, "reassign": reassign, "joint": joint, "start": start, "gap": gap, "gap_reassign": gap_reassign}


def try_hubs(model, hubs):
    """Der Nutzer wählt `hubs` selbst: beste Zuordnung (ALA) und die Kosten."""
    return h.solve_for(model, hubs)


def cost_breakdown(model, sol):
    """Kosten aufgeteilt in Sammlung, Hub-zu-Hub und Verteilung."""
    net = model.net
    collect = transfer = distribute = 0.0
    for i in range(net.n):
        for j in range(net.n):
            if i == j or not net.w[i][j]:
                continue
            k, m = sol.alloc[i], sol.alloc[j]
            w = net.w[i][j]
            collect += w * net.d[i][k]
            transfer += w * model.alpha * net.d[k][m]
            distribute += w * net.d[m][j]
    # jede ungeordnete Paarung wurde zweimal gezählt (i,j) und (j,i)
    return {"collect": collect / 2, "transfer": transfer / 2, "distribute": distribute / 2}


def alpha_series(params, grid=C.ALPHA_GRID):
    net = sc.generate(params.n, params.seed)
    naive_h = h.naive_hubs(cs.Model(net, params.alpha / 100), params.p)     # Hubwahl hängt nicht vom Rabatt ab
    rows = []
    for a in grid:
        model = cs.Model(net, a / 100)
        naive = _raw(model, naive_h)
        joint, _ = h.joint(model, params.p)
        rows.append({"x": a, "naive": naive.cost, "joint": joint.cost, "gap": gap_pct(naive.cost, joint.cost)})
    return rows


def one_net(params, seed):
    p2 = Params(params.n, params.p, params.alpha, seed)
    a = analyse(p2)
    return {"seed": seed, "naive": a["naive"].cost, "reassign": a["reassign"].cost, "joint": a["joint"].cost, "gap": a["gap"], "gap_reassign": a["gap_reassign"], "start": a["start"]}


def summarize(rows):
    gaps = [r["gap"] for r in rows]
    gaps_r = [r["gap_reassign"] for r in rows]
    mean = statistics.fmean(gaps)
    return {"count": len(rows), "gap_mean": mean, "gap_median": statistics.median(gaps), "gap_max": max(gaps), "gap_min": min(gaps),
            "gap_reassign_mean": statistics.fmean(gaps_r), "reassign_closed": 1 - statistics.fmean(gaps_r) / mean if mean > 1e-9 else None,
            "exact_naive": sum(1 for r in rows if r["gap"] <= 1e-6), "start_naiv": sum(1 for r in rows if r["start"] == "naiv")}


def distribution(params, seeds=C.SWEEP_SEEDS):
    rows = [one_net(params, s) for s in seeds]
    return {"rows": rows, "summary": summarize(rows)}


def exact_allowed(params):
    return params.n <= C.EXACT_MAX_N


def exact_compare(params):
    net, model = build(params)
    naive_hubs = h.naive_hubs(model, params.p)
    naive = _raw(model, naive_hubs)
    joint, _ = h.joint(model, params.p)
    opt, opt_hubs, opt_alloc = ex.solve_milp(model, params.p)
    return {"opt": opt, "opt_hubs": opt_hubs, "joint": joint.cost, "naive": naive.cost, "gap_joint": gap_pct(joint.cost, opt), "gap_naive": gap_pct(naive.cost, opt)}

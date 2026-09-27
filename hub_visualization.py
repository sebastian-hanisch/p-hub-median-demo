"""Plotly-Abbildungen: Karte mit Hubs, Zuordnungslinien und hervorgehobenen Hub-zu-Hub-Kanten, Kostenbalken (Sammlung/Hub-zu-Hub/Verteilung), Reihe über den Rabattfaktor, Verteilung der Mehrkosten.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen. Karten haben gleichen Maßstab (scaleanchor) mit automatischem Bereich; der Rand kommt über zwei unsichtbare Punkte."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import hub_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(net, sol, height=460):
    """Knoten (Farbe nach zugeordnetem Hub), Linien zum eigenen Hub, Hub-zu-Hub-Kanten rot hervorgehoben; Hubs als Quadrate."""
    fig = go.Figure()
    hubs = sol.hubs
    xs, ys = [], []
    for i in range(net.n):
        if i in hubs:
            continue
        h = sol.alloc[i]
        xs += [net.pos[i][0], net.pos[h][0], None]
        ys += [net.pos[i][1], net.pos[h][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLORS["line"], width=1), hoverinfo="skip", showlegend=False))
    if len(hubs) > 1:
        hx, hy = [], []
        for a in range(len(hubs)):
            for b in range(a + 1, len(hubs)):
                hx += [net.pos[hubs[a]][0], net.pos[hubs[b]][0], None]
                hy += [net.pos[hubs[a]][1], net.pos[hubs[b]][1], None]
        fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", name="Hub-zu-Hub", line=dict(color=C.COLORS["hubline"], width=2, dash="dot"), hoverinfo="skip"))
    others = [i for i in range(net.n) if i not in hubs]
    fig.add_trace(go.Scatter(x=[net.pos[i][0] for i in others], y=[net.pos[i][1] for i in others], mode="markers", name="Knoten",
                             marker=dict(color=C.COLORS["node"], size=8, opacity=0.8), text=[f"{net.names[i]} -> {net.names[sol.alloc[i]]}" for i in others], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[net.pos[i][0] for i in hubs], y=[net.pos[i][1] for i in hubs], mode="markers+text", name="Hub",
                             marker=dict(symbol="square", color=C.COLORS["hub"], size=16, line=dict(color="#111111", width=1)),
                             text=[str(i + 1) for i in hubs], textposition="top center", textfont=dict(size=10), hovertext=[net.names[i] for i in hubs], hoverinfo="text"))
    pad = 6
    fig.add_trace(go.Scatter(x=[-pad, 99 + pad], y=[-pad, 99 + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def build_costs(rows, height=220):
    """Gestapelte Balken: Sammlung, Hub-zu-Hub, Verteilung. `rows`: [(Beschriftung, {"collect","transfer","distribute"})]."""
    fig = go.Figure()
    labels = [r[0] for r in rows]
    for key, name in (("collect", "Sammlung"), ("transfer", "Hub-zu-Hub"), ("distribute", "Verteilung")):
        fig.add_trace(go.Bar(y=labels, x=[r[1][key] for r in rows], name=name, orientation="h", marker_color=C.COLORS[key],
                             text=[f"{r[1][key]:,.0f}".replace(",", " ") for r in rows], textposition="inside", hovertemplate="%{y}: %{x:,.0f}<extra>" + name + "</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Gesamtkosten")
    return _base(fig, height)


def build_alpha_series(rows, height=320):
    xs = [r["x"] for r in rows]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Gesamtkosten", "Mehrkosten der naiven Lösung"), horizontal_spacing=0.12)
    fig.add_trace(go.Scatter(x=xs, y=[r["naive"] for r in rows], mode="lines+markers", name="naiv (ignoriert den Rabatt)", line=dict(color=C.COLORS["naive"])), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=[r["joint"] for r in rows], mode="lines+markers", name="gemeinsam optimiert", line=dict(color=C.COLORS["joint"])), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=[r["gap"] for r in rows], mode="lines+markers", name="Mehrkosten in %", showlegend=False, line=dict(color=C.COLORS["hubline"])), row=1, col=2)
    fig.update_xaxes(title_text="Rabattfaktor α (%)")
    fig.update_yaxes(title_text="Kosten", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="Prozent", rangemode="tozero", row=1, col=2)
    return _base(fig, height)


def build_dist(gaps, height=280):
    fig = go.Figure(go.Histogram(x=gaps, nbinsx=20, marker_color=C.COLORS["naive"], hovertemplate="%{x:.1f} %: %{y} Netze<extra></extra>"))
    mean = sum(gaps) / len(gaps)
    fig.add_vline(x=mean, line=dict(color="#111111", dash="dash"), annotation_text=f"Mittel {mean:.1f} %".replace(".", ","), annotation_position="top right")
    fig.update_xaxes(title="Mehrkosten der naiven Lösung in %")
    fig.update_yaxes(title="Netze")
    return _base(fig, height)

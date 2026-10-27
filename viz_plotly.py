#!/usr/bin/env python3
"""Временная анимация графа истории медицины (Plotly).

Читает gephi_output_v2/nodes.csv и edges.csv. Узлы появляются/исчезают
по интервалу [Start, End], рёбра — статичный фон.
Запуск: uv run python viz_plotly.py
Выход: graph_timeline.html
"""
import csv
from pathlib import Path

import networkx as nx
import plotly.graph_objects as go

NODES_CSV = Path("gephi_output_v2/nodes.csv")
EDGES_CSV = Path("gephi_output_v2/edges.csv")
OUT = Path("graph_timeline.html")

# Ключевые годы-кадры (от древности до наших дней)
FRAMES_YEARS = [
    -3500, -3000, -2500, -2000, -1500, -1000, -800, -600, -480, -400,
    -323, -300, -200, -100, -27, 0, 100, 200, 330, 500, 622, 900,
    1000, 1200, 1300, 1400, 1543, 1600, 1700, 1760, 1800, 1837,
    1850, 1890, 1900, 1914, 1928, 1945, 1960, 1978, 1990, 2000,
    2010, 2026,
]

# Подписи показываем только для ключевых узлов, чтобы не было каши
LABELED_KINDS = {"era", "disease", "discovery", "concept", "institution", "ethic"}


def load_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    with open(NODES_CSV, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            G.add_node(
                r["ID"],
                Label=r["Label"], Kind=r["Kind"],
                Start=float(r["Start"]), End=float(r["End"]),
                Region=r["Region"], Note=r["Note"],
                Size=float(r["Size"]), Degree=float(r["Degree"]),
                Color=r["Color"],
            )
    with open(EDGES_CSV, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            G.add_edge(r["Source"], r["Target"],
                       Relation=r["Relation"], Label=r["Label"])
    return G


def main() -> None:
    G = load_graph()
    pos = nx.spring_layout(G, seed=42, iterations=60, k=0.4)

    # Статичные рёбра (контекст на фоне)
    edge_x, edge_y = [], []
    for u, v in G.edges():
        (x0, y0), (x1, y1) = pos[u], pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="#cccccc", width=0.5),
        hoverinfo="skip", showlegend=False,
    )

    def node_trace(year: int) -> go.Scatter:
        xs, ys, labels, colors, sizes, hints = [], [], [], [], [], []
        for nid, d in G.nodes(data=True):
            if d["Start"] <= year <= d["End"]:
                x, y = pos[nid]
                kind = d["Kind"]
                label = d["Label"]
                degree = d["Degree"]
                xs.append(x)
                ys.append(y)
                labels.append(label if kind in LABELED_KINDS or degree >= 8 else "")
                colors.append(d["Color"])
                sizes.append(6 + degree * 0.6)
                hints.append(f"{label}<br>{kind}: {d['Note']}")
        return go.Scatter(
            x=xs, y=ys, mode="markers+text",
            text=labels, textposition="top center", textfont=dict(size=8),
            marker=dict(color=colors, size=sizes, line=dict(width=0.5, color="#333333")),
            customdata=hints, hovertemplate="%{customdata}<extra></extra>",
            showlegend=False,
        )

    frames = [
        go.Frame(data=[node_trace(y)], traces=[1], name=str(y))
        for y in FRAMES_YEARS
    ]
    fig = go.Figure(data=[edge_trace, node_trace(FRAMES_YEARS[0])], frames=frames)

    slider = dict(
        steps=[
            dict(
                method="animate",
                args=[
                    [str(y)],
                    dict(mode="immediate", frame=dict(duration=300, redraw=True),
                         transition=dict(duration=0)),
                ],
                label=str(y),
            )
            for y in FRAMES_YEARS
        ],
        active=0,
        currentvalue=dict(prefix="Год: ", visible=True, xanchor="right"),
        pad=dict(t=20),
    )
    fig.update_layout(
        title="История медицины: сущности во времени",
        sliders=[slider],
        width=1100, height=750,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
    )
    fig.write_html(OUT)
    print(f"Сохранено: {OUT.resolve()} ({len(FRAMES_YEARS)} кадров)")


if __name__ == "__main__":
    main()

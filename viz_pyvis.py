#!/usr/bin/env python3
"""Интерактивная HTML-визуализация графа истории медицины (pyvis).

Читает gephi_output_v2/nodes.csv и edges.csv, строит интерактивный граф.
Запуск: uv run python viz_pyvis.py
Выход: graph.html
"""
import csv
from pathlib import Path

import networkx as nx
from pyvis.network import Network

NODES_CSV = Path("gephi_output_v2/nodes.csv")
EDGES_CSV = Path("gephi_output_v2/edges.csv")
OUT = Path("graph.html")


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
    net = Network(height="750px", width="100%", directed=True,
                  bgcolor="#ffffff", font_color="#222222")

    for nid, d in G.nodes(data=True):
        label = d["Label"]
        degree = d["Degree"]
        net.add_node(
            nid,
            label=label,
            title=f"{label} · {d['Kind']}",
            color=d["Color"],
            size=8 + degree * 0.6,
        )

    for u, v, d in G.edges(data=True):
        net.add_edge(u, v, title=f"{d['Relation']}: {d['Label']}", arrows="to")

    net.write_html(str(OUT))
    print(f"Сохранено: {OUT.resolve()} "
          f"(узлов: {G.number_of_nodes()}, связей: {G.number_of_edges()})")


if __name__ == "__main__":
    main()

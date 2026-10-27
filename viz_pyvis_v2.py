#!/usr/bin/env python3
"""Интерактивный граф с карточками-подсказками и ссылками на поиск (pyvis).

Отличие от viz_pyvis.py: при наведении на узел/ребро показывается карточка
с комментарием (Note / Relation) и гиперссылками на поиск топика.
Запуск: uv run python viz_pyvis_v2.py
Выход: graphV2.html
"""
import csv
import urllib.parse
from pathlib import Path

import networkx as nx
from pyvis.network import Network

NODES_CSV = Path("gephi_output_v2/nodes.csv")
EDGES_CSV = Path("gephi_output_v2/edges.csv")
OUT = Path("graphV2.html")

GOOGLE = "https://www.google.com/search?q={q}"
WIKI = "https://ru.wikipedia.org/w/index.php?search={q}"


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


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _years(s: float, e: float) -> str:
    s, e = int(s), int(e)
    return str(s) if s == e else f"{s} … {e}"


def _links(q: str) -> str:
    q = urllib.parse.quote(q)
    return (
        f"<a href='{GOOGLE.format(q=q)}' target='_blank'>🔎 поиск</a> · "
        f"<a href='{WIKI.format(q=q)}' target='_blank'>Википедия</a>"
    )


def node_card(d: dict) -> str:
    return (
        "<div style='font-family:sans-serif;max-width:280px;line-height:1.35'>"
        f"<b>{_esc(d['Label'])}</b> "
        f"<span style='color:#888'>{d['Kind']}</span><br>"
        f"<span style='color:#555'>{_years(d['Start'], d['End'])} · "
        f"{_esc(d['Region'])}</span><br>"
        f"<span>{_esc(d['Note'])}</span><br>"
        f"{_links(d['Label'])}"
        "</div>"
    )


def edge_card(u_label: str, v_label: str, d: dict) -> str:
    return (
        "<div style='font-family:sans-serif;max-width:280px;line-height:1.35'>"
        f"<b>{_esc(u_label)}</b> → <b>{_esc(v_label)}</b><br>"
        f"<span style='color:#888'>{d['Relation']}</span><br>"
        f"<span>{_esc(d['Label'])}</span><br>"
        f"{_links(v_label)}"
        "</div>"
    )


def main() -> None:
    G = load_graph()
    net = Network(height="750px", width="100%", directed=True,
                  bgcolor="#ffffff", font_color="#222222")

    for nid, d in G.nodes(data=True):
        net.add_node(
            nid,
            label=d["Label"],
            title=node_card(d),
            color=d["Color"],
            size=8 + d["Degree"] * 0.6,
        )

    for u, v, d in G.edges(data=True):
        net.add_edge(
            u, v,
            title=edge_card(G.nodes[u]["Label"], G.nodes[v]["Label"], d),
            arrows="to",
        )

    net.write_html(str(OUT))
    print(f"Сохранено: {OUT.resolve()} "
          f"(узлов: {G.number_of_nodes()}, связей: {G.number_of_edges()})")


if __name__ == "__main__":
    main()

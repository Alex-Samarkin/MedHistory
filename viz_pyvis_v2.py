#!/usr/bin/env python3
"""Интерактивный граф с карточками-подсказками и ссылками на поиск (pyvis).

Отличие от viz_pyvis.py: карточки показываются при наведении на узел или на
маркер-тег в середине ребра (подпись — тема ребра, рамка и тень).
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

# Русские подписи для типов отношений (метки маркеров-тегов на рёбрах)
REL_RU = {
    "APPLIED_BY": "применён",
    "AUTHORED": "автор",
    "BACKGROUND_TO": "предпосылка",
    "CONCERNS": "касается",
    "CONSTRAINS": "ограничивает",
    "CONTEXTUALIZES": "контекстуализирует",
    "CONTEXT_FOR": "контекст",
    "CONTRIBUTED_TO": "внёс вклад",
    "DEFINES": "определяет",
    "DERIVED_FROM": "происходит из",
    "DESCRIBES": "описывает",
    "DEVELOPED_BY": "развивали",
    "DISCOVERED": "открыл",
    "EMPIRICAL_PRECURSOR": "эмпир. предшественник",
    "ENABLED": "сделал возможным",
    "EPIDEMIC_IN": "эпидемия в",
    "ESTABLISHED_BY": "установлен",
    "ETHICAL_CHALLENGE_TO": "этич. вызов",
    "ETHICAL_CONSTRAINT_ON": "этич. ограничение",
    "EXPLAINED_BY": "объяснено",
    "EXTENDED_TO": "расширено до",
    "FOUNDATION_OF": "основа для",
    "FUNDS": "финансирует",
    "HOSTS": "место работы",
    "INFLUENCED": "повлиял",
    "INSTITUTIONALIZES": "институционализировал",
    "MENTORED": "наставник",
    "MOLECULARIZED_IN": "молекуляризовано",
    "MOTIVATED": "мотивировал",
    "ORGANIZES": "организует",
    "PRECEDED": "предшествовал",
    "REDUCED_TO": "сведено к",
    "REFUTED_BUT_PRESERVES": "опровергнуто",
    "REINTERPRETED_AS": "переосмыслено",
    "REPLACED_BY": "заменено",
    "SOURCE_FOR": "источник для",
    "SPECIFIED_BY": "конкретизировано",
    "STRUCTURAL_ANALOGUE": "структурный аналог",
    "SUCCEEDED_BY": "сменилась",
    "TARGETS": "цель",
    "TECHNIQUE_TRANSFER": "перенос техники",
    "TENSION_WITH": "напряжение с",
    "TRACED": "проследил",
    "TREATS": "лечит",
    "UNDERPINS": "обосновывает",
    "USES": "использует",
    "VACCINE_FOR": "вакцина от",
}


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
                  bgcolor="#ffffff")

    # Улучшаем наведение на рёбра: кривые линии (разделяет встречные/наложенные
    # рёбра), больший разнос узлов и более толстые рёбра, чтобы по стрелке было
    # легко попасть курсором.
    net.set_edge_smooth("dynamic")
    net.repulsion(node_distance=200, spring_length=150)
    net.options.edges.width = 2.5
    net.options.edges.hoverWidth = 3.5
    net.options.edges.selectionWidth = 3.5
    net.options.interaction.tooltipDelay = 120

    for nid, d in G.nodes(data=True):
        net.add_node(
            nid,
            label=d["Label"],
            title=node_card(d),
            color=d["Color"],
            size=8 + d["Degree"] * 0.6,
            font={"color": "#222222", "face": "sans-serif"},
        )

    # Маркеры в середине рёбер: подпись-«тег» с темой ребра, тонкой рамкой и
    # тенью; при наведении показывается карточка ребра.
    for i, (u, v, d) in enumerate(G.edges(data=True)):
        mid = f"__edge_{i}"
        u_label = G.nodes[u]["Label"]
        v_label = G.nodes[v]["Label"]
        net.add_node(
            mid,
            label=REL_RU.get(d["Relation"], d["Relation"].replace("_", " ").lower()),
            title=edge_card(u_label, v_label, d),
            shape="box",
            color={"background": "#ffffff", "border": "#999999"},
            borderWidth=1,
            font={"size": 9, "color": "#333333", "face": "sans-serif"},
            shadow={"enabled": True, "color": "rgba(0,0,0,0.25)",
                    "size": 4, "x": 1, "y": 1},
        )
        net.add_edge(u, mid, arrows="", color="#999999", width=1.2)
        net.add_edge(mid, v, arrows="to", color="#999999", width=1.2)

    net.write_html(str(OUT))
    n_markers = G.number_of_edges()
    print(f"Сохранено: {OUT.resolve()} "
          f"(узлов: {G.number_of_nodes()} + {n_markers} маркеров, "
          f"связей: {2 * n_markers})")


if __name__ == "__main__":
    main()

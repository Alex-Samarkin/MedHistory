#!/usr/bin/env python3
"""graphV3.html — переключение раскладки узлов и тем оформления (pyvis + JS).

Поверх pyvis-графа добавляется панель кнопок:
- раскладка: Силовая (barnesHut), Расталкивание (repulsion), ForceAtlas2,
  Дерево (hierarchical) и Круг (предвычисленная упаковка);
- тема: Светлая / Тёмная (меняется фон, рёбра и цвет подписей).
Запуск: uv run python viz_pyvis_v3.py
Выход: graphV3.html
"""
import json
import math
from pathlib import Path

import networkx as nx
from pyvis.network import Network

from viz_pyvis_v2 import load_graph, node_card, edge_card, REL_RU

OUT = Path("graphV3.html")


def circular_positions(G: nx.DiGraph) -> dict:
    """Круговая упаковка: реальные узлы по кругу (сгруппированы по Kind),
    маркеры — в середине своего ребра."""
    real = sorted(G.nodes(), key=lambda n: (G.nodes[n]["Kind"], str(n)))
    R = 500.0
    pos = {}
    n_real = len(real)
    for idx, nid in enumerate(real):
        ang = 2 * math.pi * idx / n_real
        pos[nid] = {"x": round(R * math.cos(ang), 2),
                    "y": round(R * math.sin(ang), 2)}
    for i, (u, v) in enumerate(G.edges()):
        mid = f"__edge_{i}"
        pos[mid] = {"x": round((pos[u]["x"] + pos[v]["x"]) / 2, 2),
                    "y": round((pos[u]["y"] + pos[v]["y"]) / 2, 2)}
    return pos


def build_controls(circular: dict) -> str:
    """HTML-панель + JS для смены раскладки и темы (встраивается в страницу)."""
    circular_js = json.dumps(circular, ensure_ascii=False)

    panel = (
        '<div id="vizcontrols" style="position:fixed;top:12px;left:12px;z-index:1000;'
        'font-family:sans-serif;font-size:13px;background:#ffffff;border:1px solid #cccccc;'
        'border-radius:8px;padding:8px 12px;box-shadow:0 2px 10px rgba(0,0,0,.25);">'
        '<b>Раскладка:</b> '
        '<button onclick="applyLayout(\'barnes\')">Силовая</button> '
        '<button onclick="applyLayout(\'repulsion\')">Расталкивание</button> '
        '<button onclick="applyLayout(\'forceatlas2\')">ForceAtlas2</button> '
        '<button onclick="applyLayout(\'tree\')">Дерево</button> '
        '<button onclick="applyLayout(\'circular\')">Круг</button>'
        '&nbsp;&nbsp;<b>Тема:</b> '
        '<button onclick="setTheme(\'light\')">Светлая</button> '
        '<button onclick="setTheme(\'dark\')">Тёмная</button>'
        '</div>'
    )

    js = """
var LAYOUT_CIRCULAR = __CIRCULAR__;
function _unfixAll(){
  if(window.nodes){ nodes.forEach(function(n){ nodes.update({id: n.id, fixed: false}); }); }
}
function applyLayout(name){
  if(!window.network) return;
  if(name === "circular"){
    network.setOptions({physics: false, layout: {hierarchical: {enabled: false}}});
    nodes.forEach(function(n){
      var p = LAYOUT_CIRCULAR[n.id];
      if(p){ nodes.update({id: n.id, x: p.x, y: p.y, fixed: true}); }
    });
    network.fit({animation: true});
  } else if(name === "tree"){
    _unfixAll();
    network.setOptions({
      layout: {hierarchical: {enabled: true, direction: "UD", sortMethod: "directed",
                              levelSeparation: 150, nodeSpacing: 90}},
      physics: {enabled: true, solver: "hierarchicalRepulsion",
                hierarchicalRepulsion: {nodeDistance: 130, springLength: 160}}
    });
  } else {
    _unfixAll();
    var phys;
    if(name === "repulsion"){
      phys = {enabled: true, solver: "repulsion", repulsion: {nodeDistance: 200, springLength: 150}};
    } else if(name === "forceatlas2"){
      phys = {enabled: true, solver: "forceAtlas2Based",
              forceAtlas2Based: {springLength: 150, gravitationalConstant: -50, damping: 0.4}};
    } else {
      phys = {enabled: true, solver: "barnesHut",
              barnesHut: {springLength: 150, gravitationalConstant: -4000, damping: 0.09}};
    }
    network.setOptions({layout: {hierarchical: {enabled: false}}, physics: phys});
  }
}
function setTheme(theme){
  if(!window.network) return;
  var dark = theme === "dark";
  var bg = dark ? "#1b1b1f" : "#ffffff";
  var nodeFont = dark ? "#e8e8e8" : "#222222";
  var markerFont = dark ? "#d0d0d0" : "#333333";
  var edgeCol = dark ? "#a0a0a0" : "#999999";
  document.body.style.backgroundColor = bg;
  network.body.container.style.backgroundColor = bg;
  network.setOptions({edges: {color: {color: edgeCol, highlight: edgeCol, hover: edgeCol}}});
  nodes.forEach(function(n){
    var isMarker = String(n.id).indexOf("__edge_") === 0;
    var cur = n.font || {};
    nodes.update({id: n.id, font: {
      color: isMarker ? markerFont : nodeFont,
      size: cur.size || (isMarker ? 9 : 14),
      face: "sans-serif"
    }});
  });
}
"""
    js = js.replace("__CIRCULAR__", circular_js)
    return panel + "<script>" + js + "</script>"


def main() -> None:
    G = load_graph()
    net = Network(height="750px", width="100%", directed=True, bgcolor="#ffffff")
    net.set_edge_smooth("dynamic")

    for nid, d in G.nodes(data=True):
        net.add_node(
            nid,
            label=d["Label"],
            title=node_card(d),
            color=d["Color"],
            size=8 + d["Degree"] * 0.6,
            font={"color": "#222222", "face": "sans-serif"},
        )

    for i, (u, v, d) in enumerate(G.edges(data=True)):
        mid = f"__edge_{i}"
        net.add_node(
            mid,
            label=REL_RU.get(d["Relation"], d["Relation"].replace("_", " ").lower()),
            title=edge_card(G.nodes[u]["Label"], G.nodes[v]["Label"], d),
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

    # Встраиваем панель управления и JS переключения раскладки/темы
    html = OUT.read_text(encoding="utf-8")
    controls = build_controls(circular_positions(G))
    html = html.replace("</body>", controls + "</body>")
    OUT.write_text(html, encoding="utf-8")

    print(f"Сохранено: {OUT.resolve()} (раскладка и тема переключаются кнопками)")


if __name__ == "__main__":
    main()

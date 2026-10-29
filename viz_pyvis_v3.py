#!/usr/bin/env python3
"""graphV3.html — переключение раскладки узлов и тем оформления (pyvis + JS).

Поверх pyvis-графа добавляется панель кнопок:
- раскладка: Силовая (barnesHut), Расталкивание (repulsion), ForceAtlas2,
  Дерево (hierarchical) и Круг (предвычисленная упаковка);
- тема: Светлая / Тёмная (меняется фон, рёбра и цвет подписей);
- поиск: умный поиск узлов по частичному вводу и с допуском опечаток
  (подстрока + расстояние Левенштейна); клик по результату фокусирует узел.
Запуск: uv run python viz_pyvis_v3.py
Выход: graphV3.html
"""
import json
import math
import re
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
        '<div style="margin-top:6px;border-top:1px solid #eeeeee;padding-top:6px;">'
        '<b>Поиск:</b> '
        '<input id="searchbox" type="text" placeholder="буквы или с опечаткой…" '
        'style="width:170px;padding:2px 6px;border:1px solid #cccccc;border-radius:4px;" '
        'oninput="doSearch(this.value)">'
        '<div id="searchresults" style="max-height:170px;overflow:auto;margin-top:2px;"></div>'
        '</div>'
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
function _lev(a, b){
  var m = a.length, n = b.length;
  if(!m) return n; if(!n) return m;
  var prev = [], cur = [];
  for(var j = 0; j <= n; j++) prev[j] = j;
  for(var i = 1; i <= m; i++){
    cur[0] = i;
    for(var j = 1; j <= n; j++){
      cur[j] = Math.min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + (a[i-1] === b[j-1] ? 0 : 1));
    }
    var t = prev; prev = cur; cur = t;
  }
  return prev[n];
}
var _nodeIndex = null;
function _buildIndex(){
  _nodeIndex = nodes.map(function(n){
    return {id: n.id, label: String(n.label || n.id), isMarker: String(n.id).indexOf("__edge_") === 0};
  });
}
function doSearch(q){
  if(!window.nodes) return;
  if(!_nodeIndex) _buildIndex();
  var box = document.getElementById("searchresults");
  box.innerHTML = "";
  q = String(q || "").trim().toLowerCase();
  if(!q) return;
  var maxDist = q.length <= 3 ? 1 : 2;
  var res = [];
  _nodeIndex.forEach(function(it){
    var l = it.label.toLowerCase();
    var score;
    if(l.indexOf(q) !== -1){
      score = 0;
    } else {
      var d = _lev(q, l.slice(0, q.length));
      if(d <= maxDist) score = d + 1;
    }
    if(score !== undefined) res.push({it: it, score: score});
  });
  res.sort(function(a, b){ return a.score - b.score; });
  res = res.slice(0, 12);
  if(!res.length){
    box.innerHTML = '<div style="color:#888888;font-size:12px;padding:2px 4px;">ничего не найдено</div>';
    return;
  }
  res.forEach(function(r){
    var d = document.createElement("div");
    d.textContent = r.it.label + (r.it.isMarker ? " · связь" : "");
    d.style.cssText = "cursor:pointer;padding:2px 4px;font-size:12px;border-radius:3px;";
    d.onmouseenter = function(){ this.style.background = "#e0ecff"; };
    d.onmouseleave = function(){ this.style.background = ""; };
    d.onclick = function(){
      network.selectNodes([r.it.id], false);
      network.focus(r.it.id, {scale: 1.5, animation: {duration: 500, easingFunction: "easeInOutQuad"}});
    };
    box.appendChild(d);
  });
}
"""
    js = js.replace("__CIRCULAR__", circular_js)
    return panel + "<script>" + js + "</script>"


def _inline_assets(html: str) -> str:
    """Делает HTML самодостаточным: встраивает vis-network локально и
    убирает внешние ссылки на bootstrap/CDN (нет зависимостей от сети)."""
    import pyvis
    lib = Path(pyvis.__file__).parent / "templates" / "lib" / "vis-9.1.2"
    js = (lib / "vis-network.min.js").read_text(encoding="utf-8")
    css = (lib / "vis-network.css").read_text(encoding="utf-8")
    js = js.replace("</script>", "<\\/script>")

    html = re.sub(
        r'<script[^>]*src="[^"]*vis-network[^"]*\.js"[^>]*>\s*</script>',
        lambda m: '<script type="text/javascript">\n' + js + '\n</script>',
        html,
    )
    html = re.sub(
        r'<link[^>]*href="[^"]*vis-network[^"]*\.css"[^>]*>',
        lambda m: '<style>\n' + css + '\n</style>',
        html,
    )
    html = re.sub(r'<script[^>]*src="[^"]*bootstrap[^"]*"[^>]*>\s*</script>', '', html)
    html = re.sub(r'<link[^>]*href="[^"]*bootstrap[^"]*"[^>]*>', '', html)
    return html


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
    html = _inline_assets(html)
    OUT.write_text(html, encoding="utf-8")

    print(f"Сохранено: {OUT.resolve()} (раскладка и тема переключаются кнопками)")


if __name__ == "__main__":
    main()

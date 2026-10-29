#!/usr/bin/env python3
"""graphV5.html — граф без изолированных узлов (все связи дополнены).

То же оформление, умный поиск и самодостаточные (инлайн) библиотеки,
что и в graphV4, но каждый узел связан с эпохой/концепцией/открытием.
Запуск: uv run python viz_pyvis_v5.py
Выход: graphV5.html
"""
from pathlib import Path

import viz_pyvis_v3 as v3

v3.OUT = Path("graphV5.html")

if __name__ == "__main__":
    v3.main()

#!/usr/bin/env python3
"""graphV4.html — расширенная база знаний истории медицины.

То же оформление и панель управления, что у graphV3, но на расширенных данных
(включая врачей и учёных России и СССР из graph_extra.json).
Запуск: uv run python viz_pyvis_v4.py
Выход: graphV4.html
"""
from pathlib import Path

import viz_pyvis_v3 as v3

v3.OUT = Path("graphV4.html")

if __name__ == "__main__":
    v3.main()

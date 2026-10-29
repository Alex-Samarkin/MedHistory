#!/usr/bin/env python3
"""Запускает визуализацию в браузере по умолчанию (кроссплатформенно).

Открывает самодостаточный graphV4.html в системном браузере.
Работает на Windows, macOS и Linux (нужен только Python 3).
Для нативного исполняемого файла без Python:
    pip install pyinstaller
    pyinstaller --onefile launch.py
(распространять launch(.exe) вместе с graphV4.html в одной папке).
"""
import sys
import webbrowser
from pathlib import Path


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):  # собрано PyInstaller
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


DEFAULT = _app_dir() / "graphV4.html"


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not target.exists():
        raise SystemExit(f"Файл не найден: {target}")
    print(f"Открываю: {target}")
    webbrowser.open(target.resolve().as_uri())


if __name__ == "__main__":
    main()

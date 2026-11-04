#!/usr/bin/env python3
"""Read-only AI research report generator for K.A.P.R.I."""
import argparse, json, os, sys, urllib.error, urllib.request
from pathlib import Path

SUFFIXES = {".kt", ".kts", ".java", ".xml", ".gradle", ".properties", ".md", ".yml", ".yaml", ".json", ".toml", ".pro", ".txt"}
SKIP = {".git", ".gradle", "build", ".idea", "captures", "node_modules"}

def collect(root):
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUFFIXES and not any(x in SKIP for x in p.parts)]
    files.sort(key=lambda p: (0 if "app/src/main" in p.as_posix() else 1 if p.name in {"build.gradle.kts", "settings.gradle.kts", "AndroidManifest.xml"} else 2, p.as_posix()))
    out, total = [], 0
    for p in files:
        try: content = p.read_text(encoding="utf-8", errors="replace")[:12000]
        except OSError: continue
        chunk = f"\n\n===== FILE: {p.relative_to(root)} =====\n{content}"
        if total + len(chunk) > 115000: break
        out.append(chunk); total += len(chunk)
    return "\n".join(out) or "Текстовые файлы не найдены."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    a = ap.parse_args()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("Не задан GitHub Actions Secret GEMINI_API_KEY. См. docs/ai-research.md.", file=sys.stderr); return 2
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    repo = os.getenv("SOURCE_REPOSITORY", "loslam-del/K.A.P.R.I")
    commit = os.getenv("SOURCE_COMMIT", "unknown")
    focus = os.getenv("RESEARCH_FOCUS", "Предложи лучшие улучшения К.А.П.Р.И.")
    prompt = f"""Ты — технический исследователь проекта К.А.П.Р.И. Подготовь на русском подробный отчёт.
Фокус: {focus}
Репозиторий: {repo}; ревизия: {commit}

Структура:
1) Архитектура — только подтверждённые файлами факты.
2) 10 ценных улучшений: польза, сложность, зависимости, риски.
3) Архитектура Mobile Runner: Android-компоненты, безопасный обмен заданиями/отчётами с KAPRI-LAB, офлайн-поведение.
4) Идеи для надёжности, UX, приватности, производительности и тестируемости.
5) План реализации в 3-5 этапов с критериями готовности.
6) Ограничения Android и план тестирования.
7) Три лучших следующих шага.

Отделяй факты от гипотез. Не выдумывай API/классы/возможности. Не предлагай обход разрешений, скрытое управление телефоном, root или сбор секретов. Не изменяй код, не создавай PR и не публикуй APK. Не включай секреты. Указывай существующие файлы только если они есть в контексте. Перечисли пробелы в данных.

Выборка исходников:
{collect(a.source)}
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"contents":[{"role":"user","parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.65,"maxOutputTokens":8192}}
    req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode(), headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as res: data = json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Gemini API HTTP {e.code}. Проверь secret, модель и доступ API.", file=sys.stderr); return 3
    except (urllib.error.URLError, TimeoutError):
        print("Нет соединения с Gemini API или истёк тайм-аут.", file=sys.stderr); return 4
    except (json.JSONDecodeError, OSError):
        print("Не удалось прочитать ответ Gemini API.", file=sys.stderr); return 5
    try: answer = "\n".join(part["text"] for c in data["candidates"] for part in c.get("content",{}).get("parts",[]) if "text" in part).strip()
    except (KeyError, TypeError): answer = ""
    if not answer:
        print("Модель вернула пустой ответ.", file=sys.stderr); return 6
    a.output.parent.mkdir(parents=True, exist_ok=True)
    header = f"# Ночной исследовательский отчёт К.А.П.Р.И.\n\n- Репозиторий: {repo}\n- Ревизия: {commit}\n- Модель: {model}\n- Режим: только чтение; код не изменялся.\n\n---\n\n"
    a.output.write_text(header + answer + "\n", encoding="utf-8")
    print(f"Отчёт создан: {a.output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())

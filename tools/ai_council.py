#!/usr/bin/env python3
"""Multi-round, read-only Gemini/OpenAI discussion for KAPRI-LAB."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SUFFIXES = {".kt", ".kts", ".java", ".xml", ".gradle", ".properties", ".md",
            ".yml", ".yaml", ".json", ".toml", ".pro", ".txt"}
SKIP = {".git", ".gradle", "build", ".idea", "captures", "node_modules"}

def collect(root):
    files = [p for p in root.rglob("*") if p.is_file()
             and p.suffix.lower() in SUFFIXES
             and not any(part in SKIP for part in p.parts)]
    files.sort(key=lambda p: (0 if "app/src/main" in p.as_posix() else 1, p.as_posix()))
    chunks, total = [], 0
    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")[:12000]
        except OSError:
            continue
        chunk = f"\n\n===== FILE: {path.relative_to(root)} =====\n{content}"
        if total + len(chunk) > 100000:
            break
        chunks.append(chunk)
        total += len(chunk)
    return "\n".join(chunks) or "Текстовые файлы не найдены."

def post_json(url, headers, payload):
    request = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # Do not print response bodies: they may contain provider diagnostics.
        raise RuntimeError(f"API вернул HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("Сеть недоступна или истёк тайм-аут API") from None

def gemini(text, key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    data = post_json(url, {}, {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"temperature": 0.55, "maxOutputTokens": 6000}})
    return "\n".join(
        part["text"] for candidate in data.get("candidates", [])
        for part in candidate.get("content", {}).get("parts", [])
        if "text" in part).strip()

def openai(text, key, model):
    data = post_json("https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {key}"},
        {"model": model, "messages": [{"role": "user", "content": text}],
         "temperature": 0.5, "max_tokens": 6000})
    return data["choices"][0]["message"]["content"].strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    gem_key = os.getenv("GEMINI_API_KEY", "").strip()
    open_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not gem_key or not open_key:
        print("Нужны оба GitHub Secrets: GEMINI_API_KEY и OPENAI_API_KEY.", file=sys.stderr)
        return 2
    gem_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    open_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    focus = os.getenv("RESEARCH_FOCUS", "Предложи лучшие улучшения К.А.П.Р.И.")
    repo = os.getenv("SOURCE_REPOSITORY", "loslam-del/K.A.P.R.I")
    commit = os.getenv("SOURCE_COMMIT", "unknown")
    source = collect(args.source)
    rules = ("Отделяй факты от гипотез; не выдумывай существующие классы и API. "
             "Не предлагай обход разрешений Android, скрытое управление устройством, "
             "root или сбор секретов. Не раскрывай секреты. Только анализ, без изменения кода.")
    try:
        first = gemini(
            f"Ты технический исследователь К.А.П.Р.И. На русском исследуй проект по теме: {focus}. "
            f"Репозиторий {repo}, ревизия {commit}. Дай архитектурные факты, 7 улучшений, "
            f"риски, идеи Mobile Runner и план этапов. {rules}\n\nИсходники:\n{source}",
            gem_key, gem_model)
        if not first:
            raise RuntimeError("Gemini вернул пустой ответ")
        critique = openai(
            f"Ты независимый технический рецензент К.А.П.Р.И. Проверь исследование Gemini. "
            f"Найди неподтверждённые выводы, слабые места, риски и альтернативы. "
            f"Затем задай конкретные вопросы для второго раунда. {rules}\n\nИсследование:\n{first}",
            open_key, open_model)
        if not critique:
            raise RuntimeError("OpenAI вернул пустой ответ")
        response = gemini(
            f"Ответь на критику второго ИИ. Признай ошибки, где критика обоснована; "
            f"защити только подтверждённые выводы; обнови приоритеты. {rules}\n\n"
            f"Исходное исследование:\n{first}\n\nКритика:\n{critique}",
            gem_key, gem_model)
        if not response:
            raise RuntimeError("Gemini вернул пустой ответ на критику")
        final = openai(
            f"Ты модератор совета двух ИИ. Составь итоговый отчёт на русском: "
            f"согласованные идеи, отклонённые идеи с причинами, нерешённые разногласия, "
            f"топ-5 задач по приоритету, критерии готовности и вопросы владельцу проекта. "
            f"Не добавляй неподтверждённых фактов. {rules}\n\n"
            f"Раунд 1 — Gemini:\n{first}\n\nРаунд 2 — критика OpenAI:\n{critique}"
            f"\n\nРаунд 3 — ответ Gemini:\n{response}",
            open_key, open_model)
        if not final:
            raise RuntimeError("OpenAI не сформировал итог")
    except (RuntimeError, KeyError, TypeError, ValueError) as error:
        print(f"Совет не завершён: {error}", file=sys.stderr)
        return 3

    header = (f"# Ночной совет ИИ К.А.П.Р.И.\n\n"
              f"- Репозиторий: {repo}\n- Ревизия: {commit}\n"
              f"- Gemini: {gem_model}\n- OpenAI API: {open_model}\n"
              f"- Тема: {focus}\n- Режим: только чтение\n\n---\n\n")
    body = ("## Раунд 1 — исследование Gemini\n\n" + first +
            "\n\n## Раунд 2 — критика OpenAI\n\n" + critique +
            "\n\n## Раунд 3 — ответ Gemini\n\n" + response +
            "\n\n## Итоговый вердикт OpenAI\n\n" + final + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header + body, encoding="utf-8")
    print(f"Отчёт совета создан: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

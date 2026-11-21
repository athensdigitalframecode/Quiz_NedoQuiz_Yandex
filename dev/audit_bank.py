"""Аудит банка вопросов BANK из index.html. Ничего не меняет: пишет отчёт на ручную проверку.
Запуск: python dev/audit_bank.py  →  dist/bank_audit.md (и сводка в консоль).
Код выхода 1 — есть структурные ошибки (нет ответа, ответ среди неверных, нет картинки, плохая тема)."""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(path=ROOT / "index.html"):
    s = path.read_text(encoding="utf-8")
    bank, _ = json.JSONDecoder().raw_decode(s, s.index("const BANK=") + len("const BANK="))
    topics, _ = json.JSONDecoder().raw_decode(s, s.index("const TOPICS=") + len("const TOPICS="))
    return bank, topics


def norm(t):
    return re.sub(r"[^a-zа-я0-9]+", " ", str(t).lower().replace("ё", "е")).strip()


def audit(bank, topics, root=ROOT):
    """Возвращает {проверка: [(индекс, пояснение), ...]}. Индекс = позиция в BANK (её же используют seen/games)."""
    r = collections.defaultdict(list)
    seen = {}
    for i, x in enumerate(bank):
        q, a, w = str(x.get("q", "")), str(x.get("a", "")), [str(v) for v in x.get("w", [])]
        opts = [a] + w
        if not q.strip() or not a.strip():
            r["E: нет вопроса или ответа"].append((i, q[:80]))
        if any(not v.strip() for v in w) or len(w) != 3:
            r["E: неверных вариантов не 3 или есть пустой"].append((i, q[:80]))
        if a.strip() in {v.strip() for v in w}:  # с учётом регистра: «тОрты»/«тортЫ» — разные варианты
            r["E: верный ответ повторён среди неверных"].append((i, q[:80]))
        elif len({norm(v) for v in opts}) < len(opts):
            r["W: варианты совпадают без знаков (−, ², ×): проверить"].append((i, " / ".join(opts)))
        if not isinstance(x.get("c"), int) or not 0 <= x["c"] < len(topics):
            r["E: тема вне списка TOPICS"].append((i, str(x.get("c"))))
        if x.get("d") not in ("e", "m", "h"):
            r["E: сложность не e/m/h"].append((i, str(x.get("d"))))
        if "i" in x and not ((root / x["i"]).is_file() and (root / x["i"]).stat().st_size > 0):
            r["E: картинка отсутствует или пустая"].append((i, x["i"]))
        if len(q) > 160:
            r["W: вопрос длиннее 160 знаков (телефон)"].append((i, f"{len(q)}: {q[:80]}"))
        if any(len(v) > 40 for v in opts):
            r["W: вариант длиннее 40 знаков (телефон)"].append((i, max(opts, key=len)))
        if re.search(r"\b(не|кроме)\b", norm(q)) and re.search(r"\b(не|кроме)\b", " ".join(norm(v) for v in opts)):
            r["W: двойное отрицание (вопрос и варианты с «не/кроме»)"].append((i, q[:80]))
        # знаки оставляем («24 ÷ 3» ≠ «24 × 3»); вопросы по картинкам с одним текстом — разные
        k = " ".join(q.lower().replace("ё", "е").rstrip("?.! ").split()) + "|" + x.get("i", "")
        if k in seen:
            j = seen[k]
            same = norm(bank[j]["a"]) == norm(a)
            r["W: повтор вопроса" + ("" if same else " с другим ответом (!)")].append((i, f"= #{j}: {q[:70]}"))
        else:
            seen[k] = i
    # перекос «верный ответ — самый длинный»: доля по теме при случайности ≈ 25%
    by = collections.defaultdict(lambda: [0, 0])
    for x in bank:
        if len(x.get("w", [])) == 3 and "i" not in x:
            by[x["c"]][1] += 1
            by[x["c"]][0] += len(x["a"]) > max(len(v) for v in x["w"])
    for c, (n_long, n) in sorted(by.items()):
        if n >= 40 and n_long / n > 0.4:
            r["W: тема, где верный ответ чаще всего самый длинный"].append((c, f"{topics[c]}: {n_long}/{n} = {n_long * 100 // n}%"))
    return r


def main():
    bank, topics = load()
    r = audit(bank, topics)
    out = ROOT / "dist" / "bank_audit.md"
    out.parent.mkdir(exist_ok=True)
    lines = [f"# Аудит банка вопросов: {len(bank)} вопросов", "",
             "E — ошибка структуры, W — на ручную проверку. Номер — индекс в BANK. Скрипт ничего не исправляет.", ""]
    for k in sorted(r):
        lines += [f"## {k} — {len(r[k])}", ""] + [f"- #{i}: {t}" for i, t in r[k][:300]] + [""]
    out.write_text("\n".join(lines), encoding="utf-8")
    for k in sorted(r):
        print(f"{len(r[k]):5}  {k}")
    print("отчёт:", out)
    return 1 if any(k.startswith("E:") for k in r) else 0


if __name__ == "__main__":
    sys.exit(main())

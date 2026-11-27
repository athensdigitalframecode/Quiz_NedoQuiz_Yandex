"""Импорт данных тренировочной комнаты команды (вход: index.html#team).
  python -I dev/team_import.py fetch   — скачать метаданные и картинки в team/_raw/ (кэш, повторно не качает)
  python -I dev/team_import.py build   — проверить, отбраковать, убрать дубли, собрать team/<код из team/code.txt>.json, team/moderation.json, team/img/
  python -I dev/team_import.py sheet <cat> — контактные листы для ручной проверки (в team/_sheets/)
Папка team/ в .gitignore и не попадает в ZIP (build_zip.py берёт только корень и fonts/): чужие картинки не публикуются.
Ручная курация (исключения, русские названия) — dev/team_curation.json. Новый источник = новая функция src_* + запись в SOURCES."""
import csv, hashlib, html, io, json, pathlib, re, sys, time, urllib.parse, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = ROOT / "team"; RAW = T / "_raw"; IMG = T / "img"
BANKF = lambda: T / ((T / "code.txt").read_text(encoding="utf-8").strip() + ".json")  # банк назван кодом комнаты (team/code.txt): без кода в игру не войти
CUR = json.loads((ROOT / "dev/team_curation.json").read_text(encoding="utf-8"))
UA = {"User-Agent": "Mozilla/5.0 (team-quiz-import)"}

SOURCES = {
    "pmovva": {"name": "pmovva/rebus-puzzles (Hugging Face)", "url": "https://huggingface.co/datasets/pmovva/rebus-puzzles", "lic": "CC BY 4.0", "rights": "ok"},
    "rebus": {"name": "Re-Bus, TrishanuDas/rebus-dataset (Hugging Face)", "url": "https://huggingface.co/datasets/TrishanuDas/rebus-dataset",
              "lic": "Apache-2.0 на HF; авторы: личное/учебное использование без коммерции. Картинки из eslvault.com, kids.niehs.nih.gov, flashbynight.com", "rights": "ok"},
    "emojiscreen": {"name": "brittanyrw/emojiscreen (GitHub) + русские названия из Wikidata", "url": "https://github.com/brittanyrw/emojiscreen", "lic": "GPL-3.0; Wikidata — CC0", "rights": "ok"},
    "art": {"name": "egil10/art (список популярных картин) + Wikidata + Wikimedia Commons", "url": "https://github.com/egil10/art",
            "lic": "список — факты из Wikidata (CC0); изображения — свободная лицензия каждого файла Commons", "rights": "ok"},
    "bigbench": {"name": "google/BIG-bench, задача emoji_movie + русские названия из Wikidata", "url": "https://github.com/google/BIG-bench/tree/main/bigbench/benchmark_tasks/emoji_movie", "lic": "Apache-2.0; Wikidata — CC0", "rights": "ok"},
    "scizor": {"name": "scizor666/rebus (GitHub), пул ru-image", "url": "https://github.com/scizor666/rebus", "lic": "MIT; эмодзи OpenMoji — CC BY-SA 4.0 (лицензия не проверялась, добавлено по решению владельца 27.11)", "rights": "ok"},
    "columbus": {"name": "koen-47/COLUMBUS (Hugging Face)", "url": "https://huggingface.co/datasets/koen-47/COLUMBUS", "lic": "MIT (по карточке на HF)", "rights": "ok"},
    "fuzzysb": {"name": "fuzzysb/Logo-Quiz-Logos (GitHub)", "url": "https://github.com/fuzzysb/Logo-Quiz-Logos", "lic": "LGPL-3.0 на репозиторий; логотипы — товарные знаки владельцев", "rights": "approval"},
}
CATS = {
    "rebus_en": {"name": "Ребусы (английские)", "ico": "🧩", "lang": "en", "q": "Разгадайте ребус (ответ по-английски)"},
    "rebus_ru": {"name": "Ребусы (русские)", "ico": "🧩", "lang": "ru", "q": "Разгадайте ребус"},
    "logos": {"name": "Логотипы и бренды", "ico": "🏷️", "lang": "en", "q": "Какой это бренд?"},
    "emoji": {"name": "Фильмы и сериалы в эмодзи", "ico": "🎬", "lang": "ru", "q": "Какой фильм, сериал или мюзикл зашифрован эмодзи?"},
    "paintings": {"name": "Известные картины", "ico": "🖼️", "lang": "ru", "q": "Как называется эта картина?"},
}

def get(url, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: return r.read()
        except Exception as e:
            if k == tries - 1: raise
            time.sleep(2 + 3 * k)

def cached(name, url):
    p = RAW / name
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        try: p.write_bytes(get(url))
        except Exception as e: print("  нет:", url, e); return None
    return p

# ---------- fetch: метаданные → список записей {sid, key, url, a, acc, d, y, cat, ref, extra} ----------
def src_pmovva():
    p = cached("pmovva/rebus_dataset.csv", "https://huggingface.co/datasets/pmovva/rebus-puzzles/resolve/main/rebus_dataset.csv")
    out = []
    for r in csv.DictReader(p.read_text(encoding="utf-8").splitlines()):
        alt = json.loads(r["alternate_solutions"]) if r["alternate_solutions"].strip() else []
        out.append({"key": r["filename"], "url": "https://huggingface.co/datasets/pmovva/rebus-puzzles/resolve/main/rebus_dataset/" + r["filename"],
                    "a": r["solution"].strip(), "acc": alt, "d": "m", "cat": "rebus_en", "ref": "rebus_dataset/" + r["filename"]})
    return out

def src_columbus():
    """Ответ — в имени файла (a_fish_out_of_water_1_icon.png). У части задач два варианта, со значками и словами: build оставит первый (значки — сортируем вперёд)."""
    fs = [s["rfilename"] for s in jget("columbus/api.json", "https://huggingface.co/api/datasets/koen-47/COLUMBUS").get("siblings", []) if s["rfilename"].startswith("images/")]
    out = []
    for f in sorted(fs, key=lambda f: ("_non-icon" in f, f)):
        a = re.sub(r"(_\d+)?(_icon|_non-icon)?$", "", f[7:].rsplit(".", 1)[0]).replace("_", " ").strip()
        out.append({"key": f[7:], "url": "https://huggingface.co/datasets/koen-47/COLUMBUS/resolve/main/" + urllib.parse.quote(f), "a": a, "acc": [], "d": "m",
                    "cat": "rebus_en", "ref": "https://huggingface.co/datasets/koen-47/COLUMBUS"})
    return out

def src_rebus():
    p = cached("rebus/full.csv", "https://huggingface.co/datasets/TrishanuDas/rebus-dataset/resolve/main/RebusPuzzlesFullDataset.csv")
    out = []
    for r in csv.DictReader(p.read_text(encoding="utf-8").splitlines()):
        if r["is_augmented"] != "False": continue  # 611 копий с фоном ControlNet — те же ответы, исключаем
        fn = r["img_url"].rsplit("/", 1)[1]
        out.append({"key": fn, "url": r["img_url"], "a": r["answer"].strip(), "acc": [], "d": {"EASY": "e", "HARD": "h"}.get(r["Difficulty"], "m"),
                    "cat": "rebus_en", "ref": r["source"], "hint": r["hint"].strip()})
    return out

def src_fuzzysb():
    p = cached("fuzzysb/LogoQuestions.json", "https://raw.githubusercontent.com/fuzzysb/Logo-Quiz-Logos/master/LogoQuestions.json")
    out, c = [], lambda s: norm(s).replace(" ", "")
    for q in json.loads(p.read_text(encoding="utf-8"))["Questions"]:
        # Utterances писались для голосового Alexa («A Deed Ass», «Ping» для Bing): берём только варианты, содержащие название или входящие в него
        acc = [u for u in q.get("Utterances", []) if len(c(u)) >= 3 and (c(q["Name"]) in c(u) or c(u) in c(q["Name"]))]
        out.append({"key": q["Name"], "url": q["logoSrc"], "a": q["Name"].strip(), "acc": acc, "d": "e", "cat": "logos",
                    "ref": q["logoSrc"], "hint": (q.get("Hints", {}).get("en-GB") or [""])[0]})
    return out

def jget(name, url):
    p = cached(name, url)
    return json.loads(p.read_text(encoding="utf-8")) if p else {}

def sparql(name, query):
    return jget(name, "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(query))["results"]["bindings"]

def wd(ids, name):
    """Метки и псевдонимы ru/en и утверждения сущностей Wikidata (CC0), пачками по 50."""
    out = {}
    for k in range(0, len(ids), 50):
        part = ids[k:k + 50]
        j = jget(f"{name}_{k}.json", "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels|aliases|claims&languages=ru|en&ids=" + "|".join(part))
        out.update(j.get("entities", {}))
    return out

lab = lambda e, l: ((e or {}).get("labels", {}).get(l) or {}).get("value", "")
als = lambda e, l: [x["value"] for x in (e or {}).get("aliases", {}).get(l, [])]

def src_emojiscreen():
    TY = {"movies": "фильм", "tv": "сериал", "musicals": "мюзикл"}
    rows = []
    for f, ty in TY.items():
        t = cached(f"emojiscreen/{f}.js", f"https://raw.githubusercontent.com/brittanyrw/emojiscreen/main/data/{f}.js").read_text(encoding="utf-8")
        for b in re.findall(r"\{(.*?)\}", t, re.S):
            g = lambda k: (re.search(k + r"""\s*:\s*(["'`])(.*?)\1""", b, re.S) or [None, None, ""])[2].strip()
            y = re.search(r"year\s*:\s*(\d{4})", b); tt = re.search(r"(tt\d+)", b)
            if g("title"): rows.append({"ty": ty, "title": g("title"), "em": g("emojiImgs"), "y": int(y.group(1)) if y else 0, "tt": tt.group(1) if tt else ""})
    tts = sorted({r["tt"] for r in rows if r["tt"]}); ru = {}
    for k in range(0, len(tts), 100):  # русские названия — из Wikidata по IMDb ID
        q = 'SELECT ?imdb ?ru ?ra WHERE { VALUES ?imdb {%s} ?item wdt:P345 ?imdb. OPTIONAL{?item rdfs:label ?ru FILTER(lang(?ru)="ru")} OPTIONAL{?item skos:altLabel ?ra FILTER(lang(?ra)="ru")} }' % " ".join(f'"{x}"' for x in tts[k:k + 100])
        for b in sparql(f"emojiscreen/wd_{k}.json", q):
            d = ru.setdefault(b["imdb"]["value"], {"ru": "", "ra": set()})
            if "ru" in b: d["ru"] = b["ru"]["value"]
            if "ra" in b: d["ra"].add(b["ra"]["value"])
    out = []
    for r in rows:
        w = ru.get(r["tt"], {"ru": "", "ra": set()})
        out.append({"key": f"{r['ty']}:{r['title']}", "url": None, "em": re.sub(r"\s+", " ", r["em"]), "a": r["title"], "a_main": w["ru"], "acc": sorted(w["ra"]),
                    "d": "m", "cat": "emoji", "ref": f"https://www.imdb.com/title/{r['tt']}/" if r["tt"] else "", "y": r["y"],
                    "e": f"{r['ty'].capitalize()}, {r['y'] or 'год не указан'}" + (f" · {r['title']}" if w["ru"] else ""),
                    "bad": "" if r["em"] else "нет эмодзи"})
    return out

def src_bigbench():
    """100 фильмов в эмодзи; ответы строчными по-английски, без IMDb ID — фильм ищем в Wikidata по названию. Дубли с emojiscreen снимает build (тот идёт раньше)."""
    j = jget("bigbench/task.json", "https://raw.githubusercontent.com/google/BIG-bench/main/bigbench/benchmark_tasks/emoji_movie/task.json")
    rows, qid = [], {}
    for x in j.get("examples", []):
        t = x["target"].strip(); em = x["input"].split("?", 1)[-1].strip(); sn = f"bigbench/s_{hashlib.sha1(t.encode()).hexdigest()[:12]}.json"
        if not (RAW / sn).exists(): time.sleep(1.5)  # Wikidata отвечает 429 на частые запросы
        s = jget(sn, "https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&type=item&language=en&limit=7&search=" + urllib.parse.quote(t))
        hit = next((h for h in s.get("search", []) if "film" in h.get("description", "")), {})  # shortcut: первый «...film» в поиске; редкие промахи править в team_curation.json
        rows.append((t, em, hit.get("id", ""), hit.get("label", ""))); qid[t] = hit.get("id", "")
    E = wd(sorted({h for h in qid.values() if h}), "bigbench/wd")
    out = []
    for t, em, h, hl in rows:  # метка из поиска: у многих фильмов английское название лежит в метке «mul», а не «en»
        e = E.get(h); en = hl if e and norm(hl) == norm(t) else ""  # чужой фильм с похожим названием не берём
        e = e if en else None
        d = next((c["mainsnak"]["datavalue"]["value"]["time"] for c in (e or {}).get("claims", {}).get("P577", []) if c["mainsnak"].get("datavalue")), "")
        y = int(d[1:5]) if d[1:5].isdigit() else 0; ru = lab(e, "ru")
        out.append({"key": f"фильм:{t}", "url": None, "em": em, "a": en or t.title(), "a_main": ru, "acc": [*als(e, "ru"), *als(e, "en")],
                    "d": "m", "cat": "emoji", "ref": f"https://www.wikidata.org/wiki/{h}" if en else "https://github.com/google/BIG-bench/tree/main/bigbench/benchmark_tasks/emoji_movie",
                    "y": y, "e": f"Фильм, {y or 'год не указан'}" + (f" · {en or t.title()}" if ru else ""), "bad": "" if em else "нет эмодзи"})
    return out

def src_scizor():
    """Русские ребусы из эмодзи и букв: картинка-токен = эмодзи OpenMoji по коду, апостроф ’ = отбросить букву. Показываются текстом (поле em), без картинок.
    shortcut: только пул ru-image; пул ru-char (230, буквы «над/в» друг друге) требует двумерной вёрстки — добавлять, если понадобится."""
    B = "https://raw.githubusercontent.com/scizor666/rebus/main/public/puzzles/"
    pools = jget("scizor/index.json", B + "index.json").get("pools", [])
    out = []
    for sh in next((p["shards"] for p in pools if p["lang"] == "ru" and p["pool"] == "image"), []):
        for x in jget("scizor/" + sh.replace("/", "_"), B + sh) or []:
            parts, bad = [], ""
            for t in x["tokens"]:
                if t["kind"] == "text": parts.append(t["text"]); continue
                cps = [int(c, 16) for c in t.get("assetId", "").split("-") if c]
                if t["kind"] != "image" or not cps or any(0xE000 <= c <= 0xF8FF or c >= 0xF0000 for c in cps): bad = "токен без эмодзи Unicode (свой значок OpenMoji)"; break
                g = "".join(map(chr, cps)) + ("️" if len(cps) == 1 else "")  # одиночный символ — всегда в эмодзи-вид (🎟, ⛽ иначе бывают текстовыми)
                parts.append("’" * t.get("dropStart", 0) + g + "’" * t.get("dropEnd", 0))
            out.append({"key": x["id"], "url": None, "em": " ".join(parts), "a": x["answer"], "a_main": "", "acc": [], "d": "m", "cat": "rebus_ru",
                        "ref": "https://github.com/scizor666/rebus", "y": 0, "e": x.get("trace", ""), "bad": bad or ("" if parts else "пустой ребус")})
    return out

def src_art():
    P = jget("art/popular.json", "https://raw.githubusercontent.com/egil10/art/main/public/paintings-popular.json")
    info = {}
    for k in range(0, len(P), 50):  # картинка и лицензия файла — Wikimedia Commons API
        j = jget(f"art/commons_{k}.json", "https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=800&iiextmetadatafilter=LicenseShortName&titles="
                 + urllib.parse.quote("|".join("File:" + x["image"] for x in P[k:k + 50])))
        norm_t = {n["to"]: n["from"] for n in j.get("query", {}).get("normalized", [])}
        for pg in j.get("query", {}).get("pages", {}).values():
            ii = (pg.get("imageinfo") or [{}])[0]
            info[norm_t.get(pg["title"], pg["title"])[5:]] = (ii.get("thumburl", ""), ((ii.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value", ""))
    E = wd([x["id"] for x in P], "art/wd")
    cr = sorted({c["mainsnak"]["datavalue"]["value"]["id"] for e in E.values() for c in e.get("claims", {}).get("P170", []) if c["mainsnak"].get("datavalue")})
    A = wd(cr, "art/wd_artists")
    out = []
    for x in P:
        e = E.get(x["id"], {}); url, lic = info.get(x["image"], ("", ""))
        c = [c["mainsnak"]["datavalue"]["value"]["id"] for c in e.get("claims", {}).get("P170", []) if c["mainsnak"].get("datavalue")]
        artist = lab(A.get(c[0]), "ru") if c else ""
        free = bool(re.search(r"public domain|^pd|cc0|cc[- ]by", lic, re.I))
        rec = {"a": x["title"], "a_main": lab(e, "ru"), "acc": [lab(e, "en"), *als(e, "ru"), *als(e, "en")]}
        if re.fullmatch(r"(self[- ]?portrait|portrait of the artist)( .*)?", x["title"].lower()):  # «Автопортрет» — угадывать имеет смысл автора
            rec = {"a": x["artist"], "a_main": artist, "acc": [lab(A.get(c[0]), "en"), *als(A.get(c[0]) if c else None, "ru")], "q": "Кто автор этого автопортрета?"}
        out.append({"key": x["id"], "url": url or None, **rec,
                    "d": "m", "cat": "paintings", "ref": f"https://www.wikidata.org/wiki/{x['id']}", "y": int(x["year"]) if str(x.get("year", "")).isdigit() else 0,
                    "e": f"{artist or x['artist']}, {x.get('year') or 'год неизвестен'}. Изображение: Wikimedia Commons, {lic or 'лицензия не указана'}",
                    "bad": "" if free else f"лицензия изображения не свободная или не указана ({lic or '—'})"})
    return out

FETCH = {"pmovva": src_pmovva, "rebus": src_rebus, "fuzzysb": src_fuzzysb,
         "emojiscreen": src_emojiscreen, "bigbench": src_bigbench, "scizor": src_scizor, "columbus": src_columbus, "art": src_art}

def fetch():
    meta = {}
    for sid, f in FETCH.items():
        recs = f(); ok = 0
        for r in recs:
            ext = (pathlib.PurePosixPath(urllib.parse.urlparse(r["url"] or "").path).suffix or ".img").lower()[:5]
            r["raw"] = f"{sid}/img/{hashlib.sha1(r['key'].encode()).hexdigest()[:16]}{ext}"
            if r["url"] and cached(r["raw"], r["url"]): ok += 1
        meta[sid] = recs; print(f"{sid}: записей {len(recs)}, картинок есть {ok}")
    (RAW / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=0), encoding="utf-8")

# ---------- build ----------
def norm(s):
    s = s.lower().replace("ё", "е").replace("’", "'").replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()

def flat(im):
    """Прозрачность — на белый фон (иначе чёрные логотипы пропадают на чёрном)."""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.getchannel("A")); return bg
    return im.convert("RGB")

def fp(im):
    """Отпечаток: dHash 16×16 (256 бит) + серая миниатюра 16×16. Один dHash склеивал разные картинки «текст на белом»."""
    g = im.convert("L"); d = g.resize((17, 16), Image.LANCZOS).tobytes(); t = g.resize((16, 16), Image.LANCZOS).tobytes()
    return sum(1 << i for i in range(256) if d[(i // 16) * 17 + i % 16] > d[(i // 16) * 17 + i % 16 + 1]), t

def same(a, b):
    return bin(a[0] ^ b[0]).count("1") <= 16 and sum(abs(x - y) for x, y in zip(a[1], b[1])) / 256 <= 6

def build():
    meta = {k: v for k, v in json.loads((RAW / "meta.json").read_text(encoding="utf-8")).items() if k in FETCH}  # в кэше могут остаться убранные источники (мемы)
    IMG.mkdir(parents=True, exist_ok=True)
    ex, ru, en = CUR["exclude"], CUR["ru"], CUR.get("en", {})
    good, mod, rej, seen_h, seen_a = [], [], [], [], {}
    stat = {sid: {"downloaded": 0, "imported": 0, "unverified": 0, "rejected": 0, "moderation": 0} for sid in meta}
    used = set()
    for sid, recs in meta.items():
        for r in recs:
            st = stat[sid]; base = {"src": sid, "key": r["key"], "a": r["a"], "ref": r["ref"]}
            def drop(why, to=rej, im=None):
                (to.append({**base, "why": why, **({"i": im} if im else {})})); st["rejected" if to is rej else "moderation"] += 1
            why = r.get("bad") or ex.get(sid, {}).get(r["key"])
            if r.get("em"):  # вопрос-эмодзи: картинки нет
                st["downloaded"] += 1
                if why: drop(why); continue
                h = None
            else:
                p = RAW / r["raw"]
                if not p.exists(): drop("картинка не скачалась / битая ссылка"); continue
                st["downloaded"] += 1
                try:
                    with Image.open(p) as im0: im0.verify()
                    im = Image.open(p); im.load(); im = flat(im)
                except Exception: drop("повреждённое изображение"); continue
                if min(im.size) < 40 or im.size[0] * im.size[1] < 10000: drop(f"слишком маленькое изображение {im.size}"); continue
                if why: drop(why); continue
                lo, hi = im.convert("L").getextrema()
                if hi - lo < 16: drop("пустое (однотонное) изображение"); continue
                h = fp(im)
                dup = None if sid == "columbus" else next((k for hh, k in seen_h if same(h, hh)), None)  # COLUMBUS — слова на белом: отпечатки склеивают разные ребусы, дубли снимает сверка ответов
                if dup: drop(f"визуальный дубль {dup}"); continue
            a, *alt = [s.strip() for s in r["a"].split("|") if s.strip()] or [""]  # «Crystallise|Crystallize»
            r = {**r, "acc": alt + [s.strip() for x in r["acc"] for s in x.split("|")]}
            na = norm(a)
            if not na: drop("пустой ответ"); continue
            ka = r["cat"] + ":" + na
            if ka in seen_a: drop(f"дубль ответа {seen_a[ka]}"); continue
            rk = f"{sid}:{r['key']}"
            q = {"id": rk, "c": r["cat"], "d": r["d"], "q": r.get("q") or CATS[r["cat"]]["q"], "a": ru.get(rk, {}).get("a") or r.get("a_main") or a,
                 "acc": [], "src": sid, "ref": r["ref"], "st": "auto"}
            if r.get("em"): q["em"] = r["em"]
            else:
                im.thumbnail((720, 720), Image.LANCZOS)
                buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True); b = buf.getvalue()
                q["i"] = fn = "team/img/" + hashlib.sha1(b).hexdigest()[:12] + ".jpg"
                (ROOT / fn).write_bytes(b); used.add(pathlib.Path(fn).name)
            if r.get("e"): q["e"] = r["e"]
            q["acc"] = list(dict.fromkeys(x for x in [a, *r["acc"], *ru.get(rk, {}).get("acc", []), *en.get(rk, [])] if norm(x) and x != q["a"]))
            if r.get("y"): q["y"] = r["y"]
            if r.get("hint"): q["e"] = r["hint"]
            reason = mod_reason(sid, r, q)
            if reason:
                q["st"] = "mod"; q["why"] = reason; mod.append(q); st["moderation"] += 1
            else:
                good.append(q); st["imported"] += 1
            if h: seen_h.append((h, rk))
            seen_a[ka] = rk
    for f in IMG.iterdir():
        if f.name not in used: f.unlink()
    cats = {k: {**v, "rights": rights_of(k, good), "n": sum(q["c"] == k for q in good)} for k, v in CATS.items()}
    for k, v in cats.items(): v["on"] = v["rights"] == "ok" or k in CUR.get("approved", [])  # неясные права — только после согласия владельца
    bank = {"v": 1, "built": time.strftime("%Y-%m-%d"), "cats": cats, "sources": SOURCES, "q": good}
    BANKF().write_text(json.dumps(bank, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (T / "moderation.json").write_text(json.dumps({"moderation": mod, "rejected": rej}, ensure_ascii=False, indent=1), encoding="utf-8")
    size = lambda d: sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    rep = {"by_source": stat, "by_cat": {k: v["n"] for k, v in cats.items()}, "raw_mb": round(size(RAW) / 2**20, 1), "img_mb": round(size(IMG) / 2**20, 1)}
    (T / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))

def mod_reason(sid, r, q):
    """Что не проверяется автоматически — в ручную модерацию, а не в игру."""
    ok = CUR["ok"].get(sid, [])
    if sid == "fuzzysb" and r["key"] not in ok: return "не просмотрен на контактном листе"
    return ""

def rights_of(cat, good):
    srcs = {q["src"] for q in good if q["c"] == cat}
    return "approval" if any(SOURCES[s]["rights"] == "approval" for s in srcs) else "ok"

def sheet(cat, start=0, n=20):
    """Контактный лист 5×4 с подписями-ответами для визуальной проверки."""
    from PIL import ImageDraw
    qs = json.loads(BANKF().read_text(encoding="utf-8"))["q"] + json.loads((T / "moderation.json").read_text(encoding="utf-8"))["moderation"]
    qs = [q for q in qs if q["c"] == cat or q["src"] == cat][start:start + n]
    W = 220; sh = Image.new("RGB", (W * 5, (W + 30) * 4), "white"); d = ImageDraw.Draw(sh)
    for k, q in enumerate(qs):
        im = Image.open(ROOT / q["i"]); im.thumbnail((W - 6, W - 6))
        x, y = (k % 5) * W, (k // 5) * (W + 30); sh.paste(im, (x + 3, y + 3))
        d.text((x + 3, y + W), f"{start + k}. {q['a']}"[:34], fill="black"); d.text((x + 3, y + W + 13), q["id"][:34], fill="gray")
    out = T / "_sheets" / f"{cat}_{start}.jpg"; out.parent.mkdir(exist_ok=True); sh.save(out, quality=80); print(out)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch": fetch()
    elif cmd == "build": build()
    elif cmd == "sheet": sheet(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    else: print(__doc__)

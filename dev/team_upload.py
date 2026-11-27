"""Загрузка тренировочной комнаты в закрытый бакет team-room основного сайта (Supabase tfgynsfmnrxumftuiflm).
Запуск (ключ service_role берёт из переменной окружения, в код и в файлы его не класть):
  $env:SUPABASE_SERVICE_ROLE_KEY = "<ключ из Supabase → Project Settings → API Keys>"
  python -I dev/team_upload.py
Кладёт bank.json (пути картинок team/img/x.jpg → img/x.jpg) и все картинки из него; повторный запуск перезаписывает."""
import concurrent.futures as cf, json, os, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = ROOT / "team"
URL = "https://tfgynsfmnrxumftuiflm.supabase.co/storage/v1/object/team-room/"
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
if not KEY:  # без переменной — ключ из буфера обмена: в Windows вставка в скрытое поле ввода ненадёжна
    import tkinter
    tk = tkinter.Tk(); tk.withdraw()
    try: KEY = tk.clipboard_get().strip()
    except tkinter.TclError: KEY = ""
    tk.destroy()
if not re.fullmatch(r"sb_secret_[A-Za-z0-9_-]{20,80}|eyJ[A-Za-z0-9_.-]{100,}", KEY):
    sys.exit("в буфере обмена (или в SUPABASE_SERVICE_ROLE_KEY) нет ключа service_role: скопируйте в Supabase ключ sb_secret_… и запустите снова")
print("ключ:", KEY[:12] + "…")

bank = json.loads((T / ((T / "code.txt").read_text(encoding="utf-8").strip() + ".json")).read_text(encoding="utf-8"))
imgs = sorted({q["i"] for q in bank["q"] if q.get("i")})
bad = [p for p in imgs if not re.fullmatch(r"team/img/[0-9a-f]{12}\.jpg", p)]
assert not bad, f"имена картинок не подходят функции team-room: {bad[:3]}"
for q in bank["q"]:
    if q.get("i"): q["i"] = q["i"][len("team/"):]

def put(path, data, ctype):
    rq = urllib.request.Request(URL + path, data=data, method="POST", headers={
        "Authorization": "Bearer " + KEY, "apikey": KEY, "Content-Type": ctype, "x-upsert": "true"})
    with urllib.request.urlopen(rq, timeout=60) as r: return r.status

with cf.ThreadPoolExecutor(8) as ex:
    futs = {ex.submit(put, p[len("team/"):], (ROOT / p).read_bytes(), "image/jpeg"): p for p in imgs}
    err = []
    for i, f in enumerate(cf.as_completed(futs), 1):
        try: f.result()
        except Exception as e: err.append((futs[f], e))
        if i % 200 == 0: print(f"{i}/{len(imgs)}")
if err: sys.exit(f"не загрузились {len(err)} картинок, например {err[0]} — запустите ещё раз")
put("bank.json", json.dumps(bank, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), "application/json")
print(f"готово: bank.json, {len(bank['q'])} вопросов, {len(imgs)} картинок")

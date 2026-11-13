"""Проставляет версию сборки: BUILD в index.html, V в sw.js, version.json.
Запуск: python dev/stamp.py .   (без этого игроки получат старый кэш)"""
import hashlib, json, re, sys, pathlib
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
idx, sw = root / "index.html", root / "sw.js"
html, swj = idx.read_text(encoding="utf-8"), sw.read_text(encoding="utf-8")
pat_h, pat_s = r'const BUILD="[0-9a-f]+"', r'const V="[0-9a-f]+"'
assert re.search(pat_h, html) and re.search(pat_s, swj), "якорь BUILD или V не найден"
# хеш без самой версии, чтобы повторный запуск давал тот же результат
body = re.sub(pat_h, "", html) + re.sub(pat_s, "", swj)
# локальные зависимости тоже в хеше: сервис-воркер отдаёт их из кэша до смены версии
for f in [root / "supabase.js", *sorted((root / "fonts").glob("*.css"))]:
    if f.exists(): body += f.read_text(encoding="utf-8")
v = hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]
idx.write_text(re.sub(pat_h, f'const BUILD="{v}"', html), encoding="utf-8", newline="")
sw.write_text(re.sub(pat_s, f'const V="{v}"', swj), encoding="utf-8", newline="")
(root / "version.json").write_text(json.dumps({"v": v}), encoding="utf-8")
print(v)

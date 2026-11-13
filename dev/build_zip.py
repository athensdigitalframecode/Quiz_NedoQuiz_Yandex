"""Сборка ZIP для консоли Яндекс Игр: python dev/build_zip.py
Проставляет версию (stamp.py), кладёт в архив файлы игры из корня и папку fonts/,
без dev/, docs/, *.md, .git; проверяет имена (латиница, без пробелов) и размер (до 100 МБ)."""
import pathlib, re, subprocess, sys, zipfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
v = subprocess.check_output([sys.executable, str(ROOT / "dev/stamp.py"), str(ROOT)], text=True).strip()
files = [p for p in ROOT.iterdir() if p.is_file() and not p.name.startswith(".") and p.suffix.lower() != ".md"]
files += sorted((ROOT / "fonts").glob("*"))
need = {"index.html", "supabase.js", "gp-adapter.js", "gp-config.js", "fonts/fonts.css", "manifest.json", "version.json"}
names = {p.relative_to(ROOT).as_posix() for p in files}
assert need <= names, f"нет файлов: {need - names}"
bad = [n for n in names if not re.fullmatch(r"[A-Za-z0-9._/-]+", n)]
assert not bad, f"недопустимые имена: {bad}"
size = sum(p.stat().st_size for p in files)
assert size < 100 * 2**20, f"размер {size} больше 100 МБ"
out = ROOT / "dist" / f"quiz-yandex-{v}.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files): z.write(p, p.relative_to(ROOT).as_posix())
print(f"{out.relative_to(ROOT)}: {len(files)} файлов, {size/2**20:.1f} МБ без сжатия, {out.stat().st_size/2**20:.1f} МБ архив")

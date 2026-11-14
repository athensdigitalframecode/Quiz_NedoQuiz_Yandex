"""Сборка ZIP: python dev/build_zip.py (Яндекс, GamePush выключен) или python dev/build_zip.py --gp
(GamePush: вместо gp-config.js кладётся локальный gp-config.local.js, он не в git).
Проставляет версию (stamp.py), кладёт в архив файлы игры из корня и папку fonts/,
без dev/, docs/, *.md, .git; проверяет имена (латиница, без пробелов) и размер (до 100 МБ)."""
import pathlib, re, subprocess, sys, zipfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
v = subprocess.check_output([sys.executable, str(ROOT / "dev/stamp.py"), str(ROOT)], text=True).strip()
files = [p for p in ROOT.iterdir() if p.is_file() and not p.name.startswith(".") and p.suffix.lower() != ".md" and ".local." not in p.name]
files += sorted((ROOT / "fonts").glob("*"))
need = {"index.html", "supabase.js", "gp-adapter.js", "gp-config.js", "fonts/fonts.css", "manifest.json", "version.json"}
names = {p.relative_to(ROOT).as_posix() for p in files}
assert need <= names, f"нет файлов: {need - names}"
bad = [n for n in names if not re.fullmatch(r"[A-Za-z0-9._/-]+", n)]
assert not bad, f"недопустимые имена: {bad}"
size = sum(p.stat().st_size for p in files)
assert size < 100 * 2**20, f"размер {size} больше 100 МБ"
GP = "--gp" in sys.argv
if GP: assert (ROOT / "gp-config.local.js").exists(), "нет gp-config.local.js"
out = ROOT / "dist" / f"quiz-{'gamepush' if GP else 'yandex'}-{v}.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):
        if GP and p.name == "gp-config.js": z.write(ROOT / "gp-config.local.js", "gp-config.js")
        else: z.write(p, p.relative_to(ROOT).as_posix())
print(f"{out.relative_to(ROOT)}: {len(files)} файлов, {size/2**20:.1f} МБ без сжатия, {out.stat().st_size/2**20:.1f} МБ архив")

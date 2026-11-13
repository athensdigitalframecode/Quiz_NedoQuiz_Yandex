"""Все автотесты подряд: python dev/tests/run_all.py  (код выхода 1, если есть FAIL)"""
import pathlib, subprocess, sys
here = pathlib.Path(__file__).parent
bad = [t.name for t in sorted(here.glob("t_*.py")) if subprocess.call([sys.executable, str(t)]) != 0]
print("ИТОГ:", "все прошли" if not bad else "FAIL в " + ", ".join(bad))
sys.exit(1 if bad else 0)

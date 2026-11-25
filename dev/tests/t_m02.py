"""M02 (§12.1): место в профиле считает сервер (player_places), рейтинг режима целиком не скачивается.
Правила функции проверены SQL-сценарием в транзакции с откатом (см. dev/sql/m02_player_places.sql).
Запуск: python dev/tests/t_m02.py"""
from harness import Run

UID = "00000000-0000-4000-8000-000000000001"  # пользователь подставной базы
st = lambda u, r: {"path": f"stats/solo/players/{u}", "col": "stats/solo/players", "id": u, "data": {"r": r, "g": 3, "w": 1}}
seed = [st(UID, 1050), st("a1", 1200), st("a2", 1100), st("a3", 900), st("kid", 1500),
        {"path": "profiles/kid", "col": "profiles", "id": "kid", "data": {"nick": "Малыш", "age": "8", "createdAt": 1}}]

with Run("t_m02") as r:
    pg = r.page(sdk=True, seed=seed)
    pg.wait_for_function("document.body.dataset.scr==='s-home'&&!!ME", timeout=15000)

    n0 = pg.evaluate("__sel.length")
    pl = pg.evaluate(f"myPlaces({UID!r},{{solo:{{r:1050}}}})")
    r.ok(pl == {"solo": 3}, f"место 3: выше двое взрослых, ребёнок в своём разряде не считается ({pl})")
    r.ok(not any(c.startswith("stats/") for c, _ in pg.evaluate(f"__sel.slice({n0})")), "рейтинг режима не скачивается")
    r.ok(pg.evaluate("__rpc.some(x=>x[0]==='player_places')"), "вызвана player_places")
    r.ok(pg.evaluate("myPlaces('kid',{solo:{r:1500}})") == {"solo": 1}, "ребёнок — 1-й в своём разряде")
    r.ok(pg.evaluate("myPlaces('a3',{})") == {}, "без записи режима места нет")

    pg.evaluate("nav('me')")
    pg.wait_for_function("document.getElementById('meStats').innerText.includes('место')", timeout=10000)
    r.ok("3 место" in pg.inner_text("#meStats"), "в профиле «3 место»")

    # запасной путь: если функции нет (старая база) — прежний расчёт
    pg.evaluate("window.__sbr=sb.rpc;sb.rpc=(n,a)=>n==='player_places'?Promise.resolve({data:null,error:{message:'no fn'}}):__sbr(n,a);0")
    r.ok(pg.evaluate(f"myPlaces({UID!r},{{solo:{{r:1050}}}})") == {"solo": 3}, "без функции — прежний расчёт, то же место")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

"""Supabase Free: подписка на коллекцию (profiles и др.) подгружает только изменённые строки, а не всю коллекцию.
Запуск: python dev/tests/t_sbdelta.py"""
from harness import Run

seed = [{"path": f"profiles/p{i}", "col": "profiles", "id": f"p{i}", "updated_at": "2026-01-01T00:00:00.000Z", "data": {"nick": f"Игрок {i}"}} for i in range(40)]
SEL = "(c=>__sel.filter(x=>x[0]===c))"

with Run("t_sbdelta") as r:
    pg = r.page(sdk=True, seed=seed)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_function("typeof profiles==='object'&&!!profiles.p39", timeout=10000)
    first = pg.evaluate(f"{SEL}('profiles')[0][1]")
    r.ok(first >= 40, f"первая загрузка — вся коллекция ({first} строк)")

    # чужой игрок появился (как запись другого клиента) → подгружается одна строка
    n0 = pg.evaluate(f"{SEL}('profiles').length")
    pg.evaluate("__db.set('profiles/new1',{path:'profiles/new1',col:'profiles',id:'new1',updated_at:new Date().toISOString(),data:{nick:'Новичок'}});sbBump('profiles/new1')")
    pg.wait_for_function("!!profiles.new1", timeout=5000)
    last = pg.evaluate(f"{SEL}('profiles').slice({n0}).map(x=>x[1])")
    r.ok(last and max(last) < 10, f"после изменения отдано мало строк, не вся коллекция ({last})")
    r.ok(pg.evaluate("Object.keys(profiles).length") >= 41, "старые профили на месте")

    # изменение существующего профиля видно
    pg.evaluate("doc=>{const r=__db.get('profiles/p3');r.data={nick:'Переименован'};r.updated_at=new Date(Date.now()+5).toISOString();sbBump('profiles/p3')}", None)
    pg.wait_for_function("profiles.p3&&profiles.p3.nick==='Переименован'", timeout=5000)
    r.ok(True, "изменение чужого профиля подхвачено")

    # своё удаление → полная сверка, строка исчезает
    pg.evaluate("db.doc('profiles/p5').delete()")
    pg.wait_for_function("!profiles.p5", timeout=5000)
    r.ok(True, "удалённый профиль исчез (полная сверка после удаления)")

    # без изменений опрос не перерисовывает (тот же массив)
    pg.evaluate("window.__pv=profiles")
    pg.evaluate("sbBump('profiles/none')")
    pg.wait_for_timeout(400)
    r.ok(pg.evaluate("window.__pv===profiles"), "без изменений состояние не пересобирается")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

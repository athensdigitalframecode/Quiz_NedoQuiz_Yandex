"""Воронка основного режима (R-05): события qm/qmOnce попадают в счётчик дня и уходят в track_day.
Запуск: python dev/tests/t_funnel.py"""
from harness import Run, GAME, start, answer

CH = {"path": "challenges/TESTCH01", "col": "challenges", "id": "TESTCH01",
      "data": {"by": "someone-else", "invited": "", "link": True, "topic": -1, "qs": list(range(15)), "sq": {},
               "createdAt": 1, "statsDone": False, "d_someone-else": {"pts": 100, "okc": 5, "dq": False, "at": 1}}}

with Run("t_funnel") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)

    # партия 1: 2 ответа, выход через окно → sq; на итоге «вызов другу» и «ещё раз»
    start(pg); answer(pg, 2)
    pg.click("#s-game [data-leave]"); pg.wait_for_selector(".dlgbg"); pg.click("#ayYes")
    pg.wait_for_function("document.body.dataset.scr==='s-end'", timeout=10000)
    pg.wait_for_timeout(500)
    pg.evaluate("navigator.share=undefined")
    pg.click("#soloShare")
    pg.click('#endBody [data-act="new"]')
    # партия 2: выход на 0 ответах → sq
    pg.wait_for_function(f"(g=>g&&g.status==='q'&&g.qi===0)({GAME})", timeout=15000)
    pg.click("#s-game [data-leave]")
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=5000)
    # партия 3: до конца → sf
    start(pg); answer(pg, 9)
    pg.wait_for_function("typeof me==='function'&&!!me()&&game&&game.status==='q'", timeout=20000)
    pg.locator("#opts .opt:not(.gone)").first.click()
    pg.wait_for_function(f"{GAME}.status==='reveal'||{GAME}.status==='end'", timeout=10000)
    if pg.locator("#soloNext").is_visible(): pg.click("#soloNext")
    pg.wait_for_function("document.body.dataset.scr==='s-end'", timeout=20000)
    pg.wait_for_timeout(500)

    m = r.metrics(pg)
    print("   m =", m)
    r.ok(m.get("ss") == 3, f"ss: начато 3 партии ({m.get('ss')})")
    r.ok(m.get("sa1") == 2, f"sa1: первый ответ в двух партиях из трёх ({m.get('sa1')})")
    r.ok(m.get("sq") == 2, f"sq: брошено 2 — через окно и на 0 ответах ({m.get('sq')})")
    r.ok(m.get("sf") == 1, f"sf: доиграна 1 ({m.get('sf')})")
    r.ok(m.get("sag") == 1 and m.get("sch") == 1, f"sag и sch по одному ({m.get('sag')}, {m.get('sch')})")
    # повторная отрисовка итога не дублирует событие
    pg.evaluate("drawEnd0()")
    r.ok(r.metrics(pg).get("sf") == 1, "повторная отрисовка итога не считает sf ещё раз")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")

    # квиз дня → dqs
    pg.evaluate("nav('home')")
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=5000)
    pg.click('[data-act="dqstart"]')
    pg.wait_for_function(f"(g=>g&&g.dly)({GAME})", timeout=10000)
    r.ok(r.metrics(pg).get("dqs") == 1, "dqs: квиз дня начат")

    # вызов по ссылке от другого игрока → cho
    pg = r.page(sdk=False, seed=[CH], query="#d=TESTCH01")
    # вызов принят: создана партия по его вопросам
    pg.wait_for_function("[...__db.keys()].some(k=>/^games\/[^/]+$/.test(k))", timeout=30000)
    m = r.metrics(pg)
    r.ok(m.get("cho") == 1, f"cho: открыт чужой вызов по ссылке ({m}, очередь {pg.evaluate('window.QMQ')}, {pg.evaluate('[...QMO]')})")

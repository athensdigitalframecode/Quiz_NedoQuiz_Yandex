"""M01 (§8.1, §8.3, §12): qstats одной пачкой через qstat_add; жалобы — только свои, скрытые и топ — из disputes_summary.
Сами правила базы проверены SQL-сценарием в транзакции с откатом (см. dev/sql/m01_qstats_disputes.sql).
Запуск: python dev/tests/t_m01.py"""
import json
from harness import Run, GAME, start, answer_wrong

OTHERS = ["u-1", "u-2", "u-3"]

with Run("t_m01") as r:
    # чужие жалобы на один и тот же вопрос (BANK[0]) — от трёх игроков
    probe = r.page(sdk=True)
    probe.wait_for_function("typeof BANK!=='undefined'&&BANK.length>0", timeout=15000)
    h, q0 = probe.evaluate("[String(hstr(BANK[0].q)),BANK[0].q]")
    probe.context.close()
    seed = [{"path": f"disputes/{h}_{u}", "col": "disputes", "id": f"{h}_{u}", "data": {"h": h, "q": q0, "a": "x", "by": u}} for u in OTHERS]

    pg = r.page(sdk=True, seed=seed)
    pg.wait_for_function("document.body.dataset.scr==='s-home'&&!!uid", timeout=15000)
    pg.wait_for_function("!!DSUM", timeout=5000)
    r.ok(pg.evaluate("Object.keys(DISPS).length") == 0, "чужие жалобы в клиент не загружаются")
    r.ok(pg.evaluate(f"hiddenQ().has({json.dumps(h)})"), "вопрос с 3 жалобами скрыт по сводке сервера")
    r.ok(pg.evaluate("!pickQs(-1,QP_PLAN,10).includes(0)"), "скрытый вопрос не попадает в партию")
    pg.evaluate("nav('suggest')")
    pg.wait_for_timeout(300)
    t = pg.inner_text("#sgDisp")
    r.ok("оспорили: 3" in t, f"топ оспоренных — из сводки ({t[:60]!r})")

    # партия: статистика вопросов — один вызов на партию
    pg.evaluate("nav('home')")
    start(pg)
    answer_wrong(pg, 3)
    pg.click("#s-game [data-leave]")
    pg.wait_for_selector(".dlgbg", timeout=3000)
    pg.click("#ayYes")
    pg.wait_for_function(f"{GAME}.status==='end'", timeout=5000)
    pg.wait_for_function("__rpc.some(x=>x[0]==='qstat_add')", timeout=8000)
    calls = pg.evaluate("__rpc.filter(x=>x[0]==='qstat_add').map(x=>x[1].items)")
    r.ok(len(calls) == 1 and len(calls[0]) == 3 and all(not i["ok"] for i in calls[0]), f"одна пачка из 3 ответов ({calls})")
    qs = pg.evaluate("[...__db.values()].filter(x=>x.col==='qstats').map(x=>x.data.n)")
    r.ok(len(qs) == 3 and all(n == 1 for n in qs), f"qstats записаны ({qs})")

    # своя жалоба видна себе
    pg.click('[data-act="review"]')
    pg.wait_for_selector('[data-act="disp"]', timeout=5000)
    pg.locator('[data-act="disp"]').first.click()
    pg.wait_for_selector("#arYes", timeout=3000)  # окно причины (этап 8)
    pg.click("#arYes")
    pg.wait_for_function("Object.keys(DISPS).length===1", timeout=10000)
    r.ok(True, "своя жалоба загружается обратно")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

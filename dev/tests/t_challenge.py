"""R-09 вызов другу: после «Играть» кнопка создаёт вызов с теми же вопросами; друг проходит их по ссылке,
видит «из 10», сравнение и «Реванш». Подставная база в памяти — два игрока в одной базе не сводятся,
поэтому сторона друга проверяется на заранее положенном вызове. Запуск: python dev/tests/t_challenge.py"""
from harness import Run, GAME, start, answer


def finish(pg):
    """Ответить на последний вопрос и дождаться итогов."""
    pg.wait_for_function("typeof me==='function'&&!!me()&&game&&game.status==='q'", timeout=20000)
    for _ in range(10):
        pg.locator("#opts .opt:not(.gone)").first.click()
        try: pg.wait_for_function(f"{GAME}.status!=='q'", timeout=2500); break
        except Exception: pass
    if pg.locator("#soloNext").is_visible(): pg.click("#soloNext")
    pg.wait_for_function("document.body.dataset.scr==='s-end'", timeout=20000)
    pg.wait_for_timeout(800)


QS = list(range(100, 110))
CH = {"path": "challenges/FRIEND01", "col": "challenges", "id": "FRIEND01",
      "data": {"by": "friend-1", "invited": "", "link": True, "topic": -1, "qs": QS, "sq": {}, "createdAt": 4102444800000,
               "statsDone": False, "d_friend-1": {"pts": 300, "okc": 4, "dq": False, "at": 1}}}
PROF = {"path": "profiles/friend-1", "col": "profiles", "id": "friend-1", "data": {"nick": "Друг", "createdAt": 1}}

with Run("t_challenge") as r:
    # --- создатель: «Играть» → вызов
    pg = r.page(sdk=False)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    start(pg); answer(pg, 9); finish(pg)
    sb = pg.locator("#soloShare")
    r.ok(sb.is_visible() and "те же вопросы" in sb.inner_text(), f"на итогах — «Вызвать друга: те же вопросы» ({sb.inner_text()!r})")
    r.ok(pg.locator('#endExtra [data-act="linkch"]').count() == 0, "второй такой же кнопки нет")
    mine = pg.evaluate(f"{GAME}.qs")
    pg.evaluate("()=>{navigator.share=o=>{window.__shared=o.text;return Promise.resolve()}}")
    sb.click()
    pg.wait_for_function("[...__db.keys()].some(k=>/^challenges\\/[^/]+$/.test(k))", timeout=10000)
    ch = pg.evaluate("[...__db.values()].filter(x=>x.col==='challenges').pop().data")
    r.ok(ch.get("qs") == mine and len(mine) == 10 and ch.get("link") and ch.get("open"), "вызов создан: те же 10 вопросов, по ссылке, open (правило базы R-06)")
    r.ok(ch.get("d_" + pg.evaluate("uid")) is not None, "результат создателя записан в вызов")
    pg.wait_for_function("!!window.__shared", timeout=5000)
    txt = pg.evaluate("window.__shared")
    r.ok("#d=" in txt and "из 10" in txt, f"текст со ссылкой на вызов и «из 10» ({txt[:120]!r})")
    m = r.metrics(pg)
    r.ok(m.get("sch") == 1 and m.get("chc") == 1, f"счётчики sch и chc по одному ({m.get('sch')}, {m.get('chc')})")
    sb.click(); pg.wait_for_timeout(500)
    r.ok(pg.evaluate("[...__db.values()].filter(x=>x.col==='challenges').length") == 1, "повторное нажатие не создаёт второй вызов")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")

    # --- друг: открыл ссылку, прошёл те же вопросы
    pg = r.page(sdk=False, seed=[CH, PROF], query="#d=FRIEND01")
    pg.wait_for_function(f"(g=>g&&g.ch==='FRIEND01'&&g.status==='q')({GAME})", timeout=30000)
    r.ok(pg.evaluate(f"{GAME}.qs") == QS, "друг получил те же вопросы")
    pg.wait_for_function("/из/.test(document.getElementById('qno').textContent)", timeout=10000)
    r.ok("из 10" in pg.evaluate("document.getElementById('qno').textContent"), f"счётчик вопросов «из 10» ({pg.inner_text('#qno')!r})")
    answer(pg, 9); finish(pg)
    pg.wait_for_function("(c=>c&&c.statsDone)(challenges.FRIEND01)", timeout=15000)
    pg.evaluate("drawEnd()")
    body = pg.inner_text("#endBody")
    r.ok("Друг" in body and "300" in body, f"сравнение с результатом создателя ({body[:80]!r})")
    r.ok(pg.locator('#endBody [data-act="rematch"]').is_visible(), "есть кнопка «Реванш»")
    m = r.metrics(pg)
    r.ok(m.get("cho") == 1 and m.get("chf") == 1, f"счётчики cho и chf ({m.get('cho')}, {m.get('chf')})")
    pg.click('#endBody [data-act="rematch"]')
    pg.wait_for_function("Object.values(challenges).some(c=>c.invited==='friend-1')", timeout=15000)
    r.ok(True, "«Реванш» создал новый вызов тому же игроку")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

"""Вызов другу в быстрых режимах: раунд записывает порядок вопросов, друг по ссылке получает те же,
итог сравнивает верные ответы, у создателя результат виден на экране режимов.
В подставной базе у всех вкладок один uid, поэтому вызов для друга кладётся заранее от имени другого автора.
Запуск: python dev/tests/t_arcch.py"""
from harness import Run

QSEL = "document.querySelector('#arcBody .arc-q')"


def play(r, pg, n):
    """Ответить на n вопросов текущего раунда (первым вариантом) и завершить раунд."""
    texts = []
    for _ in range(n):
        pg.wait_for_function(f"!!{QSEL}", timeout=10000)
        texts.append(pg.evaluate(f"{QSEL}.textContent"))
        pg.locator("#arcBody .opt").first.click()
        pg.mouse.move(1, 1)  # иначе :hover-подъём кнопки под курсором «дрожит» и следующий клик ждёт неподвижности
        pg.wait_for_function(f"!{QSEL}||{QSEL}.textContent!=={texts[-1]!r}", timeout=10000)
    r.arc(pg, "fin")
    pg.wait_for_selector("#arcBody .arc-big", timeout=5000)
    return texts


with Run("t_arcch") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'&&typeof uid!=='undefined'&&!!uid", timeout=15000)
    r.arc(pg, "m:blitz")
    shown = play(r, pg, 4)
    btn = pg.locator('#arcBody [data-arc="chal"]')
    r.ok(btn.is_visible(), "на итогах раунда — «⚔️ Вызвать друга»")
    pg.evaluate("()=>{navigator.share=o=>{window.__shared=o.text;return Promise.resolve()}}")
    btn.click()
    pg.wait_for_function("!!window.__shared", timeout=10000)
    doc = pg.evaluate("[...__db.values()].filter(x=>x.col==='challenges').pop()")
    c = doc["data"]
    r.ok(c.get("arc") == "blitz" and c.get("open") and c.get("link"), "вызов: режим, open и link (иначе база не даст его принять)")
    r.ok(len(c.get("aq", [])) >= 4, f"записан порядок вопросов ({len(c.get('aq', []))})")
    r.ok(c.get("d_" + pg.evaluate("uid")) is not None, "результат создателя записан")
    sh = pg.evaluate("window.__shared")
    r.ok(doc["id"] in sh and "верных" in sh, f"текст со ссылкой на вызов ({sh[:110]!r})")
    btn.click(); pg.wait_for_timeout(500)
    r.ok(pg.evaluate("[...__db.values()].filter(x=>x.col==='challenges').length") == 1, "повторное нажатие не создаёт второй вызов")
    r.ok(pg.evaluate("Object.values(challenges).filter(x=>x.open&&!x.link).length") == 0, "вызов не попадает в подбор случайных соперников")
    m = r.metrics(pg)
    r.ok(m.get("chc") == 1, f"счётчик chc ({m.get('chc')})")
    # друг сыграл — итог на экране режимов
    pg.evaluate(f"(()=>{{const c=challenges[{doc['id']!r}];c.invited='friend-1';c['d_friend-1']={{ok:1}}}})()")
    r.arc(pg, "hub")
    pg.wait_for_selector(".arc-chres", timeout=5000)
    r.ok("принял вызов" in pg.inner_text(".arc-chres"), f"создатель видит результат друга ({pg.inner_text('.arc-chres')!r})")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")

    # --- друг открывает ссылку
    seed = {"path": "challenges/ARCCH001", "col": "challenges", "id": "ARCCH001",
            "data": {**c, "by": "friend-1", "createdAt": 4102444800000, "d_friend-1": {"ok": 2, "sc": 2, "at": 1}}}
    seed["data"].pop("d_" + pg.evaluate("uid"), None)
    pf = {"path": "profiles/friend-1", "col": "profiles", "id": "friend-1", "data": {"nick": "Друг", "createdAt": 1}}
    pg2 = r.page(sdk=False, seed=[seed, pf], query="#d=ARCCH001")
    pg2.wait_for_function("document.body.dataset.scr==='s-arc'", timeout=30000)
    r.ok("Вызов от" in pg2.inner_text("#arcSub"), f"раунд начат как вызов ({pg2.inner_text('#arcSub')!r})")
    got = play(r, pg2, 4)
    r.ok(got == shown, f"друг получил те же вопросы в том же порядке ({got[0][:40]!r})")
    pg2.wait_for_timeout(500)
    body = pg2.inner_text("#arcBody")
    r.ok("Верных ответов" in body and "Друг" in body and "Реванш" in body, f"сравнение и реванш ({body[:90]!r})")
    d = pg2.evaluate("(__db.get('challenges/ARCCH001')||{}).data")
    r.ok(d.get("d_" + pg2.evaluate("uid")) is not None, "результат друга записан в вызов")
    r.ok(pg2.locator('#arcBody [data-arc="chal"]').count() == 0, "из раунда по вызову новый вызов не создаётся")
    m = r.metrics(pg2)
    r.ok(m.get("cho") == 1 and m.get("chf") == 1, f"счётчики cho и chf ({m.get('cho')}, {m.get('chf')})")
    r.ok(not pg2.errors, f"нет ошибок консоли ({pg2.errors[:3]})")
    r.ok(not pg2.external and not pg.external, "нет внешних запросов")

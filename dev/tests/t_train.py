"""§4: «Работа над ошибками», избранное, фильтры разбора. Тренировка не даёт звёзд, очков рейтинга и мастерства.
Запуск: python dev/tests/t_train.py"""
from harness import Run, GAME, start

def answer_wrong(pg, n):
    """Ответить на n вопросов «Играть» заведомо неверно (вариант, отличный от правильного)."""
    for _ in range(n):
        q0 = pg.evaluate(f"{GAME}.qi")
        pg.wait_for_function("typeof me==='function'&&!!me()&&game&&game.status==='q'", timeout=20000)
        pg.evaluate("(()=>{const a=bq(game,game.qi).a;const b=[...document.querySelectorAll('#opts .opt:not(.gone)')].find(o=>!o.innerText.includes(a));b.click()})()")
        pg.wait_for_function(f"(g=>g.status==='reveal'||g.qi>{q0})({GAME})", timeout=5000)
        nx = pg.locator("#soloNext")
        if nx.is_visible(): nx.click()
        pg.wait_for_function(f"(g=>g.status==='q'&&g.qi>{q0})({GAME})", timeout=15000)

ARC = "JSON.parse(localStorage.getItem('quiz_arc')||'{}')"

with Run("t_train") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)

    # партия «Играть»: 3 ответа (первый вариант — чаще неверный), выход с сохранением результата
    start(pg)
    answer_wrong(pg, 3)
    pg.click("#s-game [data-leave]")
    pg.wait_for_selector(".dlgbg", timeout=3000)
    pg.click("#ayYes")
    pg.wait_for_function(f"{GAME}.status==='end'", timeout=5000)
    rec = pg.evaluate("Object.values(REC[code]||{})")
    bad = [x for x in rec if x["a"] != x["c"]]
    mis = pg.evaluate(f"{ARC}.mis||{{}}")
    r.ok(len(rec) == 3 and len(bad) == 3 and len(mis) == 3, f"ошибки «Играть» попали в очередь ({len(bad)} из {len(rec)}, в очереди {len(mis)})")
    r.ok(all(v["s"] == 0 and v["d"] == pg.evaluate("dayKey()") for v in mis.values()), "новая ошибка — к повтору сегодня")

    # разбор: фильтры и избранное
    pg.wait_for_selector('[data-act="review"]', timeout=5000)
    pg.click('[data-act="review"]')
    pg.wait_for_selector('[data-act="revf"]', timeout=5000)
    r.ok(pg.locator('[data-act="revf"][data-f="all"]').inner_text().strip() == "Все · 3", "фильтр «Все · 3»")
    if bad:
        pg.click('[data-act="revf"][data-f="bad"]')
        r.ok(pg.locator("#endExtra .tl .tcard").count() == len(bad), "фильтр «Ошибки» оставляет только ошибки")
        pg.click('[data-act="revf"][data-f="all"]')
    pg.locator('[data-act="fav"]').first.click()
    r.ok(len(pg.evaluate(f"{ARC}.fav||[]")) == 1, "☆ добавляет вопрос в избранное")
    r.ok(pg.locator('[data-act="fav"]').first.inner_text().strip() == "★", "звёздочка закрашена")
    pg.click('[data-act="revf"][data-f="fav"]')
    r.ok(pg.locator("#endExtra .tl .tcard").count() == 1, "фильтр «Избранное»")
    if bad:
        r.ok(pg.locator('#endExtra [data-arc="m:mis"]').count() == 1, "на итогах — кнопка «Работа над ошибками»")

    # тренировка по ошибкам: верные ответы → +3 дня; рейтинг, звёзды, мастерство не меняются
    pg.evaluate("""(()=>{const S=JSON.parse(localStorage.getItem('quiz_arc'));const ks=BANK.slice(0,4).map(x=>hstr(x.q)+':'+(x.i||''));
      S.mis={};ks.forEach(k=>S.mis[k]={s:0,d:dayKey()});S.mis[ks[3]].d='2099-01-01';localStorage.setItem('quiz_arc',JSON.stringify(S))})()""")
    before = pg.evaluate(ARC)
    r.arc(pg, "hub")
    pg.wait_for_selector('[data-arc="m:mis"]', timeout=5000)
    r.ok("К повтору сегодня: 3" in pg.inner_text('[data-arc="m:mis"]'), "в быстрых режимах: «К повтору сегодня: 3»")
    pg.click('[data-arc="m:mis"]')
    for i in range(3):
        pg.wait_for_selector("#arcBody .opt", timeout=5000)
        okI = pg.evaluate("(()=>{const q=document.querySelector('#arcBody .arc-q').innerText,x=BANK.find(b=>b.q===q);return [...document.querySelectorAll('#arcBody .opt .pt')].map(e=>e.innerText).indexOf(x.a)})()")
        if i == 2: okI = (okI + 1) % 4  # последний — ошибка
        pg.click(f'[data-arc="o:{okI}"]')
        pg.wait_for_timeout(1300)
    pg.wait_for_selector(".arc-big", timeout=5000)
    after = pg.evaluate(ARC)
    st = sorted((v["s"], v["d"]) for v in after["mis"].values())
    r.ok(pg.inner_text(".arc-big").strip() == "2 из 3", f"итог тренировки «2 из 3» ({pg.inner_text('.arc-big')})")
    plus = lambda n: pg.evaluate(f"(()=>{{const d=new Date(dayKey()+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+{n});return d.toISOString().slice(0,10)}})()")
    r.ok(st.count((1, plus(3))) == 2 and (0, plus(1)) in st and (0, "2099-01-01") in st, f"интервалы: верно → +3 дня, ошибка → завтра ({st})")
    r.ok(after["stars"] == before["stars"] and after["tot"] == before["tot"] and after["runs"] == before["runs"] and after["mast"] == before["mast"],
         "тренировка не даёт звёзд, очков, раундов и мастерства")
    r.ok("Сегодня повторять нечего" not in pg.inner_text("#arcBody") and "На сегодня всё повторено" in pg.inner_text("#arcBody"), "итог: на сегодня всё повторено")

    # усвоение: 5 верных подряд — вопрос уходит из очереди
    k = pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('quiz_arc')).mis)[0]")
    pg.evaluate("k=>{const x=[...BANK].find(b=>hstr(b.q)+':'+(b.i||'')===k);for(let i=0;i<5;i++)misNote(x,true,true)}", k)
    r.ok(k not in pg.evaluate(f"{ARC}.mis"), "после 5 верных повторов вопрос усвоен")

    # облачное сохранение со старым форматом (без fav/mis) не ломает загрузку
    pg.evaluate("localStorage.setItem('quiz_arc',JSON.stringify({v:1,stars:5,rec:{},mast:{},seen:[]}))")
    r.arc(pg, "hub")
    pg.wait_for_timeout(300)
    r.ok(pg.locator("#arcBody .arc-mode").count() > 0 and not pg.errors, "старое сохранение без новых полей открывается")
    pg.evaluate("misNote(BANK[0],false)")
    r.ok(len(pg.evaluate(f"{ARC}.mis")) == 1, "в старое сохранение ошибка записывается")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

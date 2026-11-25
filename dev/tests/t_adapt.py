"""§3.1–3.2: профиль знаний и адаптивная сложность «Играть». Соревнования (призрак, вызовы, квиз дня) — общая схема (§3.4).
Запуск: python dev/tests/t_adapt.py"""
from harness import Run, GAME, start, answer_wrong

ARC = "JSON.parse(localStorage.getItem('quiz_arc')||'{}')"
SET = "kp=>{const S=JSON.parse(localStorage.getItem('quiz_arc')||'{}');S.kp=kp;localStorage.setItem('quiz_arc',JSON.stringify(S));arcOpen()}"
MIX = "(()=>{const p=adaptPlan(),q=pickQs(-1,p,10).map(i=>typeof i==='number'?BANK[i].d||'m':'s');return {lv:JSON.parse(localStorage.getItem('quiz_arc')).kp.lv,e:q.filter(d=>d==='e').length,m:q.filter(d=>d==='m').length,h:q.filter(d=>d==='h').length}})()"

with Run("t_adapt") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)

    a = pg.evaluate(MIX)
    r.ok(a["lv"] == 0 and a["h"] <= 2 and a["e"] >= 3, f"новичок: обычная схема, сложных ≤2 ({a})")

    pg.evaluate(SET, {"e": "1" * 10, "m": "1" * 20, "h": "1" * 10, "t": {}, "lv": 0})
    a = pg.evaluate(MIX)
    r.ok(a["lv"] == 1 and a["h"] >= 3 and a["e"] <= 3, f"сильный игрок: посложнее, сложных больше ({a})")
    first_e = pg.evaluate("(()=>{const q=pickQs(-1,adaptPlan(),10);return BANK[q[0]].d||'m'})()")
    r.ok(first_e == "e", "внутри партии по-прежнему от простого к сложному (первый вопрос лёгкий)")

    pg.evaluate(SET, {"e": "0" * 20, "m": "0" * 20, "h": "", "t": {}, "lv": 1})
    a1 = pg.evaluate(MIX)
    a2 = pg.evaluate(MIX)
    r.ok(a1["lv"] == 0 and a2["lv"] == -1, f"без скачков: +1 → 0 → −1 за две партии ({a1['lv']}, {a2['lv']})")
    r.ok(a2["h"] <= 2 and a2["e"] >= 5, f"после серии ошибок — полегче ({a2})")

    pg.evaluate(SET, {"e": "0" * 5, "m": "0" * 5, "h": "", "t": {}, "lv": 0})
    r.ok(pg.evaluate(MIX)["lv"] == 0, "по 10 ответам выводов не делаем (порог 15)")

    pg.evaluate("localStorage.setItem('quiz_arc',JSON.stringify({v:1,kp:{e:'x1y',m:5,t:{3:'bad'},lv:9}}));arcOpen();adaptPlan();0")
    k = pg.evaluate(f"{ARC}.kp")
    r.ok(k["e"] == "1" and k["m"] == "" and k["lv"] == 0 and k["t"] == {}, f"испорченный профиль чинится при загрузке, уровень без скачка ({k})")

    # партия «Играть»: ответы пишутся в профиль; адаптация вызывается только для обычной партии
    pg.evaluate(SET, {"e": "", "m": "", "h": "", "t": {}, "lv": 0})
    pg.evaluate("window.__ad=0;const o=window.adaptPlan;window.adaptPlan=()=>{__ad++;return o()};0")  # ;0 — иначе Playwright вызовет функцию-результат
    pg.evaluate("makeGame('solo',[],{gh:{u:'x',pts:100,okc:5,self:false}})")
    pg.evaluate("makeGame('solo',[],{qs:[1,2,3],dly:'2026-11-25',topic:-1})")
    r.ok(pg.evaluate("__ad") == 0, "призрак и квиз дня — без адаптации (одинаковые условия)")
    pg.evaluate("arcOpen();nav('home')")
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=5000)
    start(pg)
    r.ok(pg.evaluate("__ad") == 1, "обычная «Играть» — с адаптацией")
    answer_wrong(pg, 3)
    k = pg.evaluate(f"{ARC}.kp")
    n = len(k["e"]) + len(k["m"]) + len(k["h"])
    r.ok(n == 3 and "1" not in k["e"] + k["m"] + k["h"] and sum(v[0] for v in k["t"].values()) == 3, f"3 ответа партии записаны в профиль ({k})")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

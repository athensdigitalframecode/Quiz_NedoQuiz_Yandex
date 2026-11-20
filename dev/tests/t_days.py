"""R-10: одна серия дней. Любая игра засчитывает день в обе серии, на главной видна общая.
Запуск: python dev/tests/t_days.py"""
from harness import Run

with Run("t_days") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_timeout(1500)
    r.ok(pg.inner_text("#streak").strip() != "", "серия дней на главной снова рисуется")
    r.ok("начать серию" in pg.inner_text("#streak"), "до первой игры — приглашение начать серию")

    # день из быстрых режимов → общая серия и серия основного режима
    pg.evaluate("arcDayPlayed()")
    pg.evaluate("mainDayPlayed()")
    pg.wait_for_function("[...__db.keys()].some(k=>k.startsWith('ach/'))", timeout=5000)
    d = pg.evaluate("dayStreak()")
    r.ok(d["n"] == 1 and d["today"], f"после игры серия 1 день и засчитан сегодня ({d})")
    lastday = pg.evaluate("(()=>{const k=[...__db.keys()].find(k=>k.startsWith('ach/'));return __db.get(k).data.lastDay})()")
    r.ok(lastday == pg.evaluate("dayKey()"), "день засчитан и в серии основного режима (ach.lastDay)")
    pg.evaluate("drawDays()")
    r.ok("1 день" in pg.inner_text("#streak"), f"главная: «1 день подряд» ({pg.inner_text('#streak')[:80]})")
    r.arc(pg, "hub")
    pg.wait_for_timeout(300)
    r.ok("1 день подряд" in pg.inner_text("#arcBody"), "быстрые режимы показывают ту же серию")

    # награда серии сохраняется: 6 дней вчера → сегодня 7-й день, +50⭐
    pg.evaluate("""(()=>{const S=JSON.parse(localStorage.getItem('quiz_arc'));const y=prevDay(dayKey());
      S.sk={n:6,l:y,b:6,g:{3:1}};S.stars=0;localStorage.setItem('quiz_arc',JSON.stringify(S))})()""")
    r.arc(pg, "shop")  # перечитывает сохранение
    pg.evaluate("arcDayPlayed()")
    st = pg.evaluate("JSON.parse(localStorage.getItem('quiz_arc'))")
    r.ok(st["sk"]["n"] == 7 and st["stars"] == 50, f"7-й день серии: +50⭐ ({st['sk']}, {st['stars']})")
    r.ok(pg.evaluate("dayStreak().n") == 7, "общая серия — большая из двух")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

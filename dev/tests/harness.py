"""Общая обвязка автотестов: локальный сервер, Chrome через Playwright, подмена SDK и базы.
Ни один запрос не уходит наружу: *.supabase.co и всё не-localhost обрывается и записывается.
Chrome: переменная CHROME или стандартный путь. Подставной SDK ≠ проверка на платформе."""
import functools, http.server, json, os, pathlib, sys, threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
T = ROOT / "dev" / "tests"
CHROME = os.environ.get("CHROME") or next((p for p in [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"] if os.path.exists(p)), None)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def end_headers(self): self.send_header("Cache-Control", "no-store"); super().end_headers()

def serve():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"

# --- партия «Играть» на подставной базе ---
GAME = "(()=>{const g=[...__db.values()].filter(r=>r.col==='games').pop();return g?g.data:null})()"

def start(pg):
    pg.click('[data-act="new"][data-mode="solo"]')
    pg.wait_for_function(f"(g=>g&&g.status==='q')({GAME})", timeout=30000)

def answer(pg, n):
    """Ответить на n вопросов. Клик до загрузки своего игрока игра игнорирует — ждём и повторяем."""
    for i in range(n):
        q0 = pg.evaluate(f"{GAME}.qi")
        for _ in range(10):
            pg.wait_for_function("typeof me==='function'&&!!me()&&game&&game.status==='q'", timeout=20000)
            pg.locator("#opts .opt:not(.gone)").first.click()
            try:
                pg.wait_for_function(f"(g=>g.status==='reveal'||g.qi>{q0})({GAME})", timeout=3000); break
            except Exception: pass
        else: raise AssertionError(f"ответ на вопрос {q0} не принят")
        nx = pg.locator("#soloNext")
        if nx.is_visible(): nx.click()
        pg.wait_for_function(f"(g=>g.status==='q'&&g.qi>{q0})({GAME})", timeout=15000)

class Run:
    """with Run("имя") as r: page = r.page(sdk=True, db="fake"); r.ok(условие, "что проверяем")"""
    def __init__(self, name): self.name, self.fails, self.n = name, 0, 0
    def __enter__(self):
        self.base = serve(); self.pw = sync_playwright().start()
        self.br = self.pw.chromium.launch(executable_path=CHROME, headless=os.environ.get("HEADED") != "1")
        return self
    def __exit__(self, et, e, tb):
        self.br.close(); self.pw.stop()
        if et:
            import traceback; self.last_err = str(e)
            fr = [f for f in traceback.extract_tb(tb) if f.filename.endswith(".py") and "site-packages" not in f.filename]
            where = f" (строка {fr[-1].lineno}: {fr[-1].line})" if fr else ""
            print(f"FAIL {self.name}: исключение{where} {str(e)[:300]}"); self.fails += 1; self.n += 1
        print(f"== {self.name}: {self.n - self.fails} OK, {self.fails} FAIL")
        sys.exit(1 if self.fails else 0)
    def ok(self, cond, what):
        self.n += 1
        if not cond: self.fails += 1
        print(("OK   " if cond else "FAIL ") + what)
    def page(self, sdk=True, db="fake", query="", viewport=(412, 732), failsave=False, skip_onb=True, seed=None):
        """sdk: подставной SDK Яндекса или 404; db: "fake" (база в памяти) или "down" (supabase.js не грузится)."""
        ctx = self.br.new_context(viewport={"width": viewport[0], "height": viewport[1]}, service_workers="block")
        pg = ctx.new_page()
        pg.errors, pg.external, pg.track = [], [], []
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        # «Failed to load resource» — следствие наших же обрывов запросов, не ошибка игры
        pg.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and pg.errors.append(m.text))
        def route(rt):
            u = rt.request.url
            if "/rpc/track_day" in u:  # счётчики дня: запоминаем, наружу не отправляем
                try: pg.track.append(rt.request.post_data_json)
                except Exception: pass
                return rt.abort()
            if not u.startswith(self.base):
                # API Supabase разрешён игре (обрываем, чтобы не писать в рабочую базу); антивирус встраивает свои скрипты
                if ".supabase.co/" not in u and "kaspersky-labs.com" not in u: pg.external.append(u)
                return rt.abort()
            path = u[len(self.base):].split("?")[0]
            if path == "/sdk.js":
                return rt.fulfill(path=str(T / "mock_sdk.js")) if sdk else rt.fulfill(status=404, body="")
            if path == "/supabase.js":
                return rt.fulfill(path=str(T / "fake_supabase.js")) if db == "fake" else rt.abort()
            return rt.continue_()
        pg.route("**/*", route)
        # окно подтверждения браузера не должно появляться: считаем вызовы
        if skip_onb:  # обучение для новичка закрывает экран; его проверяет отдельный сценарий
            pg.add_init_script("try{localStorage.setItem('quiz_onb','1');localStorage.setItem('yg_quiz_onb','1')}catch(e){}")
        pg.add_init_script("window.__confirms=0;window.confirm=()=>{window.__confirms++;return true};window.alert=()=>{window.__confirms++}")
        if seed: pg.add_init_script(f"window.__seed={json.dumps(seed)}")
        pg.goto(self.base + "/index.html" + ("?failsave=1" if failsave else query))
        return pg
    @staticmethod
    def arc(pg, action):
        """Нажать «виртуальную» кнопку модуля быстрых режимов (data-arc)."""
        pg.evaluate("a=>{const b=document.createElement('button');b.dataset.arc=a;document.body.appendChild(b);b.click();b.remove()}", action)
    @staticmethod
    def metrics(pg):
        """Отправить счётчики дня (как при сворачивании вкладки) и вернуть последний снимок m."""
        pg.wait_for_function("!!window.QMET", timeout=30000)  # модуль счётчиков в конце файла может ещё грузиться
        n = len(pg.track)
        pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'));delete document.hidden")
        for _ in range(30):  # ждём именно этот снимок, а не предыдущий
            if len(pg.track) > n: break
            pg.wait_for_timeout(100)
        return (pg.track[-1] or {}).get("m", {}) if len(pg.track) > n else {}
    @staticmethod
    def calls(pg):
        return pg.evaluate("(window.__yg&&__yg.calls||[]).map(x=>x.join(' '))")

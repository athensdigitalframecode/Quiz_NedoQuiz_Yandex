# Квиз или Недоквиз — версия для Яндекс Игр / GamePush

Русскоязычная браузерная викторина без ведущего. Один файл `index.html` (HTML+CSS+JS без сборщика), Supabase как сервер, SDK Яндекс Игр или GamePush как платформа.

## Состав пакета
| Путь | Что |
| --- | --- |
| `index.html` | вся игра (не открывать целиком в редакторе Claude — см. `CLAUDE.md`) |
| `supabase.js`, `fonts/` | локальные зависимости |
| `gp-adapter.js`, `gp-config.js` | адаптер GamePush (по умолчанию выключен — пустой `gp-config.js`) |
| `<хеш>.jpg/png/svg`, `icon-*.png`, `apple-touch-icon.png` | картинки вопросов и иконки |
| `sw.js`, `manifest.json`, `version.json` | PWA и версия сборки |
| `dev/` | `stamp.py`, `build_zip.py`, `serve.py`, `audit_bank.py`, `sql/` (миграции и отчёты), `tests/` (Playwright) |
| `docs/` | исходная документация репозитория; `docs/archive/` — прежний `CLAUDE.md` |
| `CLAUDE.md`, `PROJECT.md`, `DECISIONS.md`, `ROADMAP.md` | документы для Claude Code |

## Установка
Рекомендуемый путь — работать в git-клоне, чтобы сохранить историю и пушить:
```bash
git clone https://github.com/athensdigitalframecode/Quiz_NedoQuiz_Yandex.git
cd Quiz_NedoQuiz_Yandex
# скопировать поверх из архива: CLAUDE.md, PROJECT.md, DECISIONS.md, ROADMAP.md, README.md, docs/archive/
git status   # убедиться, что изменились только эти файлы
```
Код в архиве совпадает с `main` на 27.11.2026 (коммит `3597a76`). Если на GitHub появились новые коммиты — правда у GitHub, архивный код не накатывать поверх.

Без git: распаковать архив и выполнить `git init` (история и remote тогда не будут связаны с GitHub).

## Запуск
Нужен Python 3.
```bash
python dev/serve.py 8792 --mock   # http://localhost:8792 — подставной SDK Яндекса
python dev/serve.py 8792          # как обычный браузер, без SDK
```
⚠️ Даже с `--mock` игра обращается к **рабочей** базе Supabase `cxblrsfnvqqblncvsjhn`. Не играть партии основного режима без нужды.

## Тесты
```bash
pip install playwright            # браузер не скачивать
export CHROME=/путь/к/chrome      # системный Chrome/Chromium
python dev/tests/run_all.py       # все t_*.py; код выхода 1 при FAIL
```
Тесты используют подставные SDK и базу в памяти, наружу запросы не уходят.

## Сборка
```bash
python dev/stamp.py .             # после любой правки index.html / supabase.js / fonts / gp-*.js
python dev/build_zip.py           # dist/ — архив для Яндекс Игр
python dev/build_zip.py --gp      # dist/quiz-gamepush-<версия>.zip; нужен gp-config.local.js (не в git)
```

## Полнота пакета — что недоступно
Пакет собран из: репозитория `Quiz_NedoQuiz_Yandex` (код и `docs/`), заметок проекта из переписки в claude.ai и документов Project Knowledge. **Недоступно в этой сессии:**
- Полные тексты прошлых чатов — только сжатые заметки. Нюансы, которые в заметки не попали, восстановить нельзя.
- Репозиторий основного сайта `Quiz_NedoQuiz` — доступ из этой сессии не дали. Поэтому в пакет не вошли изменения основного сайта после 05.11: комната «Вечер кино» и кнопка для книжного клуба Полины, плавающий значок лучшего игрока (коммит `e5820ad`), удаление кнопки «Пожертвование» (24.11), Telegram-уведомления, а также файлы дизайна `variant1/`, `variant2/`, `themes/`.
- Документы claude.ai по ссылкам не открывались: стратегия (`Bgo1mbZJriJMPLGKfcLhkA`), аудит 06.11 (`GE748TAeypZB7gwbTbTD2f`), портфолио (`Jcj3Q3bKEQKTxsdZAV9Rou`), «анализ и план монетизации». В `docs/` есть их выжимки.
- Архивы картинок `met_out`, `flags_out`, `museums_out`, `assets_out` и скрипты `fetch_met.py`/`fetch_flags.py` — на ПК владельца, в репозитории их нет.
- Банки вопросов из Project Knowledge (`logic-questions.json`, `extra-questions.json`, `linguistics-questions.json`, `README-questions.md`) не копировались: выборочная проверка показала, что они уже в `BANK`.

Лицензия — `LICENSE.txt` (все права защищены); шрифты — OFL (`fonts/OFL-*.txt`).

-- Воронка основного режима по дням. База: Supabase cxblrsfnvqqblncvsjhn, таблица day_stats(vid, day, m jsonb).
-- Пишет index.html: qm(ключ) / qmOnce(ключ, id_партии) → met() → RPC track_day (раз в 20 с и при скрытии вкладки).
-- Ключи «Играть» (Сам с собой без призрака, квиза дня и вызова):
--   ss  начата партия          sa1 первый ответ в партии
--   sf  доиграна до конца      sq  брошена (выход посреди, в т.ч. на 0 ответах)
--   sag «Сыграть ещё раз»      sch «Бросить вызов другу»
-- Квиз дня: dqs начат, dqf закончен. Вызов по ссылке: chc создан, cho открыт другим игроком.
-- Призрак: gh начата дуэль, ghf закончена.
-- Ключи быстрых режимов (уже были): ses сессии, rnd раунды, sec секунды, sk серия, ai/ar/ark реклама, bt/bo покупки.
-- Каждое значение — сумма за день у одного посетителя (vid). Доли считаются от числа событий, не от игроков.
with d as (
  select day, vid, m from day_stats where day >= to_char(current_date - 28, 'YYYY-MM-DD')
)
select day,
  count(distinct vid)                                         as visitors,
  sum(coalesce((m->>'ss')::int,0))                            as solo_started,
  sum(coalesce((m->>'sa1')::int,0))                           as solo_first_answer,
  sum(coalesce((m->>'sf')::int,0))                            as solo_finished,
  sum(coalesce((m->>'sq')::int,0))                            as solo_quit,
  round(100.0*sum(coalesce((m->>'sf')::int,0)) / nullif(sum(coalesce((m->>'ss')::int,0)),0), 1) as solo_finish_pct,
  sum(coalesce((m->>'sag')::int,0))                           as solo_again,
  sum(coalesce((m->>'sch')::int,0))                           as solo_challenge,
  sum(coalesce((m->>'dqs')::int,0))                           as daily_started,
  sum(coalesce((m->>'dqf')::int,0))                           as daily_finished,
  round(100.0*sum(coalesce((m->>'dqf')::int,0)) / nullif(sum(coalesce((m->>'dqs')::int,0)),0), 1) as daily_finish_pct,
  sum(coalesce((m->>'chc')::int,0))                           as link_ch_created,
  sum(coalesce((m->>'cho')::int,0))                           as link_ch_opened,
  sum(coalesce((m->>'gh')::int,0))                            as ghost_started,
  sum(coalesce((m->>'ghf')::int,0))                           as ghost_finished
from d group by day order by day desc;

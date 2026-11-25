-- M02 (§12.1): место игрока в рейтинге режимов считает сервер.
-- Было: профиль (свой и чужой) скачивал stats/<режим>/players целиком по каждому режиму, чтобы посчитать «N место».
-- Расчёт как в клиенте (myPlaces): 1 + число игроков того же возрастного разряда (profiles.age, пусто — взрослые)
-- с рейтингом выше; рейтинг без значения — 1000 (R0). Возвращает {режим: место} только для режимов, где у игрока есть запись.
-- Совместимо: старый клиент функцию не вызывает. Применять к проекту cxblrsfnvqqblncvsjhn.

create or replace function public.player_places(u text) returns jsonb
language sql stable security definer set search_path to 'public' as $$
  with g as (select coalesce((select data->>'age' from docs where path = 'profiles/'||u), '') ag),
  me as (
    select split_part(col, '/', 2) m,
           case when data->>'r' ~ '^-?[0-9]+(\.[0-9]+)?$' then (data->>'r')::numeric else 1000 end r
    from docs where col like 'stats/%/players' and id = u)
  select coalesce(jsonb_object_agg(me.m, 1 + (
      select count(*) from docs d
      left join docs p on p.path = 'profiles/'||d.id
      where d.col = 'stats/'||me.m||'/players'
        and coalesce(p.data->>'age', '') = (select ag from g)
        and (case when d.data->>'r' ~ '^-?[0-9]+(\.[0-9]+)?$' then (d.data->>'r')::numeric else 1000 end) > me.r)),
    '{}'::jsonb)
  from me
$$;
revoke all on function public.player_places(text) from public, anon;
grant execute on function public.player_places(text) to authenticated;

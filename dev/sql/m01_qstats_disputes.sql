-- M01 (§8.1, §8.3, §12): статистика вопросов одной пачкой, жалобы не видны чужим, очистка старых вызовов.
-- Совместимо со старым клиентом: он продолжит писать qstats напрямую; чужие жалобы просто перестанет видеть.
-- Применять целиком к проекту cxblrsfnvqqblncvsjhn.

-- 1. qstats: атомарный +1 за партию одним вызовом (было: чтение + запись на каждый вопрос, счёт терялся при одновременных партиях)
create or replace function public.qstat_add(items jsonb) returns integer
language plpgsql security definer set search_path to 'public' as $$
declare it jsonb; h text; ok int; n int := 0;
  wk int := floor((extract(epoch from now())/86400 + 3)/7);  -- как weekId() в клиенте
begin
  if auth.uid() is null then raise exception 'qstat_add: auth' using errcode = '42501'; end if;
  if jsonb_typeof(items) is distinct from 'array' or jsonb_array_length(items) > 30 then
    raise exception 'qstat_add: bad items' using errcode = '22023'; end if;
  for it in select * from jsonb_array_elements(items) loop
    h := it->>'h';
    if h is null or h !~ '^[0-9]{1,10}$' then continue; end if;
    ok := case when it->>'ok' = 'true' then 1 else 0 end;
    insert into docs(path, col, id, data, updated_at)
    values ('qstats/'||h, 'qstats', h, jsonb_build_object('n',1,'ok',ok,'wk',wk,'wn',1,'wok',ok), now())
    on conflict (path) do update set data = jsonb_build_object(
      'n',   coalesce((docs.data->>'n')::numeric, 0)::int + 1,
      'ok',  coalesce((docs.data->>'ok')::numeric, 0)::int + ok,
      'wk',  wk,
      'wn',  case when (docs.data->>'wk') = wk::text then coalesce((docs.data->>'wn')::numeric, 0)::int else 0 end + 1,
      'wok', case when (docs.data->>'wk') = wk::text then coalesce((docs.data->>'wok')::numeric, 0)::int else 0 end + ok),
      updated_at = now();
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.qstat_add(jsonb) from public, anon;
grant execute on function public.qstat_add(jsonb) to authenticated;

-- 2. Сводка жалоб без идентификаторов игроков: скрытые вопросы (≥3 разных игрока, как FLAG_N в клиенте) и топ-10 оспоренных
create or replace function public.disputes_summary() returns jsonb
language sql stable security definer set search_path to 'public' as $$
  with g as (
    select data->>'h' h, min(data->>'q') q, min(data->>'a') a, count(distinct data->>'by') n
    from docs where col = 'disputes' and data->>'h' is not null group by data->>'h')
  select jsonb_build_object(
    'hid', coalesce((select jsonb_agg(h) from g where n >= 3), '[]'::jsonb),
    'top', coalesce((select jsonb_agg(jsonb_build_object('h',h,'q',q,'a',a,'n',n) order by n desc)
                     from (select * from g order by n desc limit 10) t), '[]'::jsonb))
$$;
revoke all on function public.disputes_summary() from public, anon;
grant execute on function public.disputes_summary() to authenticated;

-- 3. Чтение: свои жалобы — да, чужие — нет (остальные коллекции как раньше)
drop policy if exists docs_read on public.docs;
create policy docs_read on public.docs for select to authenticated
  using (col <> 'disputes' or right(id, 37) = '_'||auth.uid()::text);

-- 4. Ночная очистка: вызовы старше 30 дней (клиент показывает только 7). Пользовательские данные кроме вызовов не трогаются.
create extension if not exists pg_cron;
select cron.unschedule(jobid) from cron.job where jobname = 'nq_cleanup_challenges';
select cron.schedule('nq_cleanup_challenges', '17 3 * * *',
  $$delete from public.docs where col = 'challenges' and updated_at < now() - interval '30 days'$$);

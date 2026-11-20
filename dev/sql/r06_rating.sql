-- R-06: рейтинг начисляется только через stat_bump и только участникам реальной партии или вызова.
-- Применено к проекту cxblrsfnvqqblncvsjhn 2026-11-20. Резервная копия: public.docs_backup_20261120.

-- журнал начислений: одна запись на (партия/вызов, документ рейтинга)
create table if not exists public.stat_log(
  src text not null, path text not null, by uuid, at timestamptz not null default now(),
  primary key(src, path));
alter table public.stat_log enable row level security;

-- участник партии games/<код>: есть свой документ игрока или это создатель (ТВ-экран ведёт партию, не играя)
create or replace function public.game_member(g text, u text) returns boolean
language sql stable security definer set search_path to 'public' as $$
  select u is not null and (
    exists(select 1 from docs where path = g||'/players/'||u)
    or exists(select 1 from docs where path = g and data->>'by' = u))
$$;

-- участник вызова challenges/<id>: автор, приглашённый или член одной из команд (ms = {команда: [uid…]})
create or replace function public.ch_member(c text, u text) returns boolean
language sql stable security definer set search_path to 'public' as $$
  select u is not null and exists(select 1 from docs d where d.path = c and (
    d.data->>'by' = u or d.data->>'invited' = u
    or exists(select 1 from jsonb_each(case when jsonb_typeof(d.data->'ms')='object' then d.data->'ms' else '{}'::jsonb end) e
              where jsonb_typeof(e.value)='array' and e.value ? u)))
$$;

create or replace function public.stat_bump(src text, p text, delta integer, win boolean, score integer)
returns boolean language plpgsql security definer set search_path to 'public' as $$
declare me text := auth.uid()::text; a text[] := string_to_array(p,'/'); s text[] := string_to_array(src,'/');
        g jsonb; o jsonb; ok boolean;
begin
  if me is null then raise exception 'stat_bump: no user' using errcode='42501'; end if;
  if cardinality(a)<>4 or a[1]<>'stats' or a[2] not in ('solo','pvp','evening','blitz','duel','mass')
     or a[3] not in ('players','teams') or a[4]='' then raise exception 'stat_bump: bad path' using errcode='42501'; end if;
  if cardinality(s)<>2 or s[1] not in ('games','challenges') then raise exception 'stat_bump: bad source' using errcode='42501'; end if;
  if abs(delta)>60 or score<0 or score>1000000 then raise exception 'stat_bump: out of range' using errcode='42501'; end if;
  select data into g from docs where path = src;
  if g is null then raise exception 'stat_bump: no source' using errcode='42501'; end if;
  if s[1]='games' then
    if g->>'status' is distinct from 'end' then raise exception 'stat_bump: game not ended' using errcode='42501'; end if;
    if not game_member(src, me) then raise exception 'stat_bump: caller not in game' using errcode='42501'; end if;
    ok := case when a[3]='players' then exists(select 1 from docs where path = src||'/players/'||a[4])
               else exists(select 1 from docs where col = src||'/players' and data->>'team' = a[4]) end;
  else
    if not ch_member(src, me) then raise exception 'stat_bump: caller not in challenge' using errcode='42501'; end if;
    -- результат d_<uid> пишет только сам игрок (триггер), так что начислить можно только тому, кто сыграл
    ok := case when a[3]='players' then ch_member(src, a[4]) and g ? ('d_'||a[4])
               else coalesce(g->'teams' ? a[4], false) and exists(select 1 from jsonb_array_elements_text(
                      case when jsonb_typeof(g->'ms'->a[4])='array' then g->'ms'->a[4] else '[]'::jsonb end) m where g ? ('d_'||m)) end;
  end if;
  if not ok then raise exception 'stat_bump: target not in source' using errcode='42501'; end if;
  insert into stat_log(src, path, by) values (src, p, auth.uid()) on conflict do nothing;
  if not found then return false; end if;  -- уже начислено
  select data into o from docs where path = p;
  insert into docs(path, col, id, data, updated_at)
  values (p, a[1]||'/'||a[2]||'/'||a[3], a[4], jsonb_build_object(
      'g', coalesce((o->>'g')::numeric,0)+1,
      'w', coalesce((o->>'w')::numeric,0)+case when win then 1 else 0 end,
      'r', greatest(0, coalesce((o->>'r')::numeric,1000)+delta),
      'pts', coalesce((o->>'pts')::numeric,0)+score,
      'best', greatest(coalesce((o->>'best')::numeric,0), score),
      'last', floor(extract(epoch from now())*1000)), now())
  on conflict (path) do update set data = excluded.data, updated_at = now();
  return true;
end $$;
revoke all on function public.stat_bump(text,text,integer,boolean,integer) from public, anon;
grant execute on function public.stat_bump(text,text,integer,boolean,integer) to authenticated;
revoke all on function public.game_member(text,text) from public, anon;
revoke all on function public.ch_member(text,text) from public, anon;
grant execute on function public.game_member(text,text), public.ch_member(text,text) to authenticated;

-- ===== ЧАСТЬ 2: применять только после выкладки клиента, который вызывает stat_bump =====
-- новая строка: stats из браузера — только свой «призрак» и общий набор квиза дня; игрок партии — только сам; вызов создаёт только автор
create or replace function public.docs_chk(p text, d jsonb, ins boolean) returns boolean
language sql stable set search_path to 'public' as $$
  select case split_part(p,'/',1)
    when 'profiles' then cardinality(string_to_array(p,'/'))=2 and split_part(p,'/',2)=auth.uid()::text
    when 'ach'      then cardinality(string_to_array(p,'/'))=2 and split_part(p,'/',2)=auth.uid()::text
    when 'seen'     then cardinality(string_to_array(p,'/'))=2 and split_part(p,'/',2)=auth.uid()::text
    when 'dailyans' then cardinality(string_to_array(p,'/'))=2 and right(split_part(p,'/',2),37)='_'||auth.uid()::text and d->>'u'=auth.uid()::text
    when 'disputes' then cardinality(string_to_array(p,'/'))=2 and right(split_part(p,'/',2),37)='_'||auth.uid()::text and d->>'by'=auth.uid()::text
    when 'suggest'  then cardinality(string_to_array(p,'/'))=2 and (not ins or d->>'by'=auth.uid()::text)
    when 'teams'    then cardinality(string_to_array(p,'/'))=2 and (not ins or d->>'owner'=auth.uid()::text)
    when 'qstats'   then cardinality(string_to_array(p,'/'))=2
    when 'challenges' then cardinality(string_to_array(p,'/'))=2 and (not ins or d->>'by'=auth.uid()::text)
    when 'games' then case cardinality(string_to_array(p,'/'))
        when 2 then (not ins or d->>'by'=auth.uid()::text)
        when 4 then case when split_part(p,'/',3)='players' then (not ins or split_part(p,'/',4)=auth.uid()::text)
                         else game_member('games/'||split_part(p,'/',2), auth.uid()::text) end
        else false end
    when 'history'  then true
    when 'stats'    then cardinality(string_to_array(p,'/'))=4 and (
        (split_part(p,'/',2)='ghost' and split_part(p,'/',4)=auth.uid()::text) or split_part(p,'/',2)='dailyset')
    else false end
$$;

-- старая строка (изменение и удаление)
create or replace function public.docs_old(p text, d jsonb, del boolean) returns boolean
language sql stable set search_path to 'public' as $$
  select case split_part(p,'/',1)
    when 'profiles' then split_part(p,'/',2)=auth.uid()::text
    when 'ach'      then split_part(p,'/',2)=auth.uid()::text
    when 'seen'     then split_part(p,'/',2)=auth.uid()::text
    when 'dailyans' then right(split_part(p,'/',2),37)='_'||auth.uid()::text
    when 'disputes' then right(split_part(p,'/',2),37)='_'||auth.uid()::text
    when 'suggest'  then (not del) or d->>'by'=auth.uid()::text
    when 'teams'    then d->>'captain'=auth.uid()::text or d->>'owner'=auth.uid()::text or coalesce(d->>'captain','')=''
    when 'qstats'   then not del
    when 'challenges' then d->>'by'=auth.uid()::text or (not del and (
        d->>'invited'=auth.uid()::text
        or (coalesce(d->>'invited','')='' and coalesce(d->>'open','')='true')
        or ch_member(p, auth.uid()::text)))
    when 'games' then case when cardinality(string_to_array(p,'/'))=2
        then d->>'by'=auth.uid()::text or (not del and game_member(p, auth.uid()::text))
        else split_part(p,'/',4)=auth.uid()::text or game_member('games/'||split_part(p,'/',2), auth.uid()::text) end
    when 'history'  then not del
    when 'stats'    then case when del
        then split_part(p,'/',4)=auth.uid()::text
             or (split_part(p,'/',3)='teams' and not exists(select 1 from docs t where t.path='teams/'||split_part(p,'/',4)
                   and coalesce(t.data->>'captain','')<>auth.uid()::text and coalesce(t.data->>'owner','')<>auth.uid()::text))
        else (split_part(p,'/',2)='ghost' and split_part(p,'/',4)=auth.uid()::text) or split_part(p,'/',2)='dailyset' end
    else false end
$$;

-- триггер: прежние пределы для stats + автор партии/вызова не меняется + в вызове свои d_/g_ только за себя
create or replace function public.docs_guard() returns trigger
language plpgsql set search_path to 'public' as $$
declare o jsonb; ou timestamptz; me text := auth.uid()::text; k text;
begin
  if auth.role() is distinct from 'authenticated' then return new; end if;
  new.updated_at := now();
  if split_part(new.path,'/',1)='stats' and split_part(new.path,'/',2) not in ('ghost','dailyset') then
    if tg_op='UPDATE' then o:=old.data; ou:=old.updated_at;
    else select data, updated_at into o, ou from public.docs where path=new.path; end if;
    if o is not null then
      if coalesce((new.data->>'g')::numeric,0) <> coalesce((o->>'g')::numeric,0)+1
         or abs(coalesce((new.data->>'r')::numeric,1000)-coalesce((o->>'r')::numeric,1000))>60
         or coalesce((new.data->>'w')::numeric,0)-coalesce((o->>'w')::numeric,0) not in (0,1)
         or now()-ou < interval '2 seconds'
      then raise exception 'stats update out of range' using errcode='42501'; end if;
    else
      if coalesce((new.data->>'g')::numeric,0)>1 or coalesce((new.data->>'r')::numeric,1000) not between 900 and 1100
      then raise exception 'stats insert out of range' using errcode='42501'; end if;
    end if;
  end if;
  if tg_op='UPDATE' and new.path ~ '^(games|challenges)/[^/]+$'
     and (new.data->>'by') is distinct from (old.data->>'by') then
    raise exception 'owner change' using errcode='42501';
  end if;
  if tg_op='UPDATE' and new.path ~ '^challenges/[^/]+$' then
    for k in select n.key from jsonb_each(new.data) n where n.value is distinct from old.data->n.key loop
      if (k ~ '^[dg]_' and k not in ('d_'||me, 'g_'||me)) or k in ('ms','teams','qs','sq')
         or (k='invited' and not (coalesce(old.data->>'invited','')='' and new.data->>'invited'=me)) then
        raise exception 'challenge field % not allowed', k using errcode='42501';
      end if;
    end loop;
  end if;
  return new;
end $$;

/* Подставной supabase-js для тестов: таблица docs в памяти (window.__db), анонимный вход,
   rpc doc_merge / acquire_lock / stat_bump, остальные rpc → null. Реалтайма нет — игра опрашивает базу сама.
   Покрывает только то, что вызывает index.html (sbDoc/sbCol/sbWatch, init). */
(function(){
  const DB=window.__db=new Map(),RPC=window.__rpc=[],SEL=window.__sel=[];// __sel: [коллекция, строк отдано] на каждый select
  const UID="00000000-0000-4000-8000-000000000001";
  let ses=null;
  const val=(r,c)=>{const m=/^data->>(.+)$/.exec(c);if(m)return r.data&&r.data[m[1]]!=null?String(r.data[m[1]]):null;return r[c]};
  const clone=x=>x===undefined?x:JSON.parse(JSON.stringify(x));
  function q(){
    const st={op:"select",cols:"*",f:[],ord:null,lim:null,rng:null,single:false,row:null};
    const run=()=>{
      if(st.op==="upsert"){const r=clone(st.row);r.updated_at=new Date().toISOString();/* как docs_guard: время ставит сервер */DB.set(r.path,r);return{data:null,error:null}}
      let rows=[...DB.values()].filter(r=>st.f.every(([c,v,op])=>op===">"?String(val(r,c))>v:val(r,c)===v));
      if(st.op==="delete"){rows.forEach(r=>DB.delete(r.path));return{data:null,error:null}}
      if(st.ord){const[c,asc]=st.ord;rows.sort((a,b)=>(a[c]>b[c]?1:a[c]<b[c]?-1:0)*(asc?1:-1))}
      if(st.rng)rows=rows.slice(st.rng[0],st.rng[1]+1);
      if(st.lim!=null)rows=rows.slice(0,st.lim);
      const pick=r=>{const o={};st.cols.split(",").forEach(c=>{o[c.trim()]=clone(r[c.trim()])});return o};
      rows=rows.map(pick);{const c=st.f.find(f=>f[0]==="col");if(c&&!st.single)SEL.push([c[1],rows.length])}
      return{data:st.single?(rows[0]||null):rows,error:null};
    };
    const b={
      select(c){st.cols=c||"*";return b},eq(c,v){st.f.push([c,v]);return b},gt(c,v){st.f.push([c,v,">"]);return b},
      order(c,o){st.ord=[c,!(o&&o.ascending===false)];return b},limit(n){st.lim=n;return b},
      range(a,z){st.rng=[a,z];return b},maybeSingle(){st.single=true;return b},
      upsert(r){st.op="upsert";st.row=r;return b},delete(){st.op="delete";return b},
      then(res,rej){return Promise.resolve().then(run).then(res,rej)}
    };
    return b;
  }
  const client={
    from:()=>q(),
    rpc(n,a){RPC.push([n,a]);
      if(n==="doc_merge"){const r=DB.get(a.p);if(!r)return Promise.resolve({data:false,error:null});r.data=Object.assign(r.data||{},clone(a.patch));r.updated_at=new Date().toISOString();return Promise.resolve({data:true,error:null})}
      if(n==="acquire_lock")return Promise.resolve({data:true,error:null});
      if(n==="qstat_add"){// как M01: атомарный +1 пачкой, ключ — число
        const wk=Math.floor((Date.now()/864e5+3)/7);let k=0;(a.items||[]).forEach(it=>{if(!/^[0-9]{1,10}$/.test(String(it.h)))return;const p="qstats/"+it.h,o=(DB.get(p)||{}).data||{},ok=it.ok===true?1:0,sw=o.wk===wk;
          DB.set(p,{path:p,col:"qstats",id:String(it.h),updated_at:new Date().toISOString(),data:{n:(o.n|0)+1,ok:(o.ok|0)+ok,wk,wn:(sw?o.wn|0:0)+1,wok:(sw?o.wok|0:0)+ok}});k++});return Promise.resolve({data:k,error:null})}
      if(n==="player_places"){// как M02: 1 + игроки того же разряда (profiles.age) с рейтингом выше; без r — 1000
        const R=d=>d&&d.r!=null&&isFinite(+d.r)?+d.r:1000,age=id=>((DB.get("profiles/"+id)||{}).data||{}).age||"",o={};
        [...DB.values()].filter(r=>/^stats\/[^/]+\/players$/.test(r.col)&&r.id===a.u).forEach(me=>{o[me.col.split("/")[1]]=1+[...DB.values()].filter(d=>d.col===me.col&&age(d.id)===age(a.u)&&R(d.data)>R(me.data)).length});
        return Promise.resolve({data:o,error:null})}
      if(n==="disputes_summary"){const g={};[...DB.values()].filter(r=>r.col==="disputes"&&r.data&&r.data.h).forEach(r=>{const x=g[r.data.h]=g[r.data.h]||{h:r.data.h,q:r.data.q,a:r.data.a,by:new Set()};x.by.add(r.data.by)});
        const l=Object.values(g).map(x=>({h:x.h,q:x.q,a:x.a,n:x.by.size})).sort((x,y)=>y.n-x.n);return Promise.resolve({data:{hid:l.filter(x=>x.n>=3).map(x=>x.h),top:l.slice(0,10)},error:null})}
      if(n==="stat_bump"){// как в базе, без проверок участия (их проверяют SQL-проверки R-06): один раз на (src, путь)
        const L=window.__statlog=window.__statlog||new Set(),k=a.src+"|"+a.p;if(L.has(k))return Promise.resolve({data:false,error:null});L.add(k);
        const i=a.p.lastIndexOf("/"),o=(DB.get(a.p)||{}).data||{};
        DB.set(a.p,{path:a.p,col:a.p.slice(0,i),id:a.p.slice(i+1),updated_at:new Date().toISOString(),data:{g:(+o.g||0)+1,w:(+o.w||0)+(a.win?1:0),r:Math.max(0,(o.r==null?1000:+o.r)+a.delta),pts:(+o.pts||0)+a.score,best:Math.max(+o.best||0,a.score),last:Date.now()}});
        return Promise.resolve({data:true,error:null})}
      return Promise.resolve({data:null,error:null})},
    channel(){const c={on:()=>c,subscribe:()=>c};return c},removeChannel(){},
    auth:{
      getSession:()=>Promise.resolve({data:{session:ses},error:null}),
      signInAnonymously:()=>{ses={user:{id:UID,is_anonymous:true}};return Promise.resolve({data:{session:ses},error:null})},
      onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),
      signOut:()=>{ses=null;return Promise.resolve({error:null})}
    }
  };
  // тест может заранее положить документы: window.__seed=[{path,col,id,data}]
  (window.__seed||[]).forEach(r=>DB.set(r.path,Object.assign({updated_at:new Date().toISOString()},clone(r))));
  window.supabase={createClient:()=>client};
})();

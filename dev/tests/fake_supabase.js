/* Подставной supabase-js для тестов: таблица docs в памяти (window.__db), анонимный вход,
   rpc doc_merge / acquire_lock, остальные rpc → null. Реалтайма нет — игра опрашивает базу сама.
   Покрывает только то, что вызывает index.html (sbDoc/sbCol/sbWatch, init). */
(function(){
  const DB=window.__db=new Map(),RPC=window.__rpc=[];
  const UID="00000000-0000-4000-8000-000000000001";
  let ses=null;
  const val=(r,c)=>{const m=/^data->>(.+)$/.exec(c);if(m)return r.data&&r.data[m[1]]!=null?String(r.data[m[1]]):null;return r[c]};
  const clone=x=>x===undefined?x:JSON.parse(JSON.stringify(x));
  function q(){
    const st={op:"select",cols:"*",f:[],ord:null,lim:null,rng:null,single:false,row:null};
    const run=()=>{
      if(st.op==="upsert"){const r=clone(st.row);r.updated_at=r.updated_at||new Date().toISOString();DB.set(r.path,r);return{data:null,error:null}}
      let rows=[...DB.values()].filter(r=>st.f.every(([c,v])=>val(r,c)===v));
      if(st.op==="delete"){rows.forEach(r=>DB.delete(r.path));return{data:null,error:null}}
      if(st.ord){const[c,asc]=st.ord;rows.sort((a,b)=>(a[c]>b[c]?1:a[c]<b[c]?-1:0)*(asc?1:-1))}
      if(st.rng)rows=rows.slice(st.rng[0],st.rng[1]+1);
      if(st.lim!=null)rows=rows.slice(0,st.lim);
      const pick=r=>{const o={};st.cols.split(",").forEach(c=>{o[c.trim()]=clone(r[c.trim()])});return o};
      rows=rows.map(pick);
      return{data:st.single?(rows[0]||null):rows,error:null};
    };
    const b={
      select(c){st.cols=c||"*";return b},eq(c,v){st.f.push([c,v]);return b},
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

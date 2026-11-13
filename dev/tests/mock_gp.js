/* Подставной SDK GamePush: только то, что вызывает gp-adapter.js. Вызовы пишутся в window.__gp.calls.
   Это проверка нашей логики, а не работы на платформе. ?failsave=1 — sync() возвращает ошибку. */
(function(){
  const calls=[],log=(...a)=>calls.push(a),F=/failsave=1/.test(location.search);
  const store={arc:"",arcsurv:0};
  const products=[{id:101,tag:"starter",name:"Набор новичка",description:"300 звёзд",price:49,currency:"RUB",currencySymbol:"₽"},
    {id:102,tag:"noads",name:"Без рекламы",description:"",price:99,currency:"RUB",currencySymbol:"₽"},
    {id:103,tag:"founder",name:"Основатель",description:"",price:199,currency:"RUB",currencySymbol:"₽"}];
  const purchases=window.__gpBought===false?[]:[{productId:101,createdAt:"2026-11-14T10:00:00Z"}]; // набор новичка куплен, но не потреблён
  const ev={};
  const gp={
    language:"ru",
    gameStart(){log("gameStart")},gameplayStart(){log("gameplayStart")},gameplayStop(){log("gameplayStop")},
    on(n,f){ev[n]=f},
    player:{isLoggedIn:true,ready:Promise.resolve(),
      get:k=>store[k],set(k,v){store[k]=v;log("set "+k)},
      sync(){log("sync");return F?Promise.resolve(false):Promise.resolve(true)},login(){log("login");return Promise.resolve()}},
    ads:{isAdblockEnabled:!!window.__adblock,isFullscreenAvailable:true,isRewardedAvailable:true,
      showFullscreen(){log("fullscreen");return new Promise(r=>setTimeout(()=>r(true),50))},
      showRewardedVideo(){log("rewarded");return new Promise(r=>setTimeout(()=>r(true),window.__adMs||50))}},
    payments:{isAvailable:window.__gpPay!==false,products,purchases,
      purchase({tag}){log("purchase "+tag);const p=products.find(x=>x.tag===tag);const pu={productId:p.id,createdAt:"2026-11-14T11:00:00Z"};purchases.push(pu);return Promise.resolve({product:p,purchase:pu})},
      consume({tag}){log("consume "+tag);const i=purchases.findIndex(x=>x.productId===products.find(p=>p.tag===tag).id);if(i>=0)purchases.splice(i,1);return Promise.resolve({})}},
    leaderboard:{fetch(o){log("fetch "+o.orderBy[0]);
      return Promise.resolve({topPlayers:[{name:"Тест",rank:1,[o.orderBy[0]]:42},{name:"Ещё",rank:2,[o.orderBy[0]]:30}],player:{rank:2}})}}
  };
  window.__gp={calls,store,purchases};
  window.__yg={calls:[]}; // чтобы общие проверки harness.calls не падали
  const go=()=>window.onGPInit&&window.onGPInit(gp);
  if(window.onGPInit)go();else{let n=0;const t=setInterval(()=>{if(window.onGPInit||++n>100){clearInterval(t);go()}},20)}
})();

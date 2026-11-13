/* Подставной SDK Яндекс Игр для локальной проверки. Все вызовы пишутся в window.__yg.
   Управление: ?failsave в адресе — player.setData отклоняется; __yg.purchases — неподтверждённые покупки. */
(function(){
  const L=window.__yg={calls:[],failSave:/failsave/.test(location.search),cloud:null,purchases:[{productID:"starter",purchaseToken:"tok-1"}]};
  const log=(n,...a)=>{L.calls.push([n,...a]);};
  const player={isAuthorized:()=>true,getName:()=>"Тест",getUniqueID:()=>"u1",
    getData:()=>Promise.resolve(L.cloud||{}),
    setData:(d,f)=>{log("setData",f);if(L.failSave)return Promise.reject(new Error("save failed"));L.cloud=JSON.parse(JSON.stringify(d));return Promise.resolve()}};
  const payments={getCatalog:()=>Promise.resolve([{id:"starter",title:"Набор",price:"10 YAN",getPriceCurrencyImage:()=>""},{id:"noads",title:"Без рекламы",price:"50 YAN"},{id:"founder",title:"Основатель",price:"99 YAN"}]),
    getPurchases:()=>Promise.resolve(L.purchases.slice()),
    purchase:({id})=>{log("purchase",id);return Promise.resolve({productID:id,purchaseToken:"tok-"+Date.now()})},
    consumePurchase:t=>{log("consume",t);L.purchases=L.purchases.filter(p=>p.purchaseToken!==t);return Promise.resolve()}};
  const sdk={environment:{app:{id:"123"},i18n:{lang:"ru"},payload:null},
    features:{LoadingAPI:{ready:()=>log("ready")},GameplayAPI:{start:()=>log("gp_start"),stop:()=>log("gp_stop")}},
    on:()=>{},auth:{openAuthDialog:()=>Promise.resolve()},
    getPlayer:()=>Promise.resolve(player),
    getPayments:()=>Promise.resolve(payments),payments,
    leaderboards:{setScore:(n,s)=>{log("setScore",n,s);return Promise.resolve()},
      getEntries:(n,o)=>{log("getEntries",n);return Promise.resolve({userRank:1,entries:[{rank:1,score:42,player:{publicName:"Тест"}}]})}},
    // устаревший объект: как у настоящего SDK, без setScore/getEntries
    getLeaderboards:()=>Promise.resolve({setLeaderboardScore(){},getLeaderboardEntries(){}}),
    adv:{showFullscreenAdv:({callbacks:c})=>{log("adv");c.onOpen&&c.onOpen();setTimeout(()=>c.onClose&&c.onClose(true),50)},
      showRewardedVideo:({callbacks:c})=>{log("reward");c.onOpen&&c.onOpen();c.onRewarded&&c.onRewarded();setTimeout(()=>c.onClose&&c.onClose(),window.__adMs||50)}}};
  window.YaGames={init:()=>Promise.resolve(sdk)};
})();

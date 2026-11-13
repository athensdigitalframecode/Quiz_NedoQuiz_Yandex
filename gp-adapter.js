/* Адаптер GamePush: из объекта gp строит объект в форме Yandex SDK (ysdk), поэтому код игры не меняется.
   Включается, только если в gp-config.js заполнены projectId и publicToken.
   ПРОВЕРЕН ТОЛЬКО на подставном SDK (dev/tests/mock_gp.js), не на платформе: имена методов взяты из docs.gamepush.com.
   Что нужно создать в панели GamePush: поле игрока arc (тип data/string); поля-рекорды arcsurv, arcblitz, arctf,
   arcpic, arccls (тип stats/число); товары с тегами starter, noads, founder. */
(function(){
  var URLS=["https://gs.eponesh.com/sdk/game-score.js","https://s3.gamepush.com/files/gs/sdk/game-score.js",
    "https://s3-eu.gamepush.com/sdk/game-score.js","https://gamepush.com/sdk/game-score.js"];
  var fn=function(o,n){return !!o&&typeof o[n]==="function"};

  function load(cfg){
    return new Promise(function(res,rej){
      var urls=cfg.scriptUrl?[cfg.scriptUrl]:URLS,i=0;
      window.onGPInit=function(gp){res(gp)};
      var next=function(){
        if(i>=urls.length)return rej(new Error("gp-load"));
        var s=document.createElement("script");
        s.src=urls[i++]+"?projectId="+encodeURIComponent(cfg.projectId)+"&publicToken="+encodeURIComponent(cfg.publicToken)+"&callback=onGPInit";
        s.onerror=function(){s.remove();next()};
        document.head.appendChild(s);
      };
      next();
      setTimeout(function(){rej(new Error("gp-timeout"))},15000);
    });
  }

  function make(gp){
    var syncOk=function(){return Promise.resolve(gp.player.sync()).then(function(ok){if(ok===false)throw new Error("sync")})};

    /* реклама: нет блока или реклама недоступна → onError, игра идёт дальше без ролика */
    var adOff=function(kind){return gp.ads.isAdblockEnabled||gp.ads["is"+kind+"Available"]===false};
    var adv={
      showFullscreenAdv:function(o){var c=(o&&o.callbacks)||{};
        if(adOff("Fullscreen")){c.onError&&c.onError(new Error("noad"));return}
        c.onOpen&&c.onOpen();
        Promise.resolve(gp.ads.showFullscreen()).then(function(ok){c.onClose&&c.onClose(!!ok)},function(e){c.onError&&c.onError(e)});
      },
      showRewardedVideo:function(o){var c=(o&&o.callbacks)||{};
        if(adOff("Rewarded")){c.onError&&c.onError(new Error("noad"));return}
        c.onOpen&&c.onOpen();
        Promise.resolve(gp.ads.showRewardedVideo()).then(function(ok){if(ok&&c.onRewarded)c.onRewarded();c.onClose&&c.onClose()},function(e){c.onError&&c.onError(e)});
      }
    };

    /* облачное сохранение: весь прогресс — строка JSON в поле игрока arc */
    var player={
      isAuthorized:function(){return !!gp.player.isLoggedIn},
      getData:function(){
        var raw=gp.player.get("arc"),d={};
        try{if(raw)d.arc=JSON.parse(raw)}catch(e){}
        return Promise.resolve(d);
      },
      setData:function(data,flush){
        if(data&&data.arc!==undefined)gp.player.set("arc",JSON.stringify(data.arc));
        var p=syncOk();
        if(flush)return p; // flush=true: ждём подтверждения (покупку потребляем только после него)
        p.catch(function(){});return Promise.resolve();
      }
    };

    /* покупки: наш id товара = тег товара в GamePush; токен = тег@время покупки */
    var toks={};
    var products=function(){return gp.payments.products||[]};
    var tagOf=function(pid){var p=products().filter(function(x){return x.id===pid||x.tag===pid})[0];return p?p.tag:String(pid)};
    var conv=function(pu){
      var tag=tagOf(pu.productId),t=tag+"@"+(pu.createdAt||pu.productId);toks[t]=tag;
      return{productID:tag,purchaseToken:t};
    };
    var pay={
      getCatalog:function(){return Promise.resolve(products().map(function(p){
        var pr=p.price+" "+(p.currencySymbol||p.currency||"");
        return{id:p.tag,title:p.name,description:p.description,price:pr,priceValue:pr,getPriceCurrencyImage:function(){return ""}};
      }))},
      getPurchases:function(){return Promise.resolve((gp.payments.purchases||[]).map(conv))},
      purchase:function(o){return gp.payments.purchase({tag:o.id}).then(function(r){
        return conv(r.purchase||{productId:r.product&&r.product.id,createdAt:Date.now()});
      })},
      consumePurchase:function(token){var tag=toks[token];if(!tag)return Promise.resolve();return gp.payments.consume({tag:tag}).then(function(){})}
    };

    /* рейтинг: личный рекорд хранится в поле игрока arc<режим>, таблица строится по этому полю */
    var lb={
      setScore:function(name,score){gp.player.set(name,score);return syncOk()},
      getEntries:function(name,o){
        return gp.leaderboard.fetch({orderBy:[name],order:"DESC",limit:(o&&o.quantityTop)||5,includeFields:["rank"],withMe:"first"}).then(function(r){
          var list=r.topPlayers||r.players||[];
          return{userRank:r.player&&r.player.rank?+r.player.rank:0,
            entries:list.map(function(p,i){return{rank:+p.rank||i+1,score:p[name]|0,player:{publicName:p.name}}})};
        });
      }
    };

    return{
      adv:adv,
      getPlayer:function(){return Promise.resolve(player)},
      getPayments:function(){return gp.payments&&gp.payments.isAvailable?Promise.resolve(pay):Promise.reject(new Error("nopay"))},
      auth:{openAuthDialog:function(){return Promise.resolve(gp.player.login())}},
      leaderboards:lb,
      environment:{i18n:{lang:gp.language||"ru"},payload:"",app:{}}, // payload: у GamePush не проверен, ссылки-вызовы через него не работают
      features:{
        LoadingAPI:{ready:function(){if(fn(gp,"gameStart"))gp.gameStart()}},
        GameplayAPI:{start:function(){if(fn(gp,"gameplayStart"))gp.gameplayStart()},stop:function(){if(fn(gp,"gameplayStop"))gp.gameplayStop()}}
      },
      on:function(ev,f){var m={game_api_pause:"pause",game_api_resume:"resume"}[ev];if(m&&fn(gp,"on"))gp.on(m,f)}
    };
  }

  window.GPAdapter={load:load,make:make};
})();

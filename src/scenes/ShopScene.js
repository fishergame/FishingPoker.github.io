 (function(){
 'use strict';
 class ShopScene{
     constructor(game){
         this.game=game;
         this.modal=document.getElementById('shop-screen');
     }
     open(){
         const ov=document.getElementById('overlay-screen');
         if(ov){ov.innerHTML='';ov.classList.add('visible');this.game&&this.game.setOverlayState&&this.game.setOverlayState(true);}
         if(this.modal){this.modal.style.display='flex';setTimeout(()=>{this.modal.classList.add('shop-visible');},50);}
     }
     close(){
         const ov=document.getElementById('overlay-screen');
         if(this.modal){this.modal.classList.remove('shop-visible');setTimeout(()=>{this.modal.style.display='none';},200);}
         if(ov){ov.classList.remove('visible');this.game&&this.game.setOverlayState&&this.game.setOverlayState(false);}
     }
 }
 window.ShopScene=ShopScene;
 })();
 

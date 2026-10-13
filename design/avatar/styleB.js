/* Style B : « Mascotte » — chibi 3 têtes, même langage visuel que les esprits */
(function(){
var C=AVC, cr=C.cr, both=C.both, tube=C.tube, ell=C.ell, circ=C.circ, path=C.path, line=C.line, hsl=C.hsl;
var CX=120;
function pts(a){return a.map(function(p){return [CX+p[0],p[1]]})}
function render(o){
  var isF=o.sex==='f', m=o.muscle==null?.5:o.muscle, sk=C.skinPal(o.skin), u=o.uid||'b', out='';
  function lg(id,c,a,b,vert){return '<linearGradient id="'+id+u+'" x1="0" y1="0" x2="'+(vert?0:1)+'" y2="'+(vert?1:0)+'"><stop offset="0" stop-color="'+hsl(c[0],c[1],c[2]+(a||11))+'"/><stop offset=".45" stop-color="'+hsl(c[0],c[1],c[2])+'"/><stop offset="1" stop-color="'+hsl(c[0]-3,c[1]+6,c[2]-(b||14))+'"/></linearGradient>';}
  var hc=o.hairCol, defs='<defs>'+lg('sk',o.skin,10,12)+lg('cl',o.cl,10,16)+lg('sh',o.sh2,8,12)+lg('sn',o.sn,12,10)+lg('ac',o.ac,10,14)+lg('hr',hc,16,12)
   +'<radialGradient id="hd'+u+'" cx="38%" cy="30%" r="85%"><stop offset="0" stop-color="'+sk.hi+'"/><stop offset=".55" stop-color="'+sk.base+'"/><stop offset="1" stop-color="'+sk.lo+'"/></radialGradient>'
   +'<radialGradient id="fl'+u+'" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="rgba(0,0,0,.3)"/><stop offset="1" stop-color="rgba(0,0,0,0)"/></radialGradient></defs>';
  var G='url(#sk'+u+')', HD='url(#hd'+u+')', CL='url(#cl'+u+')', SH='url(#sh'+u+')', SN='url(#sn'+u+')', AC='url(#ac'+u+')', HR='url(#hr'+u+')';
  var H0=hsl(hc[0],hc[1],hc[2]), H1=hsl(hc[0],hc[1],hc[2]+18), H2=hsl(hc[0],hc[1]+4,hc[2]-10), acc=hsl(o.ac[0],o.ac[1],o.ac[2]), cld=hsl(o.cl[0],o.cl[1],o.cl[2]-20);
  var hair=o.hair, hy=98;
  out+=ell(CX,300,64,9,'url(#fl'+u+')');
  // cheveux arrière
  if(hair==='twin') [-1,1].forEach(function(sg){out+=path(cr(pts([[sg*52,hy-6],[sg*76,hy+10],[sg*82,hy+52],[sg*70,hy+84],[sg*58,hy+56],[sg*54,hy+20]]),true),HR);});
  if(hair==='bob') out+=path(cr(pts([[0,hy-52],[50,hy-40],[62,hy+10],[60,hy+50],[40,hy+60],[0,hy+50],[-40,hy+60],[-60,hy+50],[-62,hy+10],[-50,hy-40]]),true),HR);
  if(hair==='ponytail') out+=path(cr(pts([[34,hy-44],[70,hy-34],[86,hy+6],[82,hy+50],[66,hy+84],[62,hy+44],[64,hy+8],[44,hy-20]]),true),HR);
  if(hair==='curly') out+=circ(CX,hy-8,64,HR)+circ(CX-48,hy+10,26,HR)+circ(CX+48,hy+10,26,HR);
  // jambes
  [-1,1].forEach(function(sg){
    out+=path(cr(tube([[CX+sg*14,222],[CX+sg*15,252],[CX+sg*16,278]],[15+m*2.5,13.5+m*3,11.5+m*1],.5),true),G);
  });
  // bras (relâché à gauche du perso = côté +/-)
  var W=m*9;
  function relaxed(sg){return path(cr(tube([[CX+sg*(30+W*.7),170],[CX+sg*(37+W),196],[CX+sg*(38+W),222]],[11+m*3.5,10+m*5.5,8.5+m*1.5],.7),true),G)+ell(CX+sg*(38.5+W),229,8.6+m*1.2,9.4+m*1.2,G);}
  out+=relaxed(-1);
  if(o.wrist)out+=path(cr([[CX-(38+W)-9,213],[CX-(38+W)+9,213],[CX-(38+W)+9.6,221],[CX-(38+W)-9.6,221]],true),AC);
  // torse
  var tw=[[0,150],[14,152],[30+W*.6,160],[34+W,174],[33+W*.6,190],[26,208],[28,222],[0,226]];
  out+=path(cr(both(pts(tw),CX),true),G);
  // cou
  out+=path(cr([[CX-12,132],[CX+12,132],[CX+13,156],[CX-13,156]],true),G);
  // short / legging
  [-1,1].forEach(function(sg){out+=path(cr(tube([[CX+sg*14,214],[CX+sg*15,236],[CX+sg*15.5,(isF&&o.outfit==='tight')?262:246]],[18+m*2.5,16+m*3,15.5+m*3],.1),true),SH);
    out+=line('M'+(CX+sg*28)+',222L'+(CX+sg*28.6)+',240',acc,2.6);});
  out+=path(cr([[CX-26,208],[CX+26,208],[CX+27,224],[CX,230],[CX-27,224]],true),SH);
  out+=path(cr([[CX-25,208],[CX+25,208],[CX+25,215],[CX-25,215]],true),cld);
  // chaussures
  [-1,1].forEach(function(sg){var x=CX+sg*16;
    out+=path(cr([[x-14,272],[x+14,272],[x+15,284],[x+24+sg*2,288],[x+24+sg*2,298],[x-18,298],[x-16,284]],true),SN);
    out+=path(cr([[x-19,293],[x+25+sg*2,293],[x+25+sg*2,300],[x-19,300]],true),hsl(0,0,96));
    out+=path('M'+(x+(sg>0?-15:5))+',290Q'+(x+sg*2)+',281 '+(x+(sg>0?-3:17))+',290Z',AC);
    out+=path(cr([[x-11,266],[x+11,266],[x+12,274],[x-12,274]],true),hsl(0,0,95));});
  // haut
  var top=[[0,166],[8,156],[19,153],[28+W*.6,160],[32+W,174],[31+W*.6,190],[27,208],[0,211]];
  out+=path(cr(both(pts(top),CX),true),CL);
  out+=path(cr(both(pts([[0,166],[8,156],[19,153],[28+W*.6,160],[16,170],[0,172]]),CX),true),'rgba(255,255,255,.1)');
  out+=line(cr(pts([[-10,154],[-8,162],[0,167],[8,162],[10,154]]),false),cld,2.4);
  out+=path(cr(both(pts([[31+W,172],[30+W*.6,190],[27,208],[22,208],[25,190],[25+W*.8,174]]),CX),true),AC,' opacity=".95"');
  out+=path('M'+(CX-7)+',184L'+CX+',177L'+(CX+7)+',184L'+(CX+7)+',189L'+CX+',182L'+(CX-7)+',189Z','#fff',' opacity=".92"');
  // bras droit : pose biceps
  if(o.pose==='flex'){
    var j=[[CX+30+W*.7,170],[CX+50+W*.8,184],[CX+58+W*.8,170],[CX+50+W*.8,146]];
    out+=path(cr(tube(j,[11+m*3,10.5+m*3.5,9.4+m*1.2,8.8+m*.8],.7),true),G);
    // biceps : boule qui grossit avec le muscle
    out+=circ(CX+54+W*.8,166-m*2,5+m*12,G)+path('M'+(CX+46+m*0)+','+(160-m*3)+'Q'+(CX+54)+','+(154-m*5)+' '+(CX+62)+','+(160-m*3)+'Q'+(CX+56)+','+(158-m*3)+' '+(CX+46)+','+(160-m*3)+'Z',sk.hi,' opacity=".5"');
    out+=ell(CX+50+W*.8,139,9.4+m*1.4,10.4+m*1.4,G);
    out+=line('M'+(CX+43+W*.8)+',141Q'+(CX+50+W*.8)+',144 '+(CX+57+W*.8)+',141',sk.deep,1.2,' opacity=".45"');
    out+=path(cr([[CX+40,176],[CX+60,178],[CX+62,184],[CX+42,184]],true),AC,' opacity="0"');
  } else out+=relaxed(1);
  // tête
  [-1,1].forEach(function(sg){out+=ell(CX+sg*57,hy+8,6,9,G)+ell(CX+sg*57.5,hy+8,2.6,5,sk.lo,' opacity=".4"');});
  var hd=[[0,-49],[30,-44],[52,-22],[57,6],[50,34],[30,50],[0,54]];
  out+=path(cr(both(pts(hd.map(function(p){return [p[0],p[1]+hy]})),CX),true),HD);
  // yeux
  var ec=o.eyeCol;
  [-1,1].forEach(function(sg){var ex=CX+sg*22, ey=hy+12, rx=isF?12.4:11.2, ry=isF?14.6:13;
    if(o.expr==='happy'){out+=line('M'+(ex-rx+1)+','+(ey+4)+'Q'+ex+','+(ey-12)+' '+(ex+rx-1)+','+(ey+4),'#2a1b15',4.4)+line('M'+(ex-rx+1)+','+(ey-ry-4)+'Q'+(ex+sg*1)+','+(ey-ry-8)+' '+(ex+rx+1)+','+(ey-ry-3),H2,isF?2.4:3.4);return;}
    out+=ell(ex,ey,rx,ry,'#fff');
    out+=ell(ex+sg*.8,ey+1.4,rx*.78,ry*.82,hsl(ec[0],ec[1],ec[2]));
    out+=ell(ex+sg*.8,ey+2.2,rx*.46,ry*.5,'#1a110e');
    out+=circ(ex+sg*.8-3.4,ey-4.2,3.6,'#fff')+circ(ex+sg*.8+3.2,ey+5.6,1.7,'#fff',' opacity=".85"');
    out+=path('M'+(ex-rx-.8)+','+(ey-1)+'Q'+ex+','+(ey-ry*1.28)+' '+(ex+rx+.8)+','+(ey-1)+'Q'+ex+','+(ey-ry*1.05)+' '+(ex-rx-.8)+','+(ey-1)+'Z','#2a1b15');
    if(isF) out+=line('M'+(ex+sg*rx)+','+(ey-3)+'L'+(ex+sg*(rx+4.4))+','+(ey-7),'#2a1b15',2);
    if(o.expr==='fierce')out+=line('M'+(ex-sg*rx*.9)+','+(ey-ry-8)+'L'+(ex+sg*(rx+2))+','+(ey-ry-1),H2,4);else out+=line('M'+(ex-rx+1)+','+(ey-ry-5.6)+'Q'+(ex+sg*1)+','+(ey-ry-9.6)+' '+(ex+rx+1)+','+(ey-ry-4.4+(isF?-1:1)),H2,isF?2.4:3.4);
  });
  out+=ell(CX-37,hy+31,8,4.6,sk.blush,' opacity=".5"')+ell(CX+37,hy+31,8,4.6,sk.blush,' opacity=".5"');
  out+=path('M'+(CX-8)+','+(hy+33)+'Q'+CX+','+(hy+47)+' '+(CX+8)+','+(hy+33)+'Q'+CX+','+(hy+36)+' '+(CX-8)+','+(hy+33)+'Z','#3b1a22');
  out+=path('M'+(CX-4.6)+','+(hy+39)+'Q'+CX+','+(hy+36.4)+' '+(CX+4.6)+','+(hy+39)+'Q'+CX+','+(hy+44.4)+' '+(CX-4.6)+','+(hy+39)+'Z','#ff7e8c');
  out+=line('M'+(CX-1)+','+(hy+22)+'Q'+CX+','+(hy+24.6)+' '+(CX+1.6)+','+(hy+23),sk.deep,1.6,' opacity=".55"');
  // cheveux avant
  var cap=[[-56,hy+2],[-60,hy-30],[-38,hy-56],[0,hy-62],[38,hy-56],[60,hy-30],[56,hy+2],[48,hy-14],[34,hy-24],[18,hy-30],[0,hy-24],[-16,hy-34],[-34,hy-24],[-48,hy-14]];
  if(hair==='spiky'){
    out+=path(cr(pts(cap),true),HR);
    [[-46,-40,-62,-62],[-22,-56,-30,-80],[4,-62,12,-88],[28,-56,46,-78],[46,-40,68,-56]].forEach(function(s,i){out+=path('M'+(CX+s[0])+','+(hy+s[1])+'L'+(CX+s[2])+','+(hy+s[3])+'L'+(CX+s[0]+22)+','+(hy+s[1]+4)+'Z',HR)});
    out+=line(cr(pts([[-34,hy-46],[-8,hy-56],[22,hy-50]]),false),H1,3.4,' opacity=".6"');
  }
  if(hair==='bob'||hair==='twin'||hair==='ponytail'||hair==='bun'||hair==='buzz'){
    out+=path(cr(pts(cap),true),HR,hair==='buzz'?' opacity=".55"':'');
    out+=line(cr(pts([[-36,hy-45],[-6,hy-56],[26,hy-49]]),false),H1,3.6,' opacity=".6"');
    if(hair==='bob'){out+=path(cr(pts([[-58,hy+4],[-62,hy-28],[-38,hy-56],[0,hy-62],[38,hy-56],[62,hy-28],[58,hy+4],[56,hy+36],[46,hy+44],[48,hy+8],[40,hy-12],[20,hy-22],[0,hy-18],[-20,hy-26],[-40,hy-12],[-48,hy+8],[-46,hy+44],[-56,hy+36]]),true),HR)+line(cr(pts([[-36,hy-44],[-6,hy-56],[26,hy-48]]),false),H1,3.4,' opacity=".55"');}
    if(hair==='twin')[-1,1].forEach(function(sg){out+=path(cr(pts([[sg*52,hy-20],[sg*62,hy-12],[sg*56,hy-2]]),true),HR)+path(cr([[CX+sg*62,hy-8],[CX+sg*70,hy-14],[CX+sg*70,hy-4]],true),AC);});
    if(hair==='bun')out+=circ(CX,hy-70,19,HR)+circ(CX,hy-52,5,AC)+line(cr(pts([[-10,hy-78],[0,hy-84],[11,hy-78]]),false),H1,2.6,' opacity=".6"');
    if(hair==='ponytail')out+=circ(CX+62,hy-26,5,AC);
  }
  if(hair==='curly'){out+=circ(CX-30,hy-44,26,HR)+circ(CX+30,hy-44,26,HR)+circ(CX,hy-52,28,HR)+circ(CX-50,hy-20,20,HR)+circ(CX+50,hy-20,20,HR)+path(cr(pts([[-34,hy-16],[-14,hy-30],[14,hy-30],[34,hy-16],[24,hy-28],[0,hy-38],[-24,hy-28]]),true),HR)+circ(CX-22,hy-52,8,H1,' opacity=".5"')+circ(CX+14,hy-58,6,H1,' opacity=".5"');}
  if(o.glasses){var gc=o.glassCol||[220,20,20];[-1,1].forEach(function(sg){out+=circ(CX+sg*22,hy+13,17,'rgba(190,225,255,.28)',' stroke="'+hsl(gc[0],gc[1],gc[2])+'" stroke-width="3.6"')+line('M'+(CX+sg*(22-9))+','+(hy+4)+'Q'+(CX+sg*22)+','+(hy-2)+' '+(CX+sg*(22+10))+','+(hy+3),'#fff',2,' opacity=".45"');});out+=line('M'+(CX-6)+','+(hy+11)+'Q'+CX+','+(hy+7)+' '+(CX+6)+','+(hy+11),hsl(gc[0],gc[1],gc[2]),3.2)+line('M'+(CX-39)+','+(hy+10)+'L'+(CX-56)+','+(hy+6),hsl(gc[0],gc[1],gc[2]),3)+line('M'+(CX+39)+','+(hy+10)+'L'+(CX+56)+','+(hy+6),hsl(gc[0],gc[1],gc[2]),3);}
  if(o.cap){out+=path(cr(pts([[-58,hy-4],[-60,hy-30],[-36,hy-56],[0,hy-62],[36,hy-56],[60,hy-30],[58,hy-4],[0,hy-12]]),true),AC)+path(cr(pts([[-62,hy-2],[-30,hy-14],[30,hy-14],[62,hy-2],[44,hy+8],[0,hy+4],[-44,hy+8]]),true),'url(#ac'+u+')')+path(cr(pts([[-62,hy-2],[-30,hy-14],[30,hy-14],[62,hy-2],[44,hy+8],[0,hy+4],[-44,hy+8]]),true),'rgba(0,0,0,.12)')+circ(CX,hy-62,4.4,'#fff',' opacity=".9"')+line(cr(pts([[-38,hy-46],[-8,hy-58],[24,hy-52]]),false),'#fff',3.2,' opacity=".35"');}
  if(o.band) out+=path(cr([[CX-57,hy-17],[CX-30,hy-27],[CX,hy-29],[CX+30,hy-27],[CX+57,hy-17],[CX+57,hy-6],[CX+30,hy-16],[CX,hy-18],[CX-30,hy-16],[CX-57,hy-6]],true),AC)+line('M'+(CX-30)+','+(hy-22)+'Q'+CX+','+(hy-25)+' '+(CX+30)+','+(hy-22),'#fff',1.4,' opacity=".5"');
  return '<svg viewBox="0 0 240 320" xmlns="http://www.w3.org/2000/svg">'+defs+out+'</svg>';
}
window.AVB={render:render};
})();

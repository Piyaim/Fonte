/* Style C : « Sticker » — contour épais, aplats + une ombre franche, silhouette exagérée, pose double biceps */
(function(){
var C=AVC, cr=C.cr, both=C.both, tube=C.tube, hsl=C.hsl;
var CX=130, OL='#1a1626';
function pts(a){return a.map(function(p){return [CX+p[0],p[1]]})}
function render(o){
  var isF=o.sex==='f', m=o.muscle==null?.5:o.muscle, u=o.uid||'c', defs='', body=[], det='', k=0;
  function col(c,dl){return hsl(c[0],c[1],c[2]+(dl||0))}
  // part : {d, base, shade}
  function part(d,base,shade,layer){body.push({d:d,base:base,shade:shade,layer:layer||0});}
  function paintLayer(list){
    var ol='',fl='';
    list.forEach(function(p){ol+='<path d="'+p.d+'" fill="'+OL+'" stroke="'+OL+'" stroke-width="9" stroke-linejoin="round"/>';});
    list.forEach(function(p){var id='c'+u+(k++);
      defs+='<clipPath id="'+id+'"><path d="'+p.d+'"/></clipPath>';
      fl+='<path d="'+p.d+'" fill="'+p.shade+'"/><g clip-path="url(#'+id+')"><path d="'+p.d+'" fill="'+p.base+'" transform="translate(-5,-4)"/></g>';});
    return ol+fl;
  }
  var skin=o.skin, SK=col(skin), SKs=col(skin,-14), SKd=hsl(skin[0]-8,skin[1]+10,skin[2]-26), SKh=col(skin,12);
  var CLb=col(o.cl), CLs=col(o.cl,-17), SHb=col(o.sh2), SHs=col(o.sh2,-12), SNb=col(o.sn), SNs=col(o.sn,-10), ACb=col(o.ac), ACs=col(o.ac,-16);
  var hc=o.hairCol, Hb=col(hc), Hs=col(hc,-12);
  var sh=(isF?58:72)+m*(isF?4:9), wa=isF?27:33, hp=isF?44:40, chh=(isF?44:56)+m*(isF?1:5);
  var out='';
  // ombre au sol
  out+='<ellipse cx="'+CX+'" cy="352" rx="84" ry="9" fill="rgba(0,0,0,.25)"/>';
  var back=[], mid=[], front=[];
  // cheveux arrière
  if(o.hair==='ponytail') back.push({d:cr(pts([[22,12],[50,16],[72,40],[74,84],[64,120],[52,92],[52,56],[34,34]]),true),base:Hb,shade:Hs});
  if(o.hair==='long') back.push({d:cr(pts([[0,4],[34,10],[44,40],[48,96],[40,130],[0,124],[-40,130],[-48,96],[-44,40],[-34,10]]),true),base:Hb,shade:Hs});
  // jambes
  [-1,1].forEach(function(sg){
    back.push({d:cr(tube([[CX+sg*20,238],[CX+sg*28,278],[CX+sg*30,312],[CX+sg*28,338]],[28+m*3,25+m*3,20+m*2,15],.3),true),base:SK,shade:SKs});
  });
  // bras : double biceps
  var arms=[];
  [-1,1].forEach(function(sg){
    var j=[[CX+sg*(sh-14),106],[CX+sg*(sh+20),116],[CX+sg*(sh+38),100],[CX+sg*(sh+40),64]];
    var r=[20+m*5,18+m*6,15+m*3,13];
    arms.push({d:cr(tube(j,r,.5),true),base:SK,shade:SKs,fist:[CX+sg*(sh+40),54],sg:sg,pk:[CX+sg*(sh+34),84]});
  });
  // torse
  var tw=[[0,86],[16,90],[40,96],[sh-4,104],[sh-8,124],[chh,146],[wa+8,172],[wa,196],[wa+4,222],[hp+4,236],[hp-4,252],[0,256]];
  var torso={d:cr(both(pts(tw),CX),true),base:SK,shade:SKs};
  var neck={d:cr([[CX-17,56],[CX+17,56],[CX+20,98],[CX-20,98]],true),base:SK,shade:SKs};
  // tête
  var hy=40, hd=[[0,-34],[24,-32],[38,-14],[38,6],[32,22],[18,36],[0,40]];
  var head={d:cr(both(pts(hd.map(function(p){return [p[0],p[1]+hy]})),CX),true),base:SK,shade:SKs};
  var ears=[-1,1].map(function(sg){return {d:'M'+(CX+sg*36)+','+(hy-2)+'a9,11 0 1 '+(sg>0?1:0)+' 0,22z',base:SK,shade:SKs}});
  // tenue
  var short={d:cr(both(pts([[wa+10,196],[hp+8,226],[hp+10,246],[hp+6,252],[2,254]]),CX),true),base:SHb,shade:SHs};
  var shortLegs=[-1,1].map(function(sg){return {d:cr(tube([[CX+sg*20,236],[CX+sg*29,262],[CX+sg*31,292]],[30+m*3,27+m*3,26+m*2],.1),true),base:SHb,shade:SHs}});
  var top={d:cr(both(pts([[0,114],[12,92],[26,92],[sh-10,98],[sh-12,120],[chh+2,144],[wa+9,170],[wa+7,206],[0,210]]),CX),true),base:CLb,shade:CLs};
  var shoes=[-1,1].map(function(sg){var x=CX+sg*30;return {d:cr([[x-18,326],[x+18,326],[x+20,342],[x+34+sg*3,348],[x+34+sg*3,360],[x-28,360],[x-24,344]],true),base:SNb,shade:SNs}});
  // cheveux avant + coiffure
  var hairs=[];
  if(o.hair==='flat') hairs.push({d:cr(pts([[-40,hy-8],[-42,hy-28],[-22,hy-46],[6,hy-50],[34,hy-42],[42,hy-26],[40,hy-8],[32,hy-20],[0,hy-26],[-32,hy-20]]),true),base:Hb,shade:Hs});
  if(o.hair==='mohawk') hairs.push({d:cr(pts([[-12,hy-24],[-10,hy-58],[0,hy-78],[12,hy-58],[12,hy-24]]),true),base:Hb,shade:Hs},{d:cr(pts([[-40,hy-2],[-42,hy-20],[-34,hy-34],[-12,hy-26],[0,hy-24],[12,hy-26],[34,hy-34],[42,hy-20],[40,hy-2],[34,hy-14],[0,hy-20],[-34,hy-14]]),true),base:Hs,shade:Hs});
  if(o.hair==='ponytail'||o.hair==='long') hairs.push({d:cr(pts([[-40,hy-6],[-44,hy-28],[-22,hy-48],[6,hy-52],[34,hy-44],[44,hy-24],[40,hy-6],[34,hy-20],[10,hy-28],[-6,hy-24],[-26,hy-16]]),true),base:Hb,shade:Hs});
  // ordre de rendu
  var A=back.concat(arms.map(function(a){return a}));
  out+=paintLayer(back);
  out+=paintLayer([torso,neck].concat(shortLegs).slice(0,2));
  out+=paintLayer(arms);
  // poings
  var fists=arms.map(function(a){return {d:'M'+(a.fist[0]-14)+','+(a.fist[1]+4)+'a14,15 0 1 1 28,0a14,15 0 1 1 -28,0z',base:SK,shade:SKs}});
  out+=paintLayer(fists);
  out+=paintLayer(shortLegs.concat([short]));
  out+=paintLayer([top]);
  out+=paintLayer(shoes);
  [-1,1].forEach(function(sg){var x=CX+sg*30;out+='<path d="M'+(x-27)+',353L'+(x+34+sg*3)+',353L'+(x+34+sg*3)+',360L'+(x-27)+',360Z" fill="#f4f1f8"/>'+'<path d="M'+(x-14)+',334Q'+x+',329 '+(x+14)+',334" fill="none" stroke="#fff" stroke-width="3" opacity=".5" stroke-linecap="round"/>';});
  out+=paintLayer([neck]);
  out+=paintLayer(ears.concat([head]));
  // détails du corps (traits francs)
  function dl(d,w,c,op){return '<path d="'+d+'" fill="none" stroke="'+(c||SKd)+'" stroke-width="'+(w||3)+'" stroke-linecap="round" stroke-linejoin="round" opacity="'+(op==null?1:op)+'"/>'}
  det+=dl('M'+(CX-12)+',88Q'+CX+',98 '+(CX+12)+',88',3,SKd,.0);
  // abdos visibles sous le haut (haut court) : pas ici ; marque sur le haut
  det+='<path d="M'+(CX-13)+',150L'+CX+',134L'+(CX+13)+',150L'+(CX+13)+',160L'+CX+',144L'+(CX-13)+',160Z" fill="#fff" opacity=".95"/>';
  det+=dl('M'+(CX-sh+20)+',140Q'+(CX-sh+26)+',170 '+(CX-wa-6)+',196',3,CLs,.9)+dl('M'+(CX+sh-20)+',140Q'+(CX+sh-26)+',170 '+(CX+wa+6)+',196',3,CLs,.0);
  det+='<path d="M'+(CX-wa-8)+',196L'+(CX+wa+8)+',196L'+(CX+wa+8)+',206L'+(CX-wa-8)+',206Z" fill="'+ACb+'"/>';
  det+=dl('M'+(CX-wa-10)+',226L'+(CX-hp-4)+',282',4,ACb,1)+dl('M'+(CX+wa+10)+',226L'+(CX+hp+4)+',282',4,ACb,1);
  // biceps (pics) et lignes de bras
  arms.forEach(function(a){var sg=a.sg;
    det+=dl('M'+(a.pk[0]-sg*8)+','+(a.pk[1]-8)+'Q'+(a.pk[0]+sg*6)+','+(a.pk[1]+2)+' '+(a.pk[0]-sg*4)+','+(a.pk[1]+16),3.2,SKd,.85);
    det+=dl('M'+(CX+sg*(sh+14))+',121Q'+(CX+sg*(sh+24))+',113 '+(CX+sg*(sh+32))+',106',3,SKd,.5);
    det+='<path d="M'+(a.fist[0]-9)+','+(a.fist[1]+2)+'h18" stroke="'+SKd+'" stroke-width="3" stroke-linecap="round"/>';
    det+='<path d="M'+(a.fist[0]-6)+','+(a.fist[1]-6)+'q6,-4 12,0" fill="none" stroke="'+SKh+'" stroke-width="3" stroke-linecap="round" opacity=".7"/>';
  });
  out+=det;
  // visage
  var ec=o.eyeCol;
  [-1,1].forEach(function(sg){var ex=CX+sg*15, ey=hy+4;
    out+='<ellipse cx="'+ex+'" cy="'+ey+'" rx="7.4" ry="'+(isF?8.6:7.4)+'" fill="#fff" stroke="'+OL+'" stroke-width="3.2"/><circle cx="'+(ex+sg*1.4)+'" cy="'+(ey+1)+'" r="4.4" fill="'+hsl(ec[0],ec[1],ec[2])+'"/><circle cx="'+(ex+sg*1.4)+'" cy="'+(ey+1)+'" r="2.2" fill="'+OL+'"/><circle cx="'+(ex+sg*1.4-1.6)+'" cy="'+(ey-1.2)+'" r="1.4" fill="#fff"/>';
    out+=dl('M'+(ex-sg*(-9))+','+(ey-12.6)+'L'+(ex-sg*10)+','+(ey-(isF?10.6:8)),isF?3.4:5,OL,1)+'';
    out+=dl('M'+(ex+sg*10)+','+(ey-12.2-(isF?1:0))+'L'+(ex-sg*8)+','+(ey-(isF?11.6:10.6)),isF?3.4:5.2,OL,1);
  });
  out+=dl('M'+(CX-1)+','+(hy+10)+'Q'+(CX-4)+','+(hy+19)+' '+(CX+3)+','+(hy+19),3,SKd,.9);
  out+='<path d="M'+(CX-12)+','+(hy+27)+'Q'+CX+','+(hy+40)+' '+(CX+12)+','+(hy+27)+'Z" fill="#fff" stroke="'+OL+'" stroke-width="3.2" stroke-linejoin="round"/>'+dl('M'+(CX-9)+','+(hy+30)+'L'+(CX+9)+','+(hy+30),2,'#cfc9d6',.8);
  out+=paintLayer(hairs);
  if(o.hair==='flat') out+=dl(cr(pts([[-24,hy-30],[0,hy-36],[24,hy-30]]),false),3,col(hc,18),.7);
  if(o.band) out+='<path d="M'+(CX-41)+','+(hy-22)+'Q'+CX+','+(hy-38)+' '+(CX+41)+','+(hy-22)+'L'+(CX+41)+','+(hy-12)+'Q'+CX+','+(hy-28)+' '+(CX-41)+','+(hy-12)+'Z" fill="'+ACb+'" stroke="'+OL+'" stroke-width="4" stroke-linejoin="round"/>';
  var svg='<svg viewBox="-6 -34 272 410" xmlns="http://www.w3.org/2000/svg"><defs>'+defs+'</defs>'+out+'</svg>';
  return svg;
}
window.AVCs={render:render};
})();

import sys,json,os
from playwright.sync_api import sync_playwright
OUT=sys.argv[1]
js='''
(()=>{
var R={};
var P=function(o){return Object.assign({skin:[24,50,66],cl:[210,60,48],sh2:[222,26,28],ac:[24,95,56],sn:[222,15,24],hairCol:[24,40,22],eyeCol:[22,50,30],muscle:.55},o)};
// directions
R['A-m']=AVA.render(P({sex:'m',hair:'quiff',uid:'am',pose:'hips',wrist:true,hairCol:[24,45,20]}));
R['A-f']=AVA.render(P({sex:'f',hair:'long',uid:'af',pose:'hips',wrist:true,skin:[22,45,72],cl:[330,62,54],ac:[24,95,56],hairCol:[18,55,20],muscle:.45}));
R['B-m']=AVB.render(P({sex:'m',hair:'spiky',uid:'bm',pose:'flex',band:true}));
R['B-f']=AVB.render(P({sex:'f',hair:'twin',uid:'bf',pose:'flex',skin:[22,45,72],cl:[330,62,56],ac:[170,70,50],hairCol:[18,55,20],muscle:.45}));
R['C-m']=AVCs.render(P({sex:'m',hair:'flat',uid:'cm',band:true,muscle:.6}));
R['C-f']=AVCs.render(P({sex:'f',hair:'ponytail',uid:'cf',skin:[22,45,72],cl:[330,70,58],ac:[170,80,48],hairCol:[18,60,22],muscle:.4}));
// personnalisation (B)
R['cz-m']=AVB.render(P({sex:'m',hair:'spiky',uid:'zm',pose:'flex',glasses:1,glassCol:[24,95,56],wrist:1,muscle:.6,cl:[262,52,50],ac:[48,95,58]}));
R['cz-f']=AVB.render(P({sex:'f',hair:'bob',uid:'zf',pose:'flex',skin:[22,45,72],hairCol:[330,65,50],cl:[190,60,45],ac:[48,95,58],muscle:.5,expr:'happy'}));
// coiffures
var hairs=[['spiky',[24,40,22]],['bob',[14,60,32]],['twin',[42,70,62]],['ponytail',[330,70,65]],['bun',[215,70,48]],['curly',[18,30,10]],['buzz',[150,55,42]]];
hairs.forEach(function(h,i){R['hair-'+h[0]]=AVB.render(P({sex:i%2?'f':'m',hair:h[0],uid:'h'+i,hairCol:h[1],pose:'flex',muscle:.3,expr:i%3==1?'happy':undefined}))});
// tenues (colorways)
var outs=[['acier',[210,45,46],[24,95,56]],['neon',[330,75,56],[170,85,50]],['aube',[24,92,55],[48,95,60]],['obsidienne',[250,22,16],[44,90,56]],['glace',[195,70,70],[0,0,100]],['foret',[150,50,34],[48,90,56]]];
outs.forEach(function(c,i){R['out-'+c[0]]=AVB.render(P({sex:'m',hair:'buzz',uid:'o'+i,cl:c[1],ac:c[2],pose:'flex',muscle:.5,hairCol:[24,40,22]}))});
// progression
[.08,.35,.65,.98].forEach(function(mm,i){R['prog-'+i]=AVB.render(P({sex:'m',hair:'spiky',uid:'p'+i,pose:'flex',muscle:mm,cl:[210,60,48]}))});
// esprits
if(window.CREA){
R['crea-griffe']=CREA.svg({name:'Griffe',rar:'R',hue:355,arch:'beast',eyes:'fierce',ears:'cat',horn:'two',tail:'spike',pat:'stripes',mouth:'fang'},2);
R['crea-dragon']=CREA.svg({name:'Dragon',rar:'L',hue:45,sat:80,shift:-20,arch:'drake',eyes:'fierce',ears:'none',horn:'big',tail:'flame',pat:'bolt',mouth:'fang'},3);
}
return R;})()
'''
html='<html><body>'+''.join('<script src="file:///home/claude/dev/av/%s"></script>'%f for f in ['core.js','styleA.js','styleB.js','styleC.js'])+'<script src="file:///home/claude/fonte/server/static/figure.js"></script><script src="file:///home/claude/fonte/server/static/creatures.js"></script></body></html>'
open('/home/claude/dev/av/_d.html','w').write(html)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file:///home/claude/dev/av/_d.html'); R=pg.evaluate(js); print(errs, len(R))
    for k,v in R.items():
        open(os.path.join(OUT,k+'.svg'),'w').write(v)

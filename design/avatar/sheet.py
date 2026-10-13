import sys,json
from playwright.sync_api import sync_playwright
# usage: sheet.py out.png "js expr returning html"
out=sys.argv[1]; expr=sys.argv[2]; w=int(sys.argv[3]) if len(sys.argv)>3 else 1400; bg=sys.argv[4] if len(sys.argv)>4 else '#101820'
files=sys.argv[5].split(',') if len(sys.argv)>5 else ['core.js','styleA.js']
html='<html><body style="margin:0;background:%s"><div id=g style="display:flex;flex-wrap:wrap;gap:10px;padding:10px"></div>'%bg
for f in files: html+='<script src="file:///home/claude/dev/av/%s"></script>'%f
html+='<script>document.getElementById("g").innerHTML=(function(){%s})()</script></body></html>'%expr
open('/home/claude/dev/av/_s.html','w').write(html)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':w,'height':500}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.goto('file:///home/claude/dev/av/_s.html'); pg.wait_for_timeout(200)
    pg.screenshot(path=out,full_page=True); print('errs',errs)

import functools,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'.test-results/mobile-copy';E.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();results=[]
geometry='''()=>{
 const box=s=>document.querySelector(s).getBoundingClientRect();
 const before=(a,b)=>{if(box(a).bottom>box(b).top+1)throw Error(a+' overlaps '+b)};
 if(window.VirtualFit){
  before('.catalog-note','#model');before('#model','.buy');before('#item-name','#item-price');before('.buy .info','.buy .size-option');before('.buy .size-option','.buy .actions');
  const n=document.querySelector('#item-name');if(n.scrollHeight>n.clientHeight+1)throw Error('clipped product name');
 }else{
  before('.rw__head','.rw__stage');before('.rw__stage','.rw__controls');before('.rw__controls','.rw__panel');
  for(const info of document.querySelectorAll('[data-rw-panel]:not([hidden]) .rw__info')){
   const nodes=[...info.children].filter(n=>n.getBoundingClientRect().height>0);
   for(let i=1;i<nodes.length;i++)if(nodes[i-1].getBoundingClientRect().bottom>nodes[i].getBoundingClientRect().top+1)throw Error('product copy overlaps');
  }
 }
 if(document.documentElement.scrollWidth>innerWidth)throw Error('horizontal overflow');return true;
}'''
try:
 with sync_playwright() as w:
  b=w.chromium.launch(headless=True,args=['--no-sandbox'])
  for width,height in [(320,568),(360,640),(390,844),(430,932)]:
   for mode in ['virtualfit','runway']:
    c=b.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True);p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto(f'http://127.0.0.1:{s.server_port}/#preloved',wait_until='domcontentloaded');p.locator(f'.pl-fitting-entry [data-fitting="{mode}"]').click();expect(p.locator('#pf-status')).to_have_text('Katalog NEMU',timeout=45000);f=p.frames[-1]
    if mode=='virtualfit':
     f.evaluate('VirtualFit.select(NemuCatalog.rows.reduce((a,b)=>a.name.length>b.name.length?a:b).id)');f.wait_for_function('!VirtualFit.state.scanning&&Math.abs(VirtualFit.state.target-VirtualFit.state.position)<.001');p.wait_for_timeout(500);assert f.evaluate(geometry)
    else:
     for i in range(6):
      f.evaluate('(i)=>RunwayNative.go(i)',i);f.wait_for_function('RunwayNative.raf==null');assert f.evaluate(geometry)
    f.evaluate('scrollTo(0,0)');p.screenshot(path=str(E/f'{width}-{mode}-top.png'))
    f.locator('.buy' if mode=='virtualfit' else '[data-rw-panel]:not([hidden]) .rw__items').scroll_into_view_if_needed();p.screenshot(path=str(E/f'{width}-{mode}-copy.png'))
    assert not errors,errors;results.append({'width':width,'height':height,'mode':mode,'copyOverlap':False,'overflow':False,'allLooksOrLongestName':True});c.close()
  b.close()
 print(json.dumps(results));(E/'results.json').write_text(json.dumps(results,indent=2))
finally:s.shutdown()

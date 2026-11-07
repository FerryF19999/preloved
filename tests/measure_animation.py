"""Repeatable Chromium 4x CPU lab, not a claim about physical phone FPS."""
import functools,http.server,threading,json,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];E=R/'.test-results';E.mkdir(exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();results=[]
try:
 with sync_playwright() as w:
  b=w.chromium.launch(headless=True,args=['--no-sandbox'])
  for mode in ['virtualfit','runway']:
   c=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
   p.add_init_script('window.__rafCalls=0;const nativeRAF=window.requestAnimationFrame;window.requestAnimationFrame=cb=>nativeRAF.call(window,t=>{window.__rafCalls++;cb(t)});')
   cd=c.new_cdp_session(p);cd.send('Emulation.setCPUThrottlingRate',{'rate':4});cd.send('Performance.enable')
   p.goto(f'http://127.0.0.1:{s.server_port}/{mode}.html',wait_until='domcontentloaded')
   p.wait_for_function('window.NemuCatalog?.rows.length===181')
   settled='window.VirtualFit?.state.ready&&!VirtualFit.state.scanning&&VirtualFit.state.intro===1' if mode=='virtualfit' else 'window.RunwayNative&&RunwayNative.raf==null'
   p.wait_for_function(settled,timeout=20000);p.wait_for_timeout(2500)
   def metrics():return {x['name']:x['value'] for x in cd.send('Performance.getMetrics')['metrics']}
   start=metrics();calls=p.evaluate('__rafCalls');animations=p.evaluate('document.getAnimations().filter(a=>a.playState==="running").length');p.wait_for_timeout(2000);end=metrics()
   idle={'appRafCallbacks':p.evaluate('__rafCalls')-calls,'runningAnimations':animations,'taskMs':round((end['TaskDuration']-start['TaskDuration'])*1000,2),'layoutMs':round((end['LayoutDuration']-start['LayoutDuration'])*1000,2),'styleMs':round((end['RecalcStyleDuration']-start['RecalcStyleDuration'])*1000,2)}
   start=metrics();calls=p.evaluate('__rafCalls');t=time.perf_counter()
   if mode=='virtualfit':
    old=p.evaluate('VirtualFit.state.selectedId');p.locator('.arrow.next').click();p.wait_for_function('(id)=>VirtualFit.state.selectedId!==id&&!VirtualFit.state.scanning&&Math.abs(VirtualFit.state.target-VirtualFit.state.position)<.02',arg=old,timeout=15000)
   else:
    p.locator('[data-rw-next]').click();p.wait_for_function('RunwayNative.raf==null&&RunwayNative.still&&getComputedStyle(document.querySelector(".rw__hero.is-on .rw__morph")).visibility==="visible"&&Number(getComputedStyle(document.querySelector(".rw__hero.is-on .rw__morph")).opacity)>.99',timeout=15000)
   elapsed=time.perf_counter()-t;end=metrics()
   motion={'settledMs':round(elapsed*1000,2),'appRafCallbacks':p.evaluate('__rafCalls')-calls,'taskMs':round((end['TaskDuration']-start['TaskDuration'])*1000,2)}
   assert not errors,errors
   results.append({'mode':mode,'cpuThrottle':4,'idleWindowMs':2000,'idle':idle,'navigation':motion});p.screenshot(path=str(E/f'{sys.argv[1] if len(sys.argv)>1 else "animation"}-{mode}.png'));c.close()
  b.close()
 label=sys.argv[1] if len(sys.argv)>1 else 'animation';(E/(label+'.json')).write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
finally:s.shutdown()

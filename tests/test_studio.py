import threading,http.server,functools,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1];E=R/'.test-results/restored';E.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{s.server_port}/';report=[]
try:
 with sync_playwright() as w:
  b=w.chromium.launch(headless=True,args=['--no-sandbox'])
  for width,height in [(390,844),(320,740),(1440,1000)]:
   c=b.new_context(viewport={'width':width,'height':height},has_touch=True);p=c.new_page();errors=[];req=[]
   p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:req.append(r.url));p.goto(base+'#preloved',wait_until='domcontentloaded');assert not any('virtualfit.html' in u or 'runway.html' in u or 'preloved-fashion.json' in u for u in req)
   for mode in ['virtualfit','runway']:
    p.locator(('.pl-fitting-entry ' if mode=='virtualfit' else '#pl-fitting-dialog ')+f'[data-fitting="{mode}"]').click()
    expect(p.locator('#pf-status')).to_have_text('Katalog NEMU',timeout=45000)
    f=p.frames[-1];f.wait_for_function('NemuCatalog.rows.length===181');assert f.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,mode,'overflow')
    f.wait_for_timeout(2200)
    if mode=='virtualfit':
     source=f.locator('#source').get_attribute('href');selected=f.evaluate('(url)=>NemuCatalog.rows.find(p=>p.url===url).id',source)
     if f.locator('#add-to-bag').is_enabled():f.locator('#add-to-bag').click()
     assert f.evaluate('(id)=>NemuCatalog.bag().includes(id)',selected)
     f.locator('.arrow.next').click();expect(f.locator('#source')).not_to_have_attribute('href',source)
    else:
     panel=f.locator('[data-rw-panel]:not([hidden])');before=panel.get_attribute('data-rw-panel')
     if width<700:
      box=f.locator('[data-rw-stage]').bounding_box();x=box['x']+box['width']*.78;y=box['y']+box['height']*.4
      p.mouse.move(x,y);p.mouse.down();p.mouse.move(box['x']+box['width']*.2,y,steps=12);p.mouse.up()
     else:f.locator('[data-rw-next]').click()
     expect(f.locator('[data-rw-panel]:not([hidden])')).not_to_have_attribute('data-rw-panel',before)
     expect(f.locator('[data-rw-next]')).to_be_visible();expect(f.locator('[data-rw-prev]')).to_be_visible()
     playing_from=f.locator('[data-rw-panel]:not([hidden])').get_attribute('data-rw-panel')
     f.locator('[data-rw-auto]').click();expect(f.locator('[data-rw-auto]')).to_have_attribute('aria-pressed','true')
     expect(f.locator('[data-rw-panel]:not([hidden])')).not_to_have_attribute('data-rw-panel',playing_from,timeout=9000)
     f.locator('[data-rw-auto]').click();expect(f.locator('[data-rw-auto]')).to_have_attribute('aria-pressed','false')
     panel=f.locator('[data-rw-panel]:not([hidden])');bundle=panel.locator('[data-product-id]').evaluate_all('(els)=>[...new Set(els.map(e=>e.dataset.productId))]');panel.locator('[data-rw-all]').click();f.wait_for_function('(ids)=>ids.every(id=>NemuCatalog.bag().includes(id))',arg=bundle)
    f.evaluate('NemuCatalog.bag().forEach(id=>NemuCatalog.remove(id))')
    ids=f.evaluate('NemuCatalog.rows.slice(0,2).map(p=>p.id)');f.evaluate('(ids)=>{NemuCatalog.add(ids);NemuCatalog.add(ids)}',ids);expect(p.locator('#pf-bag .cart-count')).to_have_text('2');assert f.evaluate('NemuCatalog.bag().length')==2
    f.wait_for_timeout(2400) # Let original runway reveal transitions finish before evidence capture.
    p.screenshot(path=str(E/f'{width}-{mode}.png'));report.append({'width':width,'mode':mode,'lazyLoad':True,'ready':True,'realRows':181,'sharedCartDedup':True,'overflow':False})
   p.locator('#pf-bag').click();expect(p.locator('.cart-row')).to_have_count(2);assert not errors,errors;c.close()
  b.close()
 (E/'host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
finally:s.shutdown()

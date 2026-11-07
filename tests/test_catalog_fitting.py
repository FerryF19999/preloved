import json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
R=Path(__file__).resolve().parents[1]
BASE=__import__('os').environ.get('PREVIEW_URL','http://localhost:4188/')
S=Path(__import__('os').environ.get('EVIDENCE_DIR',str(R/'.test-results')));S.mkdir(parents=True,exist_ok=True)
report=[]
with sync_playwright() as w:
 b=w.chromium.launch(headless=True,args=['--no-sandbox'])
 for name,width,height in [('mobile',390,844),('small-mobile',320,740),('desktop',1440,1000)]:
  c=b.new_context(viewport={'width':width,'height':height},has_touch=True);p=c.new_page();errors=[];requests=[];writes=[]
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:requests.append(r.url));p.on('request',lambda r:writes.append(r.url) if r.method not in ['GET','HEAD'] else None)
  p.goto(BASE+'#preloved',wait_until='domcontentloaded');p.locator('.pl-fitting-entry [data-fitting="virtualfit"]').click();p.wait_for_function('document.querySelector("#pf-garment").naturalWidth>0')
  first=p.evaluate('fittingSelected()');expect(p.locator('#pf-product h3')).to_have_text(first['name']);expect(p.locator('#pf-product .pf-source')).to_have_attribute('href',first['url']);expect(p.locator('#pf-garment')).to_have_attribute('data-id',first['id']);assert p.locator('iframe').count()==0
  p.locator('#pf-next').click();second=p.evaluate('fittingSelected()');assert first['id']!=second['id'];expect(p.locator('#pf-product h3')).to_have_text(second['name'])
  p.locator('#pf-search').fill(second['name']);expect(p.locator('#pf-catalog [data-pf-id="'+second['id']+'"]')).to_be_visible();p.locator('#pf-toggle-look').click();assert p.evaluate('fittingLook.size')==2
  # Use a fixture image, not a user's private photo. The uploaded bytes stay local.
  fixture=R/second['preview']
  p.locator('#pf-upload').set_input_files(str(fixture));expect(p.locator('#pf-person')).to_be_visible();assert p.locator('#pf-person').get_attribute('src').startswith('blob:')
  p.locator('#pf-scale').fill('65');p.locator('#pf-x').fill('60');assert p.evaluate('document.querySelector("#pf-garment").style.width')=='65%';p.locator('#pf-remove-photo').click();expect(p.locator('#pf-person')).to_be_hidden();assert p.evaluate('fittingPhotoURL')==''
  p.locator('#pf-canvas').scroll_into_view_if_needed();p.screenshot(path=str(S/f'{name}-catalog-virtualfit.png'))
  p.locator('#pl-fitting-dialog [data-fitting="runway"]').click();expect(p.locator('.pf-board-item')).to_have_count(2)
  for i in [2,3]:
   product=p.evaluate('(i)=>fittingRows[i]',i);p.locator('#pf-search').fill(product['name']);p.locator('#pf-catalog [data-pf-id="'+product['id']+'"] ').click();p.locator('#pf-toggle-look').click()
  expect(p.locator('.pf-board-item')).to_have_count(4);assert p.evaluate('[...fittingLook].every(id=>byId.get(id).storeCategory==="preloved")')
  assert p.locator('#pf-total').inner_text()==p.evaluate('money([...fittingLook].reduce((sum,id)=>sum+byId.get(id).price,0))')
  p.locator('.pf-board-item').first.click();expect(p.locator('#pf-product')).to_have_attribute('data-product-id',first['id']);expect(p.locator('#pf-product h3')).to_have_text(first['name'])
  p.locator('#pf-save-look').click();assert p.evaluate('[...fittingLook].every(id=>plLook.has(id))');p.locator('#pf-add-look').click();expect(p.locator('#pf-add-look')).to_be_disabled();assert p.evaluate('cart.size')==4
  p.locator('#pf-board').scroll_into_view_if_needed();p.wait_for_function('[...document.querySelectorAll(".pf-board-item img")].every(i=>i.complete&&i.naturalWidth>0)');p.screenshot(path=str(S/f'{name}-catalog-trylook.png'))
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.querySelector("#pl-fitting-dialog").scrollWidth<=innerWidth')
  ids=p.evaluate('[...fittingLook]');p.locator('#pf-bag').click();expect(p.locator('.cart-row')).to_have_count(4);assert set(p.locator('.cart-row').evaluate_all('(els)=>els.map(e=>e.dataset.cartId)'))==set(ids);p.keyboard.press('Escape')
  p.locator('.pl-fitting-entry [data-fitting="virtualfit"]').click();p.locator('#pf-search').fill('');p.locator('#pf-more').click();expect(p.locator('.pf-catalog-card')).to_have_count(24);p.locator('#pf-detail').click();expect(p.locator('#viewer')).to_be_visible();assert p.evaluate('current')==first['id'];p.keyboard.press('Escape')
  assert not any('higgs.ai' in u or 'reel-ref' in u or 'myshopify' in u or 'virtualfit.html' in u or 'runway.html' in u for u in requests)
  assert not errors,errors;assert not writes,writes
  report.append({'viewport':name,'status':'PASS','checks':['catalog-only photos and metadata','selected source identity','next/search/load more','local-only upload/remove/position controls','4 real product composition','board selects exact catalog ID','correct IDR total','shared save/cart','no duplicate cart entries','source detail','no overflow','no reference demo requests','no JS errors or network writes']});c.close()
 b.close()
(S/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

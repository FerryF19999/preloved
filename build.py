"""Build the static preview from the normalized public NEMU snapshot (stdlib only)."""
from pathlib import Path
import json, re, gzip
R = Path(__file__).parent
products = json.loads((R / 'catalog.json').read_text())
proof = json.loads((R / 'catalog-proof.json').read_text())
assert len(products) == len({p['id'] for p in products}) == proof['apiTotal'] == 5041

def safe_json(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')

experience = (R / 'experience.js').read_text()
words = [w for block in re.findall(r"words:\[(.*?)\]", experience) for w in re.findall(r"'([^']+)'", block)]
required = {p['id'] for w in words for p in products if w.lower() in p['name'].lower()}
required.add('70526e2c-ff0f-4890-8c8e-0988b627e0cc')
seed = [dict(p) for p in products if p['storeCategory'] == 'preloved' or p['id'] in required]
(R / 'details').mkdir(exist_ok=True)
for p in seed:
    (R / 'details' / (p['id'] + '.json')).write_text(safe_json({'gallery': p['gallery']}))
    p['gallery'] = []
    p['galleryPending'] = True
    thumb = R / 'thumbs' / (p['id'] + '.webp')
    if thumb.exists():
        p['preview'] = 'thumbs/' + thumb.name
fashion = [p for p in seed if p['category'] in ['fashion-men', 'fashion-women'] and p['storeCategory'] == 'preloved']
assert len(fashion) == 181
(R / 'preloved-fashion.json').write_text(safe_json(fashion))
html = (R / 'discovery-template.html').read_text().replace('__PRODUCTS__', safe_json(seed)).replace('__CATEGORIES__', safe_json(json.loads((R / 'categories.json').read_text()))).replace('__COUNT__', format(len(products), ',').replace(',', '.'))
for name in ['experience.css', 'shipping.css', 'preloved.css', 'preloved-mobile.css', 'preloved-studio.css']:
    html = html.replace('<link rel="stylesheet" href="' + name + '">', '<style>' + (R / name).read_text() + '</style>')
for name in ['experience.js', 'fulfillment.js', 'shipping.js', 'preloved.js', 'preloved-studio.js']:
    html = html.replace('<script src="' + name + '"></script>', '<script>' + (R / name).read_text() + '</script>')
# The public entry exposes only the two visual studios; catalog stays a data source.
html = (R / 'studio-template.html').read_text()
(R / 'index.html').write_text(html)
print(json.dumps({'catalogProducts': len(products), 'bootstrapProducts': len(seed), 'htmlBytes': len(html.encode()), 'gzipBytes': len(gzip.compress(html.encode()))}))

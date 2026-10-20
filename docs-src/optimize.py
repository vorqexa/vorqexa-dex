import re, io, os, sys, base64, shutil
from PIL import Image

DOCS, JS, INDEX = 'docs-src/docs.html', 'script.js', 'index.html'
for f in (DOCS, JS, INDEX):
    shutil.copy(f, '/tmp/' + os.path.basename(f) + '.before-optimize')

def kb(p):
    return os.path.getsize(p) // 1024

# 1) smaller copies of your official logo and favicon (originals stay untouched)
logo = Image.open('assets/logo.webp').convert('RGBA')
print('logo.webp', logo.size, kb('assets/logo.webp'), 'KB')
h = min(120, logo.height)
w = round(logo.width * h / logo.height)
logo.resize((w, h), Image.LANCZOS).save('assets/logo-sm.webp', 'WEBP', quality=85, method=6)
print('  -> logo-sm.webp', (w, h), kb('assets/logo-sm.webp'), 'KB')

fav = Image.open('assets/favicon.png').convert('RGBA')
print('favicon.png', fav.size, kb('assets/favicon.png'), 'KB')
fav.thumbnail((192, 192), Image.LANCZOS)
fav.save('assets/favicon-192.png', 'PNG', optimize=True)
print('  -> favicon-192.png', fav.size, kb('assets/favicon-192.png'), 'KB')

# 2) point index.html at the small files
idx = open(INDEX, encoding='utf-8', newline='').read()
n1, n2 = idx.count('assets/logo.webp'), idx.count('assets/favicon.png')
idx = idx.replace('assets/logo.webp', 'assets/logo-sm.webp').replace('assets/favicon.png', 'assets/favicon-192.png')
open(INDEX, 'w', encoding='utf-8', newline='').write(idx)
print('index.html: logo refs', n1, ', favicon refs', n2)
for f in (JS, 'styles.css'):
    t = open(f, encoding='utf-8').read()
    for name in ('assets/logo.webp', 'assets/favicon.png'):
        if name in t:
            print('NOTE:', f, 'still references', name)

# 3) docs: official logo in the header, no favicon, same size as the main header
d = open(DOCS, encoding='utf-8', newline='').read()
before = len(d)
d = re.sub(r'<link[^>]*href="data:image[^"]*"[^>]*>\s*', '', d)

uri = 'data:image/webp;base64,' + base64.b64encode(open('assets/logo-sm.webp', 'rb').read()).decode()
d, k = re.subn(r'(<a[^>]*class="brand"[^>]*>)(.*?)(</a>)',
               lambda m: m.group(1) + '<img alt="" src="' + uri + '"/>' + m.group(3),
               d, count=1, flags=re.S)
if k != 1:
    sys.exit('docs brand link not found, nothing packed')

LOGO_CSS = r'''
/* DOCS-LOGO */
.topbar .brand img{height:32px;width:auto;max-width:150px;object-fit:contain;display:block}
@media(max-width:640px){.topbar .brand img{height:28px}}
/* END-DOCS-LOGO */
'''
d = re.sub(r'\n?/\* DOCS-LOGO \*/.*?/\* END-DOCS-LOGO \*/\n?', '\n', d, flags=re.S)
d = d.replace('</style>', LOGO_CSS + '</style>', 1)
open(DOCS, 'w', encoding='utf-8', newline='').write(d)
print('docs.html', before // 1024, 'KB ->', len(d) // 1024, 'KB')

# 4) pack the docs into script.js
s = open(JS, encoding='utf-8', newline='').read()
b = base64.b64encode(d.encode('utf-8')).decode()
new, n = re.subn(r'(var docsData = ")[^"]*(")', lambda mm: mm.group(1) + b + mm.group(2), s, count=1)
if n != 1:
    sys.exit('docsData not found in script.js')
open(JS, 'w', encoding='utf-8', newline='').write(new)
print('script.js', len(s) // 1024, 'KB ->', len(new) // 1024, 'KB')
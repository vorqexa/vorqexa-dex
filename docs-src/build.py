import re, base64, sys, os

DOCS = 'docs-src/docs.html'
JS = 'script.js'

h = open(DOCS, encoding='utf-8', newline='').read()

# 1) pack the docs into script.js for the in-page overlay
s = open(JS, encoding='utf-8', newline='').read()
b = base64.b64encode(h.encode('utf-8')).decode()
new, n = re.subn(r'(var docsData = ")[^"]*(")', lambda m: m.group(1) + b + m.group(2), s, count=1)
if n != 1:
    sys.exit('docsData not found in script.js')
if new != s:
    open(JS, 'w', encoding='utf-8', newline='').write(new)
    print('script.js docs updated')
else:
    print('script.js docs already up to date')

# 2) standalone page at docs/index.html (search engines, direct links, no JavaScript)
page = h

def fix_anchor(m):
    tag = m.group(0)
    if 'closeVorqexaDocs' not in tag:
        return tag
    tag = re.sub(r'\s+onclick="[^"]*"', '', tag)
    return tag.replace('href="#"', 'href="../"')

page = re.sub(r'<a\b[^>]*>', fix_anchor, page)
page = re.sub(r'<button[^>]*closeVorqexaDocs[^>]*>(.*?)</button>',
              lambda m: '<a class="docs-return" href="../">' + m.group(1) + '</a>', page, flags=re.S)
if 'name="description"' not in page:
    page = page.replace('</title>', '</title>\n<meta name="description" content="Vorqexa documentation: how trading works, accounts and deposits, fees, security, markets and FAQ."/>', 1)
if 'fonts.googleapis.com/css2' not in page:
    fonts = ('<link href="https://fonts.googleapis.com" rel="preconnect"/>'
             '<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>'
             '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&amp;family=Inter:wght@400;500;600&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap" rel="stylesheet"/>')
    page = page.replace('</head>', fonts + '\n</head>', 1)
os.makedirs('docs', exist_ok=True)
open('docs/index.html', 'w', encoding='utf-8', newline='').write(page)
print('docs/index.html written')

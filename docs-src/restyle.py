import re, base64, shutil, sys

DOCS = 'docs-src/docs.html'
JS = 'script.js'
shutil.copy(DOCS, '/tmp/docs.before-restyle.html')
shutil.copy(JS, '/tmp/script.before-restyle.js')

CSS = r'''
/* DOCS-RESTYLE */
:root{--bg:#030504;--panel:#0B0F0D;--panel2:#0F1512;--line:#1C2620;--text:#EDF5F0;--muted:#7C9089;--accent:#B6FAD1;--accent-dark:#04140D}
body{background:radial-gradient(600px 400px at 85% -5%,rgba(182,250,209,.08),transparent 60%),radial-gradient(500px 400px at -5% 40%,rgba(182,250,209,.04),transparent 60%),var(--bg);background-attachment:fixed;-webkit-font-smoothing:antialiased}
h1,h2,h3{font-family:'Space Grotesk',Inter,ui-sans-serif,system-ui,sans-serif;text-wrap:balance}
.eyebrow,.side-title{font-family:'JetBrains Mono',ui-monospace,monospace}
code{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:.86em}
::selection{background:rgba(182,250,209,.25);color:var(--text)}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
[id]{scroll-margin-top:96px}

.topbar{background:rgba(3,5,4,.82);backdrop-filter:blur(10px)}
.brand{font-weight:600}
.navlinks{gap:30px;color:var(--muted)}
.navlinks a{transition:color .15s ease}
.nav-cta{border-radius:7px;background:transparent;color:var(--text);transition:border-color .15s ease,color .15s ease}
.nav-cta:hover{border-color:var(--accent);color:var(--accent)}

.layout{gap:64px}
.side{border-left:1px solid var(--line)}
.side a{margin-left:-1px;padding:8px 14px;border-left:2px solid transparent;border-radius:0 8px 8px 0;transition:color .15s ease,background .15s ease,border-color .15s ease}
.side a:hover{color:var(--text);background:rgba(182,250,209,.05);border-left-color:var(--accent)}
.side-title{color:var(--muted);letter-spacing:.2em;margin-bottom:14px}

.content{max-width:760px}
.eyebrow{letter-spacing:.2em}
h1{letter-spacing:-.04em}
h3{font-weight:600}
section{margin-top:56px;padding-top:34px;border-top:1px solid var(--line)}
section>h2{margin:0 0 16px}

.card,.step,.note{background:var(--panel);border-radius:10px}
.card{transition:transform .28s cubic-bezier(.2,.8,.2,1),border-color .25s ease}
.card:hover{transform:translateY(-3px);border-color:rgba(182,250,209,.2)}
.step{transition:border-color .25s ease,transform .25s ease}
.step:hover{border-color:rgba(182,250,209,.3);transform:translateX(4px)}
.note{border-color:rgba(182,250,209,.2)}
.callout{border-left-color:var(--accent)}
th{background:var(--panel2)}

#faq h3{margin:0;padding:22px 0 6px;border-top:1px solid var(--line)}
#faq h2+h3{border-top:0;padding-top:0}
#faq p{margin:0 0 16px}

.footer{color:var(--muted)}
.footerrow .docs-return{padding:9px 16px;border:1px solid var(--line);border-radius:7px;background:transparent;color:var(--text);cursor:pointer;transition:border-color .15s ease,color .15s ease}
.footerrow .docs-return:hover{border-color:var(--accent);color:var(--accent)}

@media(max-width:850px){.side{border-left:0}.side a{margin-left:0;border-left:0;border-radius:8px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.card:hover,.step:hover{transform:none}}
/* END-DOCS-RESTYLE */
'''

h = open(DOCS, encoding='utf-8', newline='').read()

# remove a previous restyle block so this script can be re-run
h = re.sub(r'\n?/\* DOCS-RESTYLE \*/.*?/\* END-DOCS-RESTYLE \*/\n?', '\n', h, flags=re.S)

if '</style>' not in h:
    sys.exit('no </style> found, nothing changed')
h = h.replace('</style>', CSS + '</style>', 1)

# add a Journal link to the top navigation (once)
m = re.search(r'<nav class="navlinks">.*?</nav>', h, re.S)
if m and 'href="#journal"' not in m.group(0):
    nav = m.group(0)
    nav2 = nav.replace('<a href="#trading">Trading</a>',
                       '<a href="#trading">Trading</a>\n<a href="#journal">Journal</a>', 1)
    h = h.replace(nav, nav2, 1)

open(DOCS, 'w', encoding='utf-8', newline='').write(h)

# pack the docs into script.js
s = open(JS, encoding='utf-8', newline='').read()
b = base64.b64encode(h.encode('utf-8')).decode()
new, n = re.subn(r'(var docsData = ")[^"]*(")', lambda mm: mm.group(1) + b + mm.group(2), s, count=1)
if n != 1:
    sys.exit('docsData not found in script.js')
open(JS, 'w', encoding='utf-8', newline='').write(new)
print('docs restyled and packed into script.js')
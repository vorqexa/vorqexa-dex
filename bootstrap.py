import os, re, sys, shutil, subprocess

def read(p):
    return open(p, encoding='utf-8', newline='').read()

def write(p, t):
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    open(p, 'w', encoding='utf-8', newline='').write(t)

for f in ('index.html', 'script.js', 'styles.css'):
    shutil.copy(f, '/tmp/' + f + '.before-hardening')

problems = []
idx, js, css = read('index.html'), read('script.js'), read('styles.css')

# 1) app URL lives in one place: APP_ORIGIN in script.js
SET_LAUNCH = """
  (function(){
    function setLaunchLinks(){
      document.querySelectorAll('a[data-launch]').forEach(function(a){ a.setAttribute('href', APP_ORIGIN + '/'); });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setLaunchLinks);
    else setLaunchLinks();
  })();"""
if 'data-launch' not in idx:
    idx, n = re.subn(r'(<a\b[^>]*?)\s(href="https://dex\.vorqexa\.xyz/")', r'\1 data-launch="" \2', idx)
    if n < 1:
        problems.append('no launch links found in index.html')
    else:
        print('launch links tagged:', n)
if 'a[data-launch]' not in js:
    old_sel = 'a[href^="https://dex.vorqexa.xyz/"]'
    anchor = "var APP_ORIGIN='https://dex.vorqexa.xyz';"
    if js.count(old_sel) < 1 or js.count(anchor) != 1:
        problems.append('launch handlers or APP_ORIGIN not found in script.js (selectors: %d, origin: %d)' % (js.count(old_sel), js.count(anchor)))
    else:
        print('launch selectors updated:', js.count(old_sel))
        js = js.replace(old_sel, 'a[data-launch]').replace(anchor, anchor + SET_LAUNCH)

# 2) Docs links point to the real /docs/ page (JavaScript still opens the overlay on click)
old_docs = 'data-vorqexa-docs="" href="#docs"'
if old_docs in idx:
    print('docs links updated:', idx.count(old_docs))
    idx = idx.replace(old_docs, 'data-vorqexa-docs="" href="docs/"')

# 3) skip link
if 'vq-skip' not in idx:
    if 'id="main"' in idx:
        problems.append('id="main" already exists in index.html')
    else:
        idx, n1 = re.subn(r'(<body[^>]*>)', r'\1\n<a class="vq-skip" href="#main">Skip to content</a>', idx, count=1)
        idx, n2 = re.subn(r'<section class="hero">', '<section class="hero" id="main" tabindex="-1">', idx, count=1)
        if n1 != 1 or n2 != 1:
            problems.append('skip link: <body> or hero section not found')

# 4) small CSS fixes
COMPAT = """
/* COMPAT-A11Y */
header{-webkit-backdrop-filter:blur(10px)}
.vq-reveal.vq-in,.vq-reveal.vq-visible{will-change:auto}
.vq-skip{position:absolute;left:-9999px;top:8px;z-index:100;padding:10px 16px;border-radius:7px;background:var(--mint);color:#04140D;font-weight:600}
.vq-skip:focus{left:12px}
#main:focus{outline:none}
"""
if 'COMPAT-A11Y' not in css:
    css = css.rstrip('\n') + '\n' + COMPAT

# 5) page behind the docs overlay becomes inert while it is open
INERT_FN = """function vqSetInert(on, overlay){
    Array.prototype.forEach.call(document.body.children, function(el){
      if (el === overlay || el.tagName === 'SCRIPT') return;
      if (on) { el.setAttribute('inert', ''); el.setAttribute('data-vq-inert', ''); }
      else if (el.hasAttribute('data-vq-inert')) { el.removeAttribute('inert'); el.removeAttribute('data-vq-inert'); }
    });
  }
  function getDocsOverlay() {"""
if 'vqSetInert' not in js:
    a1 = 'function getDocsOverlay() {'
    a2 = "overlay.style.display = 'block';"
    a3 = "if (overlay) overlay.style.display = 'none';"
    if js.count(a1) != 1 or js.count(a2) != 1 or js.count(a3) != 1:
        problems.append('docs overlay open/close code not as expected (%d/%d/%d)' % (js.count(a1), js.count(a2), js.count(a3)))
    else:
        js = js.replace(a1, INERT_FN).replace(a2, a2 + '\n    vqSetInert(true, overlay);').replace(a3, a3 + '\n    vqSetInert(false, overlay);')

if problems:
    print('NOTHING CHANGED. Problems:')
    for p in problems:
        print(' -', p)
    sys.exit(1)

write('index.html', idx)
write('script.js', js)
write('styles.css', css)

# 6) new files (existing ones are kept, except docs-src/build.py)
FILES = {}
OVERWRITE = {'docs-src/build.py'}

FILES['.gitignore'] = r'''node_modules/
playwright-report/
test-results/
.DS_Store
*.zip
*.log
*.bak
__pycache__/
'''

FILES['README.md'] = r'''# Vorqexa website

Plain HTML, CSS and JavaScript. The main page has no build step.

## Layout
- `index.html` - landing page
- `styles.css` - all styles; design tokens are the variables in `:root`
- `script.js` - interactions, scroll animations, docs overlay
- `assets/` - logo and favicon
- `docs-src/docs.html` - the docs source of truth
- `docs/index.html` - generated standalone docs page (do not edit by hand)
- `scripts/` and `tests/` - automated checks

## Rules that keep it maintainable
1. **App link.** The trading app URL is `APP_ORIGIN` in `script.js`. Launch buttons in `index.html` carry `data-launch` and a matching `href` (fallback without JavaScript). To change it, edit `APP_ORIGIN` and those `href`s, then run `npm run check`, which fails if they disagree.
2. **Docs.** Edit `docs-src/docs.html`, then run `npm run build:docs`. It repacks the docs into `script.js` and regenerates `docs/index.html`. Never edit the `docsData` line by hand.
3. **CSS.** No new `!important`. Use the `:root` variables instead of hard-coded colors. Run `python3 scripts/css_report.py` to find dead or duplicated rules.
4. **Cache busting.** `styles.css` and `script.js` load with a `?v=` query. Change the number when you edit them, or hard refresh (Ctrl+Shift+R) while testing.
5. **Security.** The CSP is a `<meta>` tag in `index.html`. Extra headers live in `_headers` (Netlify, Cloudflare Pages) and `vercel.json`. New third-party scripts, fonts or images stay blocked until the CSP allows them.

## Commands
- `python3 -m http.server 8000` - run locally
- `npm install` - once
- `npm run check` - syntax, file references, app-link and docs sync, HTML lint
- `npm run build:docs` - rebuild the docs
- `npx playwright install --with-deps chromium`, then `npm test` - smoke tests
'''

FILES['package.json'] = r'''{
  "name": "vorqexa-site",
  "private": true,
  "scripts": {
    "build:docs": "python3 docs-src/build.py",
    "check": "node scripts/check.mjs && htmlhint index.html",
    "test": "playwright test"
  },
  "devDependencies": {
    "@playwright/test": "^1.48.0",
    "htmlhint": "^1.1.4"
  }
}
'''

FILES['playwright.config.js'] = r'''module.exports = {
  testDir: 'tests',
  webServer: {
    command: 'python3 -m http.server 4173',
    url: 'http://localhost:4173',
    reuseExistingServer: true,
  },
  use: { baseURL: 'http://localhost:4173' },
};
'''

FILES['tests/smoke.spec.js'] = r'''const { test, expect } = require('@playwright/test');

test('home page loads without errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('/');
  await expect(page.locator('h1').first()).toBeVisible();
  expect(errors).toEqual([]);
});

test('launch links point to the trading app', async ({ page }) => {
  await page.goto('/');
  const hrefs = await page.$$eval('a[data-launch]', (links) => links.map((a) => a.href));
  expect(hrefs.length).toBeGreaterThan(5);
  for (const h of hrefs) expect(h).toBe('https://dex.vorqexa.xyz/');
});

test('docs open from the Docs link and close with Escape', async ({ page }) => {
  await page.goto('/');
  await page.locator('a[data-vorqexa-docs]:visible').first().click();
  const overlay = page.locator('#vorqexa-docs-overlay');
  await expect(overlay).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(overlay).toBeHidden();
});

test('no sideways scrolling on a phone', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto('/');
  const extra = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(extra).toBeLessThanOrEqual(1);
});
'''

FILES['scripts/check.mjs'] = r'''import fs from 'node:fs';
import vm from 'node:vm';

let failed = false;
const fail = (msg) => { console.error('FAIL: ' + msg); failed = true; };
const ok = (msg) => console.log('ok:   ' + msg);

const html = fs.readFileSync('index.html', 'utf8');
const js = fs.readFileSync('script.js', 'utf8');

// 1) script.js parses
try { new vm.Script(js); ok('script.js syntax'); } catch (e) { fail('script.js syntax: ' + e.message); }

// 2) local files referenced by index.html exist
const refs = [...html.matchAll(/(?:src|href)="([^"#?]+)(?:[?#][^"]*)?"/g)].map((m) => m[1])
  .filter((u) => !/^(https?:|\/\/|mailto:|tel:|data:)/.test(u));
const missing = [...new Set(refs)].filter((u) => !fs.existsSync(u));
if (missing.length) fail('missing files: ' + missing.join(', ')); else ok('referenced files exist');

// 3) the app link lives in one place
const origin = (js.match(/var APP_ORIGIN\s*=\s*'([^']+)'/) || [])[1];
if (!origin) {
  fail('APP_ORIGIN not found in script.js');
} else {
  const launches = [...html.matchAll(/<a\b[^>]*\bdata-launch[^>]*>/g)].map((m) => (m[0].match(/href="([^"]*)"/) || [])[1]);
  const bad = launches.filter((h) => h !== origin + '/');
  if (launches.length && !bad.length) ok('launch links match APP_ORIGIN (' + launches.length + ')');
  else fail('launch links out of sync with APP_ORIGIN: ' + JSON.stringify(bad));
}

// 4) docs overlay is in sync with docs-src/docs.html
const blob = (js.match(/var docsData = "([^"]*)"/) || [])[1];
const src = fs.readFileSync('docs-src/docs.html');
if (!blob) fail('docsData not found in script.js');
else if (Buffer.from(blob, 'base64').equals(src)) ok('docs overlay in sync with docs-src/docs.html');
else fail('docs-src/docs.html and script.js differ: run npm run build:docs');

// 5) standalone docs page exists
if (fs.existsSync('docs/index.html')) ok('docs/index.html exists'); else fail('docs/index.html missing: run npm run build:docs');

process.exit(failed ? 1 : 0);
'''

FILES['.github/workflows/check.yml'] = r'''name: check
on:
  push:
  pull_request:
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm install
      - run: npm run check
      - run: npx playwright install --with-deps chromium
      - run: npm test
'''

FILES['_headers'] = r'''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: frame-ancestors 'none'
  Strict-Transport-Security: max-age=31536000
'''

FILES['vercel.json'] = r'''{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
        { "key": "Content-Security-Policy", "value": "frame-ancestors 'none'" },
        { "key": "Strict-Transport-Security", "value": "max-age=31536000" }
      ]
    }
  ]
}
'''

FILES['docs-src/build.py'] = r'''import re, base64, sys, os

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
'''

FILES['scripts/css_report.py'] = r'''import re, collections

css = open('styles.css', encoding='utf-8').read()
css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
css = re.sub(r'url\([^)]*\)', 'url()', css)

src = ''
for f in ('index.html', 'script.js', 'docs-src/docs.html'):
    t = open(f, encoding='utf-8').read()
    t = re.sub(r'var docsData = "[^"]*"', '', t)
    t = re.sub(r'data:[a-z/+-]+;base64,[A-Za-z0-9+/=]+', '', t)
    src += t + '\n'

classes = []
for m in re.finditer(r'\.([A-Za-z_][\w-]*)', css):
    if m.group(1) not in classes:
        classes.append(m.group(1))

unused = [c for c in classes if not re.search(r'(?<![\w-])' + re.escape(c) + r'(?![\w-])', src)]
print('Classes in styles.css:', len(classes))
print('Not found in index.html / script.js / docs (verify, then delete):', len(unused))
for c in unused:
    print('  .' + c)

heads = re.findall(r'(?m)^\s*([^@{}\n][^{}]*?)\s*\{', css)
count = collections.Counter(h.strip() for h in heads)
print('\nSelectors defined 3+ times (consolidate):')
for sel, n in count.most_common():
    if n < 3:
        break
    print('  %dx  %s' % (n, sel[:90]))
print('\n!important used:', css.count('!important'))
print('Old teal color still hard-coded (127,226,197):', css.count('127,226,197'))
print('\nNote: classes built from strings in JS may show as unused; check before deleting.')
'''

for path, text in FILES.items():
    if os.path.exists(path) and path not in OVERWRITE:
        print('exists, kept:', path)
        continue
    write(path, text)
    print('wrote:', path)

subprocess.run([sys.executable, 'docs-src/build.py'], check=True)
print('done')
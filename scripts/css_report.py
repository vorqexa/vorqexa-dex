import re, collections

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

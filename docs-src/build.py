import re, base64, sys
s = open('script.js', encoding='utf-8', newline='').read()
b = base64.b64encode(open('docs-src/docs.html', 'rb').read()).decode()
new, n = re.subn(r'(var docsData = ")[^"]*(")', lambda m: m.group(1) + b + m.group(2), s, count=1)
if n != 1:
    sys.exit('docsData not found')
open('script.js', 'w', encoding='utf-8', newline='').write(new)
d = base64.b64decode(re.search(r'var docsData = "([^"]*)"', new).group(1)).decode('utf-8')
print('script.js updated')
print('Orderly mentions in docs:', d.lower().count('orderly'))
print('journal section present:', 'id="journal"' in d)
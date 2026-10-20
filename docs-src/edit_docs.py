import re, sys
p = 'docs-src/docs.html'
h = open(p, encoding='utf-8', newline='').read()
problems = []

def sub(old, new):
    global h
    if h.count(old) != 1:
        problems.append(old[:70])
        return
    h = h.replace(old, new)

sub('<p>For transparency, the underlying trading infrastructure used by Vorqexa is provided by Orderly Network.</p>',
    '<p>For transparency, core trading services are provided by that third-party infrastructure rather than built and operated by Vorqexa itself.</p>')
sub('Orderly Network provides the underlying trading infrastructure used by the platform.',
    'That infrastructure runs behind the Vorqexa interface and supports the trading services you use.')
sub('<h3>Is Vorqexa the same thing as Orderly Network?</h3><p>No. Vorqexa is the product and user-facing trading platform. Orderly Network is the underlying infrastructure provider used by Vorqexa.</p>',
    '<h3>Is Vorqexa the same thing as its underlying infrastructure?</h3><p>No. Vorqexa is the product and user-facing trading platform. The underlying trading infrastructure is provided by a separate third-party provider.</p>')
sub('<p>Vorqexa uses Orderly Network as its underlying trading infrastructure. Any formal',
    '<p>Vorqexa uses established third-party trading infrastructure for core trading functionality. Any formal')
sub('<span>Perpetual trading, made clear. Underlying trading infrastructure provided by Orderly Network.</span>',
    '<span>Perpetual trading, made clear.</span>')

journal = ('<section id="journal"><h2>4. Built-in Trading Journal</h2>\n'
 '<h3>What It Is</h3>\n'
 '<p>Vorqexa includes a trading journal built directly into the app, so you can keep a record of your trading and review how you trade over time.</p>\n'
 '<h3>What You Can Do</h3>\n'
 '<p>Log your trades, track your emotional state alongside them, and review your PnL history, all inside the app.</p>\n'
 '<h3>Why Keep a Journal</h3>\n'
 '<p>Writing down what you traded and how you felt makes it easier to spot patterns in your own decisions, such as trades taken under pressure, and to review your results with a clear head.</p>\n'
 '<p>The journal is for your own review and does not constitute financial advice.</p>\n'
 '</section>\n\n')
sub('<section id="funds">', journal + '<section id="funds">')

sub('<h3>Is perpetual trading safe?</h3>',
    '<h3>Does Vorqexa have a trading journal?</h3><p>Yes. Vorqexa includes a built-in trading journal where you can log your trades, track your emotional state, and review your PnL history inside the app.</p>\n<h3>Is perpetual trading safe?</h3>')

# Sidebar link: only inside <nav class="side">
m = re.search(r'<nav class="side">.*?</nav>', h, re.S)
if not m:
    problems.append('sidebar nav not found')
else:
    nav = m.group(0)
    nav2 = nav.replace('<a href="#trading">Trading</a>',
                       '<a href="#trading">Trading</a>\n<a href="#journal">Trading journal</a>', 1)
    if nav2 == nav:
        problems.append('sidebar Trading link not found')
    else:
        h = h.replace(nav, nav2, 1)

if problems:
    print('NOTHING CHANGED. Problems:')
    for x in problems:
        print(' -', x)
    sys.exit(1)

n = 0
def renum(m):
    global n
    n += 1
    return m.group(1) + str(n) + '. '
h = re.sub(r'(<h2>)\d+\. ', renum, h)

open(p, 'w', encoding='utf-8', newline='').write(h)
print('docs edited, sections now numbered 1-%d' % n)
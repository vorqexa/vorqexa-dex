import sys, shutil

JS = 'script.js'
js = open(JS, encoding='utf-8', newline='').read()
if 'vqScopeDocsCss' in js:
    sys.exit('already applied, nothing changed')

HELPERS = r"""function vqScopeDocsCss(css){
    return css
      .replace(/:root\b/g, ':host')
      .replace(/(^|[\s,{};])html(?=\s*[,{])/g, '$1:host')
      .replace(/(^|[\s,{};])body(?=\s*[,{])/g, '$1.vq-docs-body');
  }
  function vqDocsMotion(overlay, shadow, content){
    var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var st = document.createElement('style');
    st.textContent = '.side a.is-active{color:var(--text);border-left-color:var(--accent);background:rgba(182,250,209,.07)}' +
      '.vq-docs-reveal{opacity:0;transform:translateY(18px);transition:opacity .48s ease,transform .48s cubic-bezier(.22,.61,.36,1);will-change:opacity,transform}' +
      '.vq-docs-reveal.vq-in{opacity:1;transform:none;will-change:auto}';
    shadow.appendChild(st);
    if (!('IntersectionObserver' in window)) return;

    var links = {};
    shadow.querySelectorAll('.side a[href^="#"]').forEach(function(a){ links[a.getAttribute('href').slice(1)] = a; });
    var spy = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (!e.isIntersecting || !links[e.target.id]) return;
        Object.keys(links).forEach(function(k){ links[k].classList.remove('is-active'); });
        links[e.target.id].classList.add('is-active');
      });
    }, {root: overlay, rootMargin: '-15% 0px -75% 0px', threshold: 0});
    shadow.querySelectorAll('section[id]').forEach(function(s){ if (links[s.id]) spy.observe(s); });

    if (calm) return;

    var revealed = 0;
    var items = Array.prototype.slice.call(content.querySelectorAll('.content > h1,.content > .lead,section > h2,section > h3,section > p,.card,.step,.note,.callout,table,.footer'));
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (!e.isIntersecting) return;
        revealed++;
        e.target.classList.add('vq-in');
        io.unobserve(e.target);
        setTimeout(function(t){ t.classList.remove('vq-docs-reveal', 'vq-in'); t.style.transitionDelay = ''; }, 800, e.target);
      });
    }, {root: overlay, rootMargin: '0px 0px -6% 0px', threshold: 0.05});
    items.forEach(function(el){
      el.classList.add('vq-docs-reveal');
      if (el.matches('.card,.step')){
        var idx = Array.prototype.indexOf.call(el.parentNode.children, el);
        el.style.transitionDelay = Math.min(idx * 60, 180) + 'ms';
      }
      io.observe(el);
    });
    overlay._vqEnsure = function(){
      if (revealed === 0) items.forEach(function(el){ el.classList.add('vq-in'); });
    };
  }
  function getDocsOverlay() {"""

OPEN_JS = """var vqCalm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!vqCalm) {
      overlay.style.transition = 'none';
      overlay.style.opacity = '0';
      overlay.style.transform = 'translateY(12px)';
    }
    overlay.style.display = 'block';
    if (!vqCalm) {
      void overlay.offsetWidth;
      overlay.style.transition = 'opacity .3s ease,transform .3s cubic-bezier(.22,.61,.36,1)';
      overlay.style.opacity = '1';
      overlay.style.transform = 'none';
    }
    setTimeout(function(){ if (overlay._vqEnsure) overlay._vqEnsure(); }, 900);"""

problems = []
def rep(old, new):
    global js
    c = js.count(old)
    if c != 1:
        problems.append('%s  (found %d times)' % (old[:70], c))
        return
    js = js.replace(old, new)

rep('function getDocsOverlay() {', HELPERS)
rep('background:#0b0f0d;overflow:auto;', 'background:#030504;overflow:auto;scroll-behavior:smooth;')
rep('st.textContent = node.textContent;', 'st.textContent = vqScopeDocsCss(node.textContent);')
rep("var content = document.createElement('div');", "var content = document.createElement('div');\n    content.className = 'vq-docs-body';")
rep('shadow.appendChild(content);', 'shadow.appendChild(content);\n    vqDocsMotion(overlay, shadow, content);')
rep("overlay.style.display = 'block';", OPEN_JS)

if problems:
    print('NOTHING CHANGED. Problems:')
    for p in problems:
        print(' -', p)
    sys.exit(1)

shutil.copy(JS, '/tmp/script.js.before-motion')
open(JS, 'w', encoding='utf-8', newline='').write(js)
print('script.js patched')
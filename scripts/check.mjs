import fs from 'node:fs';
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

# Vorqexa website

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

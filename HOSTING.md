# Enthermal™ Configurator — Hosting Handoff

A one-page guide for the web/hosting team. Covers what the app is, how to deploy it, and the gotchas that matter.

---

## What it is

The **LuxWall Enthermal™ Product Configurator** — a client-side technical sales tool for architects and specifiers. Users select glass configuration options and the app displays thermal performance metrics (U-value, SHGC, Tvis, R-value, OITC) plus visual cross-section and color renderings. Single-page, primarily a desktop tool.

- **Stack:** Vanilla HTML5 / CSS3 / JavaScript (ES6). No React, no build step, no npm, no server-side code.
- **Backend:** None required. This is a fully static site.
- **State:** No login, cookies, `localStorage`, analytics, or user-data collection. All data is read-only reference data shipped with the app.

---

## How to deploy

Host as a static site on any static host — S3 + CloudFront, Netlify, Vercel, GitHub Pages, Azure Static Web Apps, or a plain Nginx/Apache directory. No Node runtime or database needed.

**Deploy the entire directory, preserving the folder structure:**

```
/ (deploy root or subpath)
├── enthermal-configurator.html   ← entry point
└── data/
    ├── enthermal.json
    ├── enthermal-plus-inboard.json
    ├── enthermal-plus-outboard.json
    └── *.png                      ← product/sky images
```

---

## Critical gotchas

### 1. The `data/` folder must ship with the HTML ⚠️
The app is **not** a single self-contained file. On load it fetches three JSON files from the `data/` folder using **relative paths** (`data/enthermal.json`, etc.). If `data/` is missing or moved, **the app loads blank — no data appears, no obvious error.** Always deploy `data/` as a sibling of the HTML file.

### 2. Must be served over HTTP(S), not `file://`
Because of the `fetch()` calls, browsers block data loading over the `file://` protocol. Real hosting serves over `http(s)://`, so this is automatic — but **do not test by double-clicking the HTML file**; it will appear broken. Use the deployed URL or a local web server.

### 3. Only external dependency: Google Fonts
Loads "Plus Jakarta Sans" and "DM Sans" from the Google Fonts CDN. If a strict Content-Security-Policy is in place, allowlist `fonts.googleapis.com` and `fonts.gstatic.com`, or typography falls back to system fonts.

---

## Performance notes

Total payload is **~20 MB**, front-loaded on first page load.

| Asset | Size |
|---|---|
| `enthermal-plus-inboard.json` | ~4.5 MB |
| `enthermal-plus-outboard.json` | ~1.9 MB |
| 5 × PNG images (product/sky) | ~2.8 MB each (~14 MB total) |
| `enthermal.json` | ~71 KB |
| `enthermal-configurator.html` | ~102 KB |

Recommendations:
- **Enable gzip/Brotli compression.** The JSON compresses ~80–90%, cutting ~6 MB of data down to well under 1 MB. Biggest single win for first-load speed.
- **Set sensible Cache-Control headers** on the `data/` and image assets (they change infrequently).
- **Optimize the PNGs** if first-load performance matters (WebP conversion / resizing) — they're large and uncompressed.

---

## Open questions for the hosting team

- **Hosting target?** (CDN, static host, internal server) — confirms compression/caching are configurable.
- **Root domain or subpath?** (e.g. `luxwall.com/configurator/`) — relative paths support subpaths, but worth confirming.
- **Can you enable gzip/Brotli + Cache-Control** for `data/` and image assets?
- **Any CSP** that would block Google Fonts?

---

## Local preview (for testing before deploy)

From the project folder, run any static server, e.g.:

```
python -m http.server 8000
```

Then open `http://localhost:8000/enthermal-configurator.html`.

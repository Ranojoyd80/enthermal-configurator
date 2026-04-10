# Data Architecture — Enthermal Configurator

> Decisions and specifications for the data layer powering the configurator UI.

---

## 1. Data Storage

**External JSON files** loaded via `fetch()` at runtime. Three files served alongside the HTML:

| File | Product | Rows | Size |
|---|---|---|---|
| `data/enthermal.json` | Enthermal | ~84 | ~35 KB |
| `data/enthermal-plus-inboard.json` | Enthermal Plus (VIG inboard) | ~4,200 | ~2.2 MB |
| `data/enthermal-plus-outboard.json` | Enthermal Plus (VIG outboard) | ~1,750 | ~940 KB |

**Why external JSON instead of embedded JS arrays:**
- Data updates don't touch UI code — drop new JSON files, done
- Clean git history — data commits separated from UI commits
- Browser caches JSON — repeat visitors skip unchanged downloads
- ~6,000 rows embedded would bloat the HTML to ~800 KB

---

## 2. JSON Schema

See `ProductData/json-schema.md` for the full field reference.

**Enthermal:** 17 fields — outerLite, outerLowE, innerLite, totalThickness, performance metrics (uval, uvalIP, rval, shgc, tvis, routVis, tuv), color data (extL/A/B, intL/A/B)

**Enthermal Plus:** 21 fields — adds middleLite, middleLowE, innerLowE, gasFill

---

## 3. Fields Excluded from JSON

| Field | Reason |
|---|---|
| Product Type | Implicit per file |
| Comment | Not used in UI |
| NFRC IDs | Not displayed |
| tdwISO | Removed entirely |
| Manufacturer | JS lookup table (see below) |

---

## 4. Runtime Calculations (in HTML JS)

| Metric | Lookup Key | Notes |
|---|---|---|
| IGU Weight | Lite thicknesses | Simple lookup table |
| OITC / Rw | VIG lite thicknesses | Simple lookup table |
| Embodied Carbon | Hardcoded to **38.6** kg CO2e/m2 (GWP-Fossil, A1-A3) | Will eventually become a lookup keyed off IGU weight |

---

## 5. Coating Display Names

Three levels of coating name used in the UI:

| Context | Format | Example |
|---|---|---|
| JSON data (raw) | Full name with surface suffix | `LoE³ 366 S2` |
| Config panel dropdown | Manufacturer + product, no surface | `Cardinal LoE³ 366` |
| Summary bar & cross-section | Short name, no surface, no manufacturer | `LoE³ 366` |

**Short name rules by brand:**

| Raw Name Pattern | Short Name |
|---|---|
| LoE / LoE² / LoE³ / Quad LoE ... | Keep as-is minus surface |
| Solarban® ... | `Solarban` + model (strip ®) |
| COOL-LITE SKN 183 II ... | `SKN 183` |
| COOL-LITE XTREME 61-29 II ... | `XTREME 61-29` |
| ECLAZ II ... | `ECLAZ` |

**Manufacturer lookup:** A JS object in the HTML maps coating base names to manufacturers (Cardinal, Vitro, Saint-Gobain). If a coating loaded from JSON is not in the lookup, log `console.warn("Unknown manufacturer for coating: XYZ")`.

---

## 6. Data Flow — Filter Cascades

### Enthermal
Outer Thickness → Low-E Coating → Inner Thickness → **single row**

### Enthermal Plus — Inboard Placement
Outboard Thickness → Outboard Low-E Coating → Gas Fill (Argon/Air) → VIG Thickness → VIG Low-E Coating → Coating Surface (S4/S5) → **single row**

### Enthermal Plus — Outboard Placement
VIG Thickness → VIG Low-E Coating → Gas Fill (Argon/Air) → Inboard Thickness → Inboard Low-E Coating (always S5, no toggle) → **single row**

---

## 7. Data Update Procedure

1. Run PyWinCalc script → outputs 3 JSON files directly (see `ProductData/json-schema.md` for format)
2. Place JSON files in the `data/` folder alongside the HTML
3. No HTML changes needed for data-only updates
4. If new coatings or manufacturers appear → update the JS manufacturer lookup table in the HTML

---

## 8. Hosting & Testing

- **Production:** HTML + JSON files served from the same web host. `fetch()` uses relative paths.
- **Pre-launch testing:** GitHub Pages, Netlify Drop, or company staging server. All serve over HTTP so fetch works without CORS issues.
- **Local file://:** Not supported for fetch-based loading. Use a local server for testing (`python -m http.server`).

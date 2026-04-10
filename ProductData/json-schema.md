# JSON Schema for Enthermal Configurator

## Output Files

| File | Product | Rows |
|---|---|---|
| `data/enthermal.json` | Enthermal | ~84 |
| `data/enthermal-plus-inboard.json` | Enthermal Plus (VIG inboard) | ~4,200 |
| `data/enthermal-plus-outboard.json` | Enthermal Plus (VIG outboard) | ~1,750 |

Each file is a JSON array of objects. All numeric values must be stored as numbers, not strings.

---

## enthermal.json

```json
{
  "outerLite": "4mm Clear",
  "outerLowE": "LoE 180 S2",
  "innerLite": "Float Glass - 4mm",
  "totalThickness": 8.05,
  "uval": 0.4778,
  "uvalIP": 0.0842,
  "rval": 11.88,
  "shgc": 0.6332,
  "tvis": 0.7868,
  "routVis": 0.1532,
  "tuv": 0.2747,
  "extL": 46.23,
  "extA": -1.34,
  "extB": -5.55,
  "intL": 45.2,
  "intA": -0.5,
  "intB": -5.95
}
```

## enthermal-plus-inboard.json / enthermal-plus-outboard.json

```json
{
  "outerLite": "4mm Clear",
  "outerLowE": "LoE 180 S2",
  "middleLite": "4mm Clear",
  "middleLowE": "LoE 180 S4",
  "innerLite": "Float Glass - 4mm",
  "innerLowE": "",
  "gasFill": "Ar90",
  "totalThickness": 25.4,
  "uval": 0.3723,
  "uvalIP": 0.0656,
  "rval": 15.25,
  "shgc": 0.5117,
  "tvis": 0.691,
  "routVis": 0.2078,
  "tuv": 0.1245,
  "extL": 52.91,
  "extA": -2.37,
  "extB": -6.75,
  "intL": 51.41,
  "intA": -1.16,
  "intB": -7.39
}
```

---

## Field Reference

| Field | Type | Unit | Description |
|---|---|---|---|
| `outerLite` | string | — | Outer lite name and thickness as-is from IGDB/NFRC |
| `outerLowE` | string | — | Outer Low-E coating name including surface position (S2) |
| `middleLite` | string | — | Middle lite name and thickness (Plus only) |
| `middleLowE` | string | — | Middle Low-E coating including surface (S4). Empty string if none |
| `innerLite` | string | — | Inner lite name and thickness |
| `innerLowE` | string | — | Inner Low-E coating including surface (S5). Empty string if none |
| `gasFill` | string | — | Gas fill type: `"Ar90"` or `"Air"` (Plus only) |
| `totalThickness` | number | mm | Total IGU thickness |
| `uval` | number | W/m²K | U-value (NFRC, SI) |
| `uvalIP` | number | BTU/hr·ft²·°F | U-value (NFRC, IP) |
| `rval` | number | hr·ft²·°F/BTU | R-value (NFRC) |
| `shgc` | number | — | Solar Heat Gain Coefficient |
| `tvis` | number | — | Visible Transmittance |
| `routVis` | number | — | Exterior Visible Reflectance |
| `tuv` | number | — | UV Transmittance |
| `extL` | number | — | Exterior Reflected Color CIE L* |
| `extA` | number | — | Exterior Reflected Color CIE a* |
| `extB` | number | — | Exterior Reflected Color CIE b* |
| `intL` | number | — | Interior Reflected Color CIE L* |
| `intA` | number | — | Interior Reflected Color CIE a* |
| `intB` | number | — | Interior Reflected Color CIE b* |

---

## Notes

- Low-E coating names must include the surface suffix (S2, S4, S5) — the UI strips it at display time
- Preserve Unicode characters: ² ³ ® in coating names
- Empty Low-E fields must be empty strings `""`, not null
- The `gasFill` field uses `"Ar90"` for 90% Argon and `"Air"` for 100% Air
- Fields NOT included (handled elsewhere): Product Type, Comment, NFRC IDs, tdwISO, manufacturer, OITC, Rw, IGU Weight, Embodied Carbon

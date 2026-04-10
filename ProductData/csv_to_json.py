"""
Convert PyWinCalc CSV exports to JSON for the Enthermal Configurator.

Outputs:
  data/enthermal.json
  data/enthermal-plus-inboard.json
  data/enthermal-plus-outboard.json

Usage:
  python csv_to_json.py
"""

import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'data')

# CSV file paths
ENTHERMAL_CSV = os.path.join(SCRIPT_DIR, 'PyWinCalc_Enthermal_10-04-26.csv')
PLUS_INBOARD_CSV = os.path.join(SCRIPT_DIR, 'PyWinCalc_EnthermalPlus_Inboard_10-04-26.csv')
PLUS_OUTBOARD_CSV = os.path.join(SCRIPT_DIR, 'PyWinCalc_EnthermalPlus_Outboard_10-04-26.csv')


def parse_float(val):
    """Convert string to float, return None if empty."""
    val = val.strip()
    if not val:
        return None
    return float(val)


def normalize_string(val):
    """Normalize lite and coating name strings.

    Fixes two issues from the IGDB source data:
    1. Collapse double spaces to single (e.g. "Optigray®  6mm" -> "Optigray® 6mm")
    2. Normalize clear glass to "Xmm Clear" format:
       - "4 mm Clear" -> "4mm Clear"
       - "Clear  4mm" -> "4mm Clear"
    """
    import re
    # Collapse double spaces
    val = re.sub(r'  +', ' ', val)
    # "Clear 4mm" (reversed order) -> "4mm Clear"
    m = re.match(r'^Clear\s+(\d+mm)$', val)
    if m:
        return m.group(1) + ' Clear'
    # "4 mm Clear" (space before mm) -> "4mm Clear"
    m = re.match(r'^(\d+)\s+mm\s+Clear$', val)
    if m:
        return m.group(1) + 'mm Clear'
    return val


def parse_lite_thicknesses_from_comment(comment):
    """Extract nominal thickness for each lite from the Comment field.

    Comment formats:
      Enthermal:      "SB60 4mm / Vacuum 0.25mm / Clear 4mm"
      Plus Inboard:   "C180 4mm / Argon 13.36mm / SB60 4mm / Vacuum 0.25mm / Clear 4mm"
      Plus Outboard:  "SB60 4mm / Vacuum 0.25mm / Clear 4mm / Argon 13.36mm / C180 4mm"

    Returns a list of lite thicknesses in order (excluding Vacuum and Argon segments).
    """
    import re
    parts = [p.strip() for p in comment.split('/')]
    thicknesses = []
    for part in parts:
        # Skip Vacuum, Argon, and Air gap segments
        low = part.lower()
        if low.startswith('vacuum') or low.startswith('argon') or low.startswith('air'):
            continue
        # Match nominal thickness: "SB60 4mm" -> 4, "Clear 6mm" -> 6
        # Use word-boundary match to avoid picking up decimals like "13.45mm"
        m = re.search(r'(?<!\.)(\d+)mm', part)
        if m:
            thicknesses.append(int(m.group(1)))
        else:
            thicknesses.append(None)
    return thicknesses


def fix_clear_float_glass(lite_name, nominal_mm):
    """Replace 'Clear Float Glass' with a name that includes the nominal thickness."""
    if lite_name == 'Clear Float Glass' and nominal_mm is not None:
        return f'Clear Float Glass - {nominal_mm}mm'
    return lite_name


def convert_enthermal(csv_path):
    """Convert Enthermal CSV to JSON array."""
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Parse nominal thicknesses from Comment: "SB60 4mm / Vacuum 0.25mm / Clear 4mm"
            # Gives [outer_mm, inner_mm]
            thicknesses = parse_lite_thicknesses_from_comment(r['Comment'])
            inner_mm = thicknesses[1] if len(thicknesses) > 1 else None
            inner_lite = normalize_string(r['Inner Lite (Name_Thickness mm)'].strip())
            inner_lite = fix_clear_float_glass(inner_lite, inner_mm)
            rows.append({
                'outerLite': normalize_string(r['Outer Lite (Name_Thickness mm)'].strip()),
                'outerLowE': normalize_string(r['Outer Lite Low-E'].strip()),
                'innerLite': inner_lite,
                'totalThickness': parse_float(r['Total Thickness (mm)']),
                'uval': parse_float(r['U-value NFRC (W/m²K)']),
                'uvalIP': parse_float(r['U-value NFRC (BTU/hrftF)']),
                'rval': parse_float(r['R-value NFRC']),
                'shgc': parse_float(r['SHGC']),
                'tvis': parse_float(r['Tvis (Visible Transmittance)']),
                'routVis': parse_float(r['Exterior Visible Reflectance']),
                'tuv': parse_float(r['T-UV']),
                'extL': parse_float(r['Exterior Reflected Color L*']),
                'extA': parse_float(r['Exterior Reflected Color a*']),
                'extB': parse_float(r['Exterior Reflected Color b*']),
                'intL': parse_float(r['Interior Reflected Color L*']),
                'intA': parse_float(r['Interior Reflected Color a*']),
                'intB': parse_float(r['Interior Reflected Color b*']),
            })
    return rows


def convert_plus(csv_path):
    """Convert Enthermal Plus CSV to JSON array."""
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Parse nominal thicknesses from Comment:
            #   Inboard:  "C180 4mm / Argon 13.36mm / SB60 4mm / Vacuum 0.25mm / Clear 4mm"
            #             -> [outer, middle, inner]
            #   Outboard: "SB60 4mm / Vacuum 0.25mm / Clear 4mm / Argon 13.36mm / C180 4mm"
            #             -> [outer, middle, inner]
            thicknesses = parse_lite_thicknesses_from_comment(r['Comment'])
            outer_mm = thicknesses[0] if len(thicknesses) > 0 else None
            middle_mm = thicknesses[1] if len(thicknesses) > 1 else None
            inner_mm = thicknesses[2] if len(thicknesses) > 2 else None

            outer_lite = fix_clear_float_glass(
                normalize_string(r['Outer Lite (Name_Thickness mm)'].strip()), outer_mm)
            middle_lite = fix_clear_float_glass(
                normalize_string(r['Middle Lite (Name_Thickness mm)'].strip()), middle_mm)
            inner_lite = fix_clear_float_glass(
                normalize_string(r['Inner Lite (Name_Thickness mm)'].strip()), inner_mm)
            rows.append({
                'outerLite': outer_lite,
                'outerLowE': normalize_string(r['Outer Lite Low-E'].strip()),
                'middleLite': middle_lite,
                'middleLowE': normalize_string(r['Middle Lite Low-E'].strip()),
                'innerLite': inner_lite,
                'innerLowE': normalize_string(r['Inner Lite Low-E'].strip()),
                'gasFill': r['Gas Fill'].strip(),
                'totalThickness': parse_float(r['Total Thickness (mm)']),
                'uval': parse_float(r['U-value NFRC (W/m²K)']),
                'uvalIP': parse_float(r['U-value NFRC (BTU/hrftF)']),
                'rval': parse_float(r['R-value NFRC']),
                'shgc': parse_float(r['SHGC']),
                'tvis': parse_float(r['Tvis (Visible Transmittance)']),
                'routVis': parse_float(r['Exterior Visible Reflectance']),
                'tuv': parse_float(r['T-UV']),
                'extL': parse_float(r['Exterior Reflected Color L*']),
                'extA': parse_float(r['Exterior Reflected Color a*']),
                'extB': parse_float(r['Exterior Reflected Color b*']),
                'intL': parse_float(r['Interior Reflected Color L*']),
                'intA': parse_float(r['Interior Reflected Color a*']),
                'intB': parse_float(r['Interior Reflected Color b*']),
            })
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Convert Enthermal
    enthermal = convert_enthermal(ENTHERMAL_CSV)
    out_path = os.path.join(OUTPUT_DIR, 'enthermal.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(enthermal, f, ensure_ascii=False, indent=2)
    print(f'enthermal.json: {len(enthermal)} rows')

    # Convert Plus Inboard
    plus_inboard = convert_plus(PLUS_INBOARD_CSV)
    out_path = os.path.join(OUTPUT_DIR, 'enthermal-plus-inboard.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(plus_inboard, f, ensure_ascii=False, indent=2)
    print(f'enthermal-plus-inboard.json: {len(plus_inboard)} rows')

    # Convert Plus Outboard
    plus_outboard = convert_plus(PLUS_OUTBOARD_CSV)
    out_path = os.path.join(OUTPUT_DIR, 'enthermal-plus-outboard.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(plus_outboard, f, ensure_ascii=False, indent=2)
    print(f'enthermal-plus-outboard.json: {len(plus_outboard)} rows')

    # Report all unique coatings found
    all_coatings = set()
    for row in enthermal:
        all_coatings.add(row['outerLowE'])
    for row in plus_inboard + plus_outboard:
        all_coatings.add(row['outerLowE'])
        if row['middleLowE']:
            all_coatings.add(row['middleLowE'])
        if row['innerLowE']:
            all_coatings.add(row['innerLowE'])

    print(f'\nUnique coatings found ({len(all_coatings)}):')
    for c in sorted(all_coatings):
        print(f'  {c}')


if __name__ == '__main__':
    main()

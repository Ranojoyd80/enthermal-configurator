#!/usr/bin/env python3
"""Phase 4: Convert anchor PNG renders -> lossless WebP for the app.

Source PNGs (Blender, 2075x1550) live OUTSIDE the repo, one folder per sky:
  <SRC>/ClearSky_AnchorRenders/Clear_Anchor0001..0137.png
  <SRC>/CloudySky_AnchorRenders/Cloudy_Anchor0001..0137.png
  <SRC>/Overcast_AnchorRenders/Overcast_Anchor0001..0137.png

Mapping: Blender frame N (Anchor NNNN) -> per-config cid = N-1.
Output: App_Data/Anchor_Renders/{Clear,Overcast,Cloudy}/anchor_<cid>.webp
        cid zero-padded to >=2 digits (0->"00", 5->"05", 135->"135").

Lossless only (lossy visibly degrades glass). Verifies pixel-identical after save.
"""
import sys
from pathlib import Path
from PIL import Image, ImageChops

SRC = Path(r"C:\Users\14084\Documents\Rhino_GH_Files\Office_RenderingModel\AnchorRenders")
DST = Path(__file__).resolve().parents[2] / "App_Data" / "Anchor_Renders"

# (source subfolder, source filename prefix, destination folder name)
SKIES = [
    ("ClearSky_AnchorRenders",  "Clear",    "Clear"),
    ("CloudySky_AnchorRenders", "Cloudy",   "Cloudy"),
    ("Overcast_AnchorRenders",  "Overcast", "Overcast"),
]
N_FRAMES = 137  # frames 0001..0137 -> cid 0..136


def main():
    total, failures = 0, []
    for sub, prefix, dstname in SKIES:
        srcdir = SRC / sub
        dstdir = DST / dstname
        dstdir.mkdir(parents=True, exist_ok=True)
        if not srcdir.is_dir():
            sys.exit(f"ERROR: missing source folder {srcdir}")
        for frame in range(1, N_FRAMES + 1):
            cid = frame - 1
            png = srcdir / f"{prefix}_Anchor{frame:04d}.png"
            webp = dstdir / f"anchor_{cid:02d}.webp"
            if not png.is_file():
                sys.exit(f"ERROR: missing {png}")
            with Image.open(png) as im:
                im = im.convert("RGB")
                im.save(webp, "WEBP", lossless=True, method=6)
                # verify pixel-identical
                with Image.open(webp) as out:
                    diff = ImageChops.difference(im, out.convert("RGB")).getbbox()
                    if diff is not None:
                        failures.append(str(webp))
            total += 1
            if total % 40 == 0:
                print(f"  ...{total}/{N_FRAMES*len(SKIES)}")
        print(f"[{dstname}] {N_FRAMES} files -> {dstdir}")
    print(f"\nDone: {total} WebP written.")
    if failures:
        sys.exit(f"PIXEL MISMATCH in {len(failures)} files:\n" + "\n".join(failures))
    print("All files verified pixel-identical to source PNG.")


if __name__ == "__main__":
    main()

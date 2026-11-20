#!/usr/bin/env python3
"""Download a public boundary outline for the `map` scene (geoBoundaries, CC BY; cite it in the slide).

  geo.py <ISO3> [--level ADM0|ADM1|ADM2] [--name REGEX] -o <deck>/assets/<file>.geojson

--name keeps only the units whose name matches (e.g. a region). Prints the attribution to put in
the slide's source note.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

API = "https://www.geoboundaries.org/api/current/gbOpen/{iso}/{level}/"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iso3")
    ap.add_argument("--level", default="ADM1")
    ap.add_argument("--name")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args(argv)
    meta = json.loads(urllib.request.urlopen(API.format(iso=a.iso3.upper(), level=a.level), timeout=60).read())
    geo = json.loads(urllib.request.urlopen(meta["simplifiedGeometryGeoJSON"], timeout=120).read())
    if a.name:
        rx = re.compile(a.name, re.I)
        geo["features"] = [f for f in geo["features"] if rx.search(str(f["properties"].get("shapeName", "")))]
        if not geo["features"]:
            sys.exit(f"no unit matches {a.name!r}")
    for f in geo["features"]:   # round coordinates: smaller file, same drawing
        def r(c):
            return [r(x) for x in c] if isinstance(c[0], list) else [round(c[0], 4), round(c[1], 4)]
        f["geometry"]["coordinates"] = r(f["geometry"]["coordinates"])
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(geo, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out} ({len(geo['features'])} units)")
    print(f"source note: geoBoundaries ({meta.get('boundarySource', '')}), {meta.get('boundaryLicense', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

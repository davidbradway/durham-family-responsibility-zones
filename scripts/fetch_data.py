"""Download map layers from public sources and write them as GeoJSON to site/data/.

Uses only the Python standard library so it runs on a bare GitHub Actions runner.
Usage: python scripts/fetch_data.py
"""

import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "site" / "data"
DURHAM = "https://webgis2.durhamnc.gov/server/rest/services"
BIKEPED = f"{DURHAM}/ProjectServices/Trans_ExistingFutureBikePedFacilities/MapServer"
EDUCATION = f"{DURHAM}/PublicServices/Education/MapServer"
USER_AGENT = "durham-family-responsibility-zones (+https://github.com/davidbradway/durham-family-responsibility-zones)"

# id -> source definition. "arcgis" layers are paged through the REST query endpoint.
LAYERS = {
    "frz": {
        "kind": "kmz",
        "title": "DPS Family Responsibility Zones",
        "url": "https://www.google.com/maps/d/kml?mid=1VBBGZwnFRggYWzlq4T1NCGyMiZeaDkc",
        "source_page": "https://www.google.com/maps/d/viewer?mid=1VBBGZwnFRggYWzlq4T1NCGyMiZeaDkc",
    },
    # The Education service adds a layer per school year, e.g. "School Districts (2026-2027)".
    # "latest" picks the newest dated layer whose name starts with the given prefix.
    "school_districts": {
        "kind": "arcgis",
        "title": "DPS School Assignment Zones",
        "service": EDUCATION,
        "latest": "School Districts",
        "out_fields": "name,shortname,type,region,calendar,choice",
    },
    "schools": {
        "kind": "arcgis",
        "title": "DPS Schools",
        "service": EDUCATION,
        "latest": "Educational Facilities",
        "where": "agency = 'Durham Public Schools'",
        "out_fields": "name,factype,fulladdr,phone,agencyurl,grades",
    },
    "existing_ped": {
        "kind": "arcgis",
        "title": "Existing Pedestrian Facilities",
        "url": f"{BIKEPED}/0",
        "out_fields": "On_Road,From_Road,To_Road,Facility_Type,Simplified_Facilities,Date_Completed_Year",
    },
    "future_ped": {
        "kind": "arcgis",
        "title": "Future Pedestrian Facilities",
        "url": f"{BIKEPED}/2",
        "out_fields": "Project_Name,Project_ID,On_Road,From_Road,To_Road,Facility_Type_Section,Phase_Status,Est_Construction_Comp_Date,Simplified_Facilities",
    },
    "future_bike": {
        "kind": "arcgis",
        "title": "Future Bike Facilities",
        "url": f"{BIKEPED}/3",
        "out_fields": "Project_Name,Project_ID,On_Road,From_Road,To_Road,Facility_Type_Section,Phase_Status,Est_Construction_Comp_Date,Simplified_Facilities",
    },
    "existing_bike": {
        "kind": "arcgis",
        "title": "Existing Bike Facilities",
        "url": f"{BIKEPED}/4",
        "out_fields": "On_Road,From_Road,To_Road,Facility_Type,Simplified_Facilities,Date_Completed_Year",
    },
    "paper_streets": {
        "kind": "arcgis",
        "title": "Paper Streets",
        "url": f"{DURHAM}/ProjectServices/BMS_PaperStreets/MapServer/3",
        "out_fields": "strname,length,width_1,stream,floodzone,utilitylin,slope",
    },
    "city_limits": {
        "kind": "arcgis",
        "title": "Durham City Limits",
        "url": f"{DURHAM}/PublicServices/Administrative/MapServer/1",
        "out_fields": "",
        "max_offset": 0.00003,  # degrees (~3 m); the raw boundary is ~1 MB
    },
}


def get(url, params=None, retries=3):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))


def resolve_latest(layer):
    """Point layer["url"] at the newest "<prefix> (YYYY-YYYY)" layer and set layer["school_year"]."""
    service = json.loads(get(layer["service"], {"f": "json"}))
    pattern = re.compile(rf"^{re.escape(layer['latest'])} \((\d{{4}})-(\d{{4}})\)$")
    dated = []
    for lyr in service.get("layers", []):
        m = pattern.match(lyr["name"])
        if m:
            dated.append((int(m.group(1)), int(m.group(2)), lyr["id"]))
    if not dated:
        raise RuntimeError(f"no dated '{layer['latest']}' layers in {layer['service']}")
    start, end, layer_id = max(dated)
    layer["url"] = f"{layer['service']}/{layer_id}"
    layer["school_year"] = f"{start}-{str(end)[-2:]}"


def fetch_arcgis(layer):
    """Page through an ArcGIS MapServer layer and return a GeoJSON FeatureCollection."""
    meta = json.loads(get(layer["url"], {"f": "json"}))
    page_size = min(meta.get("maxRecordCount") or 1000, 2000)
    features, offset = [], 0
    while True:
        data = json.loads(
            get(
                f"{layer['url']}/query",
                {
                    "where": layer.get("where", "1=1"),
                    "outFields": layer["out_fields"],
                    "returnGeometry": "true",
                    "outSR": 4326,
                    "geometryPrecision": 5,  # ~1 m
                    "maxAllowableOffset": layer.get("max_offset", ""),
                    "orderByFields": meta.get("objectIdField") or "OBJECTID",
                    "resultOffset": offset,
                    "resultRecordCount": page_size,
                    "f": "geojson",
                },
            )
        )
        if "error" in data:
            raise RuntimeError(f"{layer['url']}: {data['error']}")
        batch = data.get("features", [])
        features.extend(batch)
        if len(batch) < page_size and not data.get("exceededTransferLimit"):
            break
        offset += len(batch)
    return {"type": "FeatureCollection", "features": features}


KML_NS = {"k": "http://www.opengis.net/kml/2.2"}


def _coords(text):
    pts = []
    for tok in text.split():
        lon, lat, *_ = (float(v) for v in tok.split(","))
        pts.append([round(lon, 5), round(lat, 5)])
    return pts


def _kml_geometries(el):
    for poly in el.iter(f"{{{KML_NS['k']}}}Polygon"):
        rings = [_coords(poly.find("k:outerBoundaryIs/k:LinearRing/k:coordinates", KML_NS).text)]
        for inner in poly.findall("k:innerBoundaryIs/k:LinearRing/k:coordinates", KML_NS):
            rings.append(_coords(inner.text))
        yield {"type": "Polygon", "coordinates": rings}
    for line in el.iter(f"{{{KML_NS['k']}}}LineString"):
        yield {"type": "LineString", "coordinates": _coords(line.find("k:coordinates", KML_NS).text)}
    for pt in el.iter(f"{{{KML_NS['k']}}}Point"):
        yield {"type": "Point", "coordinates": _coords(pt.find("k:coordinates", KML_NS).text)[0]}


def _strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def fetch_kmz(layer):
    """Download a KMZ (e.g. a Google My Maps export) and convert its placemarks to GeoJSON."""
    with zipfile.ZipFile(io.BytesIO(get(layer["url"]))) as z:
        kml_name = next(n for n in z.namelist() if n.endswith(".kml"))
        root = ET.fromstring(z.read(kml_name))
    features = []
    for folder in root.iter(f"{{{KML_NS['k']}}}Folder"):
        folder_name = folder.findtext("k:name", default="", namespaces=KML_NS)
        for pm in folder.findall("k:Placemark", KML_NS):
            props = {
                "name": (pm.findtext("k:name", default="", namespaces=KML_NS) or "").strip(),
                "description": _strip_html(pm.findtext("k:description", default="", namespaces=KML_NS)),
                "folder": folder_name,
            }
            for d in pm.findall("k:ExtendedData/k:Data", KML_NS):
                props[d.get("name")] = d.findtext("k:value", default="", namespaces=KML_NS)
            geoms = list(_kml_geometries(pm))
            if not geoms:
                continue
            geometry = geoms[0] if len(geoms) == 1 else {"type": "GeometryCollection", "geometries": geoms}
            features.append({"type": "Feature", "properties": props, "geometry": geometry})
    return {"type": "FeatureCollection", "features": features}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    failed = []
    for layer_id, layer in LAYERS.items():
        try:
            if "latest" in layer:
                resolve_latest(layer)
            fc = fetch_arcgis(layer) if layer["kind"] == "arcgis" else fetch_kmz(layer)
        except Exception as e:  # keep the last good copy of this layer
            print(f"FAILED {layer_id}: {e}", file=sys.stderr)
            failed.append(layer_id)
            continue
        if not fc["features"]:
            print(f"FAILED {layer_id}: no features returned", file=sys.stderr)
            failed.append(layer_id)
            continue
        out = OUT_DIR / f"{layer_id}.geojson"
        text = json.dumps(fc, separators=(",", ":"))
        prev = manifest.get(layer_id, {})
        changed = (
            not out.exists()
            or out.read_text(encoding="utf-8") != text
            or prev.get("school_year") != layer.get("school_year")
        )
        if changed:
            out.write_text(text, encoding="utf-8")
        manifest[layer_id] = {
            "title": layer["title"],
            "source": layer.get("source_page", layer["url"]),
            "features": len(fc["features"]),
            "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d") if changed else prev.get("updated"),
        }
        if "school_year" in layer:
            manifest[layer_id]["school_year"] = layer["school_year"]
        print(f"{layer_id}: {len(fc['features'])} features ({len(text) // 1024} KB){' changed' if changed else ''}")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Fail the run only if every layer failed; partial failures keep the old files.
    if len(failed) == len(LAYERS):
        sys.exit(1)


if __name__ == "__main__":
    main()

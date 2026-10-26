# Durham Family Responsibility Zones

An interactive [Leaflet](https://leafletjs.com/) and [OpenStreetMap](https://www.openstreetmap.org/) map of
Durham Public Schools (DPS) **Family Responsibility Zones (FRZs)**, school assignment zones, and
walking and biking infrastructure in Durham, NC.

It is for DPS parents, prospective Durham families, and walk/bike advocates such as Bike Durham.
It shows which homes fall inside an FRZ (no DPS bus service), how a family could walk or bike
to school, and where gaps in the network block safe routes.

**Live map:** https://davidbradway.github.io/durham-family-responsibility-zones/

This project replaces an earlier
[ArcGIS Online version](https://dukeuniv.maps.arcgis.com/apps/instant/basic/index.html?appid=ae91fb85c4e14e628348263be7287bbc).

## Layers

- DPS Family Responsibility Zones, with a sidebar listing each school that has one (click to zoom)
- Elementary, middle, and high school assignment zones (newest school year Durham publishes, shown on the map)
- DPS school locations
- Existing sidewalks and paths (off by default) and future pedestrian facilities
- Existing and future bike facilities
- Paper streets (platted but unbuilt rights-of-way that could become connections)
- Durham city limits

See [DATA.md](DATA.md) for sources, processing, and attribution.

## How it works

```
scripts/fetch_data.py   ->  site/data/*.geojson  ->  site/ (static Leaflet page)  ->  GitHub Pages
```

- `scripts/fetch_data.py` downloads every layer from public City of Durham ArcGIS services and
  the DPS Google My Maps. It uses only the Python standard library.
- `.github/workflows/update-and-deploy.yml` runs the script every Monday (or on demand), commits
  any data changes, and deploys `site/` to GitHub Pages. Pushes to `main` redeploy without refetching.
- If a source is down, that layer keeps its last committed copy.

## Run locally

```sh
python scripts/fetch_data.py         # optional: refresh data
python -m http.server -d site 8000   # then open http://localhost:8000
```

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Code: [MIT](LICENSE). Data: see [DATA.md](DATA.md). Each layer keeps its publisher's terms.

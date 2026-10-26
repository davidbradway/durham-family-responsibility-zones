# Data sources and attribution

The map data in `site/data/` is downloaded from public sources by
[`scripts/fetch_data.py`](scripts/fetch_data.py) and refreshed weekly by GitHub Actions.
This repository does not own the data. Each layer keeps the terms of its publisher.
See `site/data/manifest.json` for feature counts and the date each layer last changed.

| Layer | File | Publisher | Source |
|---|---|---|---|
| DPS Family Responsibility Zones | `frz.geojson` | Durham Public Schools | [Google My Maps](https://www.google.com/maps/d/viewer?mid=1VBBGZwnFRggYWzlq4T1NCGyMiZeaDkc) (KMZ export) |
| School Districts (newest school year) | `school_districts.geojson` | City of Durham / DPS | [Education MapServer](https://webgis2.durhamnc.gov/server/rest/services/PublicServices/Education/MapServer), newest `School Districts (YYYY-YYYY)` layer |
| Educational Facilities (newest school year), DPS only | `schools.geojson` | City of Durham | [Education MapServer](https://webgis2.durhamnc.gov/server/rest/services/PublicServices/Education/MapServer), newest `Educational Facilities (YYYY-YYYY)` layer |
| Existing Pedestrian Facilities | `existing_ped.geojson` | City of Durham Transportation | [Trans_ExistingFutureBikePedFacilities/0](https://webgis2.durhamnc.gov/server/rest/services/ProjectServices/Trans_ExistingFutureBikePedFacilities/MapServer/0) |
| Future Pedestrian Facilities | `future_ped.geojson` | City of Durham Transportation | […/2](https://webgis2.durhamnc.gov/server/rest/services/ProjectServices/Trans_ExistingFutureBikePedFacilities/MapServer/2) |
| Future Bike Facilities | `future_bike.geojson` | City of Durham Transportation | […/3](https://webgis2.durhamnc.gov/server/rest/services/ProjectServices/Trans_ExistingFutureBikePedFacilities/MapServer/3) |
| Existing Bike Facilities | `existing_bike.geojson` | City of Durham Transportation | […/4](https://webgis2.durhamnc.gov/server/rest/services/ProjectServices/Trans_ExistingFutureBikePedFacilities/MapServer/4) |
| Paper Streets | `paper_streets.geojson` | City of Durham BMS / Public Works | [BMS_PaperStreets/MapServer/3](https://webgis2.durhamnc.gov/server/rest/services/ProjectServices/BMS_PaperStreets/MapServer/3) |
| City Limits | `city_limits.geojson` | City of Durham | [Administrative/MapServer/1](https://webgis2.durhamnc.gov/server/rest/services/PublicServices/Administrative/MapServer/1) |
| Basemap | n/a | OpenStreetMap contributors | [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) (ODbL) |

## Processing

- School layers: Durham adds one layer per school year to the Education service. The script picks the newest dated layer and records its year (for example `2026-27`) in `manifest.json`. The map then shows that year in the header, the layer names, and the popups. The undated "Current Year" and "Next Year" layers are skipped because they don't say which year they cover.
- ArcGIS layers are queried as GeoJSON in WGS 84 with coordinates rounded to 5 decimal places (about 1 m), and only the fields used in popups are kept.
- The city limits boundary is simplified to about 3 m.
- The FRZ KMZ is converted to GeoJSON. Placemark names, descriptions, and folder names become properties.

## Related resources

- [Durham Public School Travel Maps 2025](https://www.durhamnc.gov/5417/Durham-Public-School-Travel-Maps-2025)
- [Way to Go Durham: Ways to Get to School](https://waytogodurham.com/project/ways-to-get-to-school/)
- [Durham Bike and Pedestrian Facilities (Experience app)](https://experience.arcgis.com/experience/dca2cf0d57f443d9971c8900c8ab9df1/)
- [Durham Open Data Portal](https://live-durhamnc.opendata.arcgis.com/)

## Disclaimer

This map is an independent project for personal use, research, and planning discussion.
It is not an official product of Durham Public Schools or the City of Durham. For official
school assignment and transportation eligibility, contact DPS.

# Plan

## Goal

Rebuild the ArcGIS Online FRZ map as an open Leaflet + OpenStreetMap site on GitHub Pages,
with data that refreshes from authoritative public sources automatically.

**Audience:** DPS parents, prospective Durham families, and walk/bike advocates (Bike Durham).

## Phase 1: Parity with the ArcGIS map (this commit)

- [x] Find live public sources for every layer in the original web map
  - FRZ: the DPS Google My Maps KMZ export (22 zones + 21 school pins), matching the Jan 2025 copy on ArcGIS Online by name.
  - Bike/ped: `Trans_ExistingFutureBikePedFacilities`, the service behind Durham's Experience app
  - Paper streets: `BMS_PaperStreets/MapServer/3`
- [x] Add school assignment zones, always using the newest dated year from the Education service (now 2026–27), with the year shown on the map
- [x] Fetch script using only the standard library, keeping the last good copy when a source fails
- [x] Static Leaflet page with a layer switcher, popups, and a legend; sidewalks off by default
- [x] Weekly GitHub Action to fetch data, commit it, and deploy to Pages
- [x] Create the GitHub repo and enable Pages (source: GitHub Actions)
- [ ] Visual QA against the ArcGIS map

## Phase 2: Usability

- [ ] Address search: which FRZ and assignment zone contains this address? (Nominatim, or Durham's Composite_Address_Locator)
- [ ] Link schools to their DPS travel map PDFs
- [ ] Optionally compare with the previous year's assignment zones to show boundary changes
- [ ] Vector tiles or per-zoom loading if the 6.8 MB sidewalk layer feels slow on phones

## Phase 3: Planning tools

- Deferred: barrier catalog (Erik L's idea, crowd-sourced barrier data). Not planned for now.
- [ ] Gap analysis: sidewalk coverage inside each FRZ and assignment zone
- [ ] Share with Bike Durham and DPS parent groups; also Durham CAN (Bob Kruhm), the UNC researchers, and the Walk+Bike plan update team

## Open questions

- Does DPS have an FRZ update for 2025–26 or 2026–27 that is not yet in the My Maps?

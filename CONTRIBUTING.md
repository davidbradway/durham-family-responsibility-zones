# Contributing

Thanks for your interest! This is a small volunteer project, so keep changes focused.

- **Data problems** (a missing sidewalk, an outdated zone): open an issue. Most layers come from
  the City of Durham or DPS, so a fix may also need to go upstream to them. See [DATA.md](DATA.md).
- **New layers**: add an entry to `LAYERS` in `scripts/fetch_data.py` and to `OVERLAYS` in
  `site/app.js`, and add a row to `DATA.md`.
- **Code**: there is no build step. Edit `site/` directly and test with
  `python -m http.server -d site 8000`.

Do not commit data files by hand unless they come from `scripts/fetch_data.py`.

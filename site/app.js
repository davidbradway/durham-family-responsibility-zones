// Durham Family Responsibility Zones map.
// Layer data lives in data/*.geojson and is refreshed by scripts/fetch_data.py.

const map = L.map("map", { preferCanvas: true }).setView([35.994, -78.899], 12);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

map.attributionControl.addAttribution(
  'Data: <a href="https://www.durhamnc.gov/">City of Durham</a>, <a href="https://www.dpsnc.net/">DPS</a>'
);

const COLORS = {
  frz: "#e66101",
  elementary: "#5e3c99",
  middle: "#1b7837",
  high: "#b2182b",
  existingPed: "#2166ac",
  futurePed: "#67a9cf",
  existingBike: "#1a9850",
  futureBike: "#91cf60",
  paper: "#d01c8b",
  city: "#555",
};

function esc(v) {
  return String(v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Build a popup table from the listed [label, property] pairs, skipping empty values.
function popupTable(title, props, fields) {
  const rows = fields
    .filter(([, key]) => props[key] !== null && props[key] !== undefined && props[key] !== "")
    .map(([label, key]) => `<tr><th>${esc(label)}</th><td>${esc(props[key])}</td></tr>`)
    .join("");
  return `<h3>${esc(title || "")}</h3>${rows ? `<table>${rows}</table>` : ""}`;
}

async function loadJSON(name) {
  const resp = await fetch(`data/${name}`);
  if (!resp.ok) throw new Error(`${name}: ${resp.status}`);
  return resp.json();
}

const lineStyle = (color, dashed) => ({ color, weight: 3, opacity: 0.9, dashArray: dashed ? "6 6" : null });

// Overlays in the order they appear in the layer control. `on` = visible at load.
const OVERLAYS = [
  {
    file: "city_limits.geojson",
    label: "Durham city limits",
    on: false,
    options: { style: { color: COLORS.city, weight: 2, fill: false, dashArray: "4 4" }, interactive: false },
  },
  {
    file: "school_districts.geojson",
    label: "Elementary assignment zones",
    on: true,
    filter: (f) => /^Elementary/.test(f.properties.type || ""),
    color: COLORS.elementary,
  },
  {
    file: "school_districts.geojson",
    label: "Middle assignment zones",
    on: false,
    filter: (f) => /^Middle/.test(f.properties.type || ""),
    color: COLORS.middle,
  },
  {
    file: "school_districts.geojson",
    label: "High / secondary zones",
    on: false,
    filter: (f) => /^(High|Secondary)/.test(f.properties.type || ""),
    color: COLORS.high,
  },
  {
    file: "frz.geojson",
    label: "Family Responsibility Zones",
    on: true,
    // The My Maps export also has school pins; the DPS schools layer covers those.
    filter: (f) => f.geometry.type !== "Point",
    options: {
      style: { color: COLORS.frz, weight: 2, fillColor: COLORS.frz, fillOpacity: 0.3 },
      onEachFeature: (f, l) => l.bindPopup(popupTable(f.properties.name, f.properties, [["Notes", "description"]])),
    },
  },
  {
    file: "existing_ped.geojson",
    label: "Existing sidewalks and paths",
    on: false, // ~15k segments; too busy to show at load
    options: {
      style: { color: COLORS.existingPed, weight: 2, opacity: 0.8 },
      onEachFeature: (f, l) =>
        l.bindPopup(
          popupTable(f.properties.Facility_Type || "Pedestrian facility", f.properties, [
            ["On", "On_Road"], ["From", "From_Road"], ["To", "To_Road"], ["Completed", "Date_Completed_Year"],
          ])
        ),
    },
  },
  {
    file: "future_ped.geojson",
    label: "Future pedestrian facilities",
    on: true,
    options: { style: lineStyle(COLORS.futurePed, true), onEachFeature: projectPopup },
  },
  {
    file: "existing_bike.geojson",
    label: "Existing bike facilities",
    on: true,
    options: {
      style: lineStyle(COLORS.existingBike),
      onEachFeature: (f, l) =>
        l.bindPopup(
          popupTable(f.properties.Facility_Type || "Bike facility", f.properties, [
            ["On", "On_Road"], ["From", "From_Road"], ["To", "To_Road"], ["Completed", "Date_Completed_Year"],
          ])
        ),
    },
  },
  {
    file: "future_bike.geojson",
    label: "Future bike facilities",
    on: true,
    options: { style: lineStyle(COLORS.futureBike, true), onEachFeature: projectPopup },
  },
  {
    file: "paper_streets.geojson",
    label: "Paper streets",
    on: true,
    options: {
      style: { color: COLORS.paper, weight: 3, dashArray: "2 5" },
      onEachFeature: (f, l) =>
        l.bindPopup(
          popupTable(`Paper street: ${f.properties.strname || "unnamed"}`, f.properties, [
            ["Length (ft)", "length"], ["Width (ft)", "width_1"], ["Stream", "stream"],
            ["Flood zone", "floodzone"], ["Utility line", "utilitylin"], ["Steep slope", "slope"],
          ])
        ),
    },
  },
  {
    file: "schools.geojson",
    label: "DPS schools",
    on: true,
    options: {
      pointToLayer: (f, latlng) =>
        L.circleMarker(latlng, { radius: 5, color: "#000", weight: 1, fillColor: "#ffd92f", fillOpacity: 1 }),
      onEachFeature: (f, l) => {
        const p = f.properties;
        let html = popupTable(p.name, p, [["Type", "factype"], ["Grades", "grades"], ["Address", "fulladdr"], ["Phone", "phone"]]);
        if (p.agencyurl) {
          const url = /^https?:/.test(p.agencyurl) ? p.agencyurl : `https://${p.agencyurl}`;
          html += `<p><a href="${esc(url)}" target="_blank" rel="noopener">School website</a></p>`;
        }
        l.bindPopup(html);
      },
    },
  },
];

function projectPopup(f, l) {
  l.bindPopup(
    popupTable(f.properties.Project_Name, f.properties, [
      ["Facility", "Facility_Type_Section"], ["On", "On_Road"], ["From", "From_Road"], ["To", "To_Road"],
      ["Status", "Phase_Status"], ["Project ID", "Project_ID"], ["Est. completion", "Est_Construction_Comp_Date"],
    ])
  );
}

function districtOptions(def) {
  return {
    filter: def.filter,
    style: { color: def.color, weight: 2, fillColor: def.color, fillOpacity: 0.05 },
    onEachFeature: (f, l) =>
      l.bindPopup(
        popupTable(f.properties.name, { ...f.properties, year: fmtYear(def.year) }, [
          ["School year", "year"], ["Zone type", "type"], ["Region", "region"], ["Calendar", "calendar"], ["Choice", "choice"],
        ])
      ),
  };
}

// "2026-27" -> "2026–27"
const fmtYear = (y) => (y ? y.replace("-", "–") : "");

function addLegend(year) {
  const legend = L.control({ position: "bottomleft" });
  legend.onAdd = () => {
    const div = L.DomUtil.create("div", "legend");
    const fill = (c, label) => `<div><span class="swatch" style="background:${c};opacity:.6;border:2px solid ${c}"></span>${label}</div>`;
    const line = (c, label, style = "solid") =>
      `<div><span class="swatch line" style="border-top-color:${c};border-top-style:${style}"></span>${label}</div>`;
    div.innerHTML =
      fill(COLORS.frz, "Family Responsibility Zone") +
      line(COLORS.elementary, `Elementary assignment zone${year ? ` (${fmtYear(year)})` : ""}`) +
      line(COLORS.existingPed, "Existing sidewalk / path") +
      line(COLORS.futurePed, "Future pedestrian", "dashed") +
      line(COLORS.existingBike, "Existing bike facility") +
      line(COLORS.futureBike, "Future bike", "dashed") +
      line(COLORS.paper, "Paper street", "dotted") +
      `<div><span class="swatch" style="background:#ffd92f;border:1px solid #000;border-radius:50%;width:.7rem"></span>DPS school</div>`;
    return div;
  };
  legend.addTo(map);
}

async function init() {
  let manifest = {};
  try {
    manifest = await loadJSON("manifest.json");
  } catch (e) {
    console.error(e);
  }
  // School-year label for layers fetched from the newest dated Durham layer.
  const yearOf = (file) => manifest[file.replace(".geojson", "")]?.school_year;
  const year = yearOf("school_districts.geojson");
  if (year) {
    const badge = document.getElementById("school-year");
    badge.textContent = `School year ${fmtYear(year)}`;
    badge.hidden = false;
  }

  const cache = {};
  const control = L.control.layers(null, null, { collapsed: window.innerWidth < 800 }).addTo(map);
  const results = await Promise.allSettled(
    OVERLAYS.map(async (def) => {
      cache[def.file] ??= loadJSON(def.file);
      const data = await cache[def.file];
      const opts = def.color ? districtOptions({ ...def, year: yearOf(def.file) }) : { filter: def.filter, ...def.options };
      const layer = L.geoJSON(data, opts);
      return { def, layer };
    })
  );
  // Add in declared order so polygons sit beneath lines and points.
  for (const r of results) {
    if (r.status === "rejected") {
      console.error(r.reason);
      continue;
    }
    const { def, layer } = r.value;
    const y = yearOf(def.file);
    control.addOverlay(layer, y ? `${def.label} (${fmtYear(y)})` : def.label);
    if (def.on) layer.addTo(map);
  }
  const frz = results.find((r) => r.status === "fulfilled" && r.value.def.file === "frz.geojson");
  if (frz) map.fitBounds(frz.value.layer.getBounds(), { padding: [20, 20] });
  addLegend(year);

  document.getElementById("data-dates").innerHTML = Object.values(manifest)
    .map((m) => {
      const yr = m.school_year ? `, ${fmtYear(m.school_year)} school year` : "";
      return `<li>${esc(m.title)}${esc(yr)}: last changed ${esc(m.updated || "unknown")}</li>`;
    })
    .join("");
}

const aboutBtn = document.getElementById("about-toggle");
aboutBtn.addEventListener("click", () => {
  const about = document.getElementById("about");
  about.hidden = !about.hidden;
  aboutBtn.setAttribute("aria-expanded", String(!about.hidden));
  map.invalidateSize();
});

init();

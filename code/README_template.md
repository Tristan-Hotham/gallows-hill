# Gallows Hill

Where did Britain put its gallows? This study measures {{n_strong|int}} Gallows and Gibbet names on the Ordnance Survey map of Great Britain for height above their surroundings, distance to towns and roads, line of sight from the nearest town, and closeness to boundaries, and compares each name with {{k_controls|int}} ordinary names of the same kind from the same 50 km square, and with random points of land.

**Interactive version:** https://tristan-hotham.github.io/gallows-hill/

**Paper:** https://doi.org/10.5281/zenodo.23688587

By Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion studies: [Bloody Place Names](https://tristan-hotham.github.io/bloody-place-names/) (do grim names mark real battles?), [Within Sight](https://tristan-hotham.github.io/within-sight/) (line of sight between hillforts).

## Headline results

- OS Open Names has {{by_class.gallows|int}} Gallows or Gallow names and {{by_class.gibbet|int}} Gibbet names ({{n_strong|int}} in all; {{strong_by_country.Scotland|int}} in Scotland, {{strong_by_country.England|int}} in England, {{strong_by_country.Wales|int}} in Wales). {{strong_hill_share|pct0}} are hills.
- Near towns: {{groups.strong.town_3.match.obs|pct1}} lie within 3 km of an OS town or city, against {{groups.strong.town_3.match.base|pct1}} of matched ordinary names (chance {{groups.strong.town_3.match.p|p}}). But only {{groups.strong.vill_05.match.obs|pct1}} lie within 500 m of a village or town centre, while the {{stocks.n|int}} village stocks and pillories in OpenStreetMap sit a median {{stocks.vill_med|m}} from one.
- By roads: {{groups.strong.aroad_05.match.obs|pct1}} lie within 500 m of an A-road, against {{groups.strong.aroad_05.match.base|pct1}} of matched names and {{groups.strong.aroad_05.town.base|pct1}} of names also matched on distance to town. Gibbet names: {{groups.gibbet.aroad_05.match.obs|pct0}}. In England, {{groups.strong_england.roman_1.match.obs|pct1}} lie within 1 km of an Itiner-e Roman road, against {{groups.strong_england.roman_1.match.base|pct1}}.
- On low hills: {{groups.strong.rel_pos.match.obs|pct0}} stand above the mean ground within 1 km (random land: {{groups.strong.rel_pos.rand.base|pct0}}), but Gallows hills rise a median {{groups.strong_hills.rel_med.match.obs|f1}} m above their surroundings against {{groups.strong_hills.rel_med.match.base|f1}} m for matched named hills, and stand lower ({{groups.strong_hills.elev_med.match.obs|m0}} against {{groups.strong_hills.elev_med.match.base|m0}}). The gap comes mostly from Scotland; in England gallows names are about as prominent as matched names ({{groups.strong_england.rel_med.match.obs|f1}} m against {{groups.strong_england.rel_med.match.base|f1}} m).
- In view: {{groups.strong.seen_town.match.obs|pct1}} are in line of sight from their nearest town (within 10 km), against {{groups.strong.seen_town.match.base|pct1}} of matched names and {{groups.strong.seen_town.town.base|pct1}} of distance-matched names (chance {{groups.strong.seen_town.town.p|p}}).
- Boundaries: a weak signal only. {{groups.strong.hund_05.match.obs|pct1}} lie within 500 m of an approximate Domesday hundred edge, against {{groups.strong.hund_05.match.base|pct1}} (chance {{groups.strong.hund_05.match.p|p}}). Modern district boundaries: {{groups.strong.lad_1.match.obs|pct1}} within 1 km, against {{groups.strong.lad_1.match.base|pct1}}.
- Hanging names, which usually mean a steep slope, are steep ({{groups.hanging.steep5.match.obs|pct0}} on slopes over 5 degrees against {{groups.hanging.steep5.match.base|pct0}}) and show none of the town or road pattern.

## Files

- `index.html`: the interactive page (Leaflet map, charts). Data are embedded.
- `header.png`: social card (1200 by 630).
- `data/execution_names.csv`: one row per OS Open Names feature in the four classes (Gallows, Gibbet, Hangman, Hanging): names, OS type, coordinates (WGS84 and British National Grid), the baseline stratum, the 1 km cluster id, and every measure (height, height above the ground within 1 km and 500 m, share of ground within 1 km that is lower, slope, nearest town and village with distance and line of sight, distance to A-road and Roman road, district code and distances to district, county, Domesday hundred and Domesday county edges, and position between Domesday places).
- `data/controls.csv.gz`: the {{k_controls|int}} matched names and {{k_controls|int}} random land points for each feature (`parent` is the feature's `os_feature_row`), with the same measures.
- `data/test_results.csv`: every test: group, measure, control type, observed value, control value, 95% range of the replicate controls, chance value.
- `data/documented_gallows.csv`: the four gallows and gibbets that are Wikidata items, with the source of each coordinate and the same measures.
- `data/stocks_pillories.csv`: stocks and pillories in OpenStreetMap (Great Britain) with distances.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage.
- `code/terms.py`: the name classes, with tests. `code/dem.py`: elevation reader and line of sight (from Within Sight).
- `code/01_points.py`, `code/02_measure.py`, `code/03_analyse.py`, `code/04_build_site.py`, `code/05_header.py`: run in that order. `release/` holds the paper and blog figure scripts and `reddit/` the collage.

## Method in brief

Names: OS Open Names features of type populated place, landform, landcover and hydrography, searched for "gallow" (not Galloway), "gibbet", "hangman" and, as a contrast class, "hanging" at the start of a word. Controls: for each name, {{k_controls|int}} OS names of the same local type from the same 50 km grid square (falling back to 100 km, then country, when fewer than 20), excluding grim names; and {{k_controls|int}} random land points in the same square. Each test uses 2,000 replicate control sets, one control per name, and two-sided chance values. A third control set takes the 10 matched names closest to each name in distance to the nearest town.

Measures: AWS Terrain Tiles (zoom 10) for height, height above the mean of 64 samples within 1 km, and slope; OS towns and cities, and villages, for distances and for line of sight (2 m above the town point to 3 m above the name, 45 m steps, curvature and refraction k = 0.13); OpenStreetMap A-roads; Itiner-e Roman roads corrected for a datum shift; ONS district and county boundaries (shared edges only); Voronoi edges between Domesday places in different hundreds and counties (England, within 3 km of a Domesday place).

Caveats: OS points are label points, not gallows sites; OS Open Names omits field names; modern towns and roads stand in for medieval ones; many gallows were manorial or baronial; the Domesday edges are crude and blur any boundary effect; {{n_measures|int}} measures were tested on several groups, so isolated chance values near 0.03 should be read with caution.

## Rerun

Needs Python 3 with pandas, numpy, scipy, shapely 2 and pyproj (and playwright for the header). Place these one folder above this repository (or set `HIST`): `osnames_gb.tsv` (OS Open Names extract), `_data8/uk_bundle_wikidata_osm.json` (Wikidata and OSM extract), `how-roman-is-your-road/` (data/counties.geojson, data/ons/ltla.geojson, data/osm_aroads.json.gz, results/itinere_gb_corrected.geojson) and `domesday-destiny/data/domesday_places.csv`. The elevation tiles are read from the paths in `code/dem.py` (set `DEM_BIN` and `DEM_IDX`). Then run the scripts in `code/` in order.

## Sources and licence

- Place names: OS Open Names. Contains OS data © Crown copyright and database right 2026. Open Government Licence v3.0. https://www.ordnancesurvey.co.uk/products/os-open-names
- Elevation: AWS Terrain Tiles by Mapzen/Tilezen (terrarium, zoom 10). Attribution: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- Roman roads: de Soto, P., Pažout, A., Brughmans, T. and others (2025). Itiner-e: a high-resolution dataset of roads of the Roman Empire. Zenodo 17122148. CC BY 4.0. Datum correction from https://github.com/Tristan-Hotham/how-roman-is-your-road
- A-roads, stocks and pillories: © OpenStreetMap contributors, ODbL.
- Gallows items: Wikidata, CC0.
- District and county boundaries: Office for National Statistics, OGL v3.0. Contains OS data © Crown copyright and database right.
- Domesday places and hundreds: Hull Domesday Project, J.J.N. Palmer, George Slater and the University of Hull (CC BY-NC-SA), via https://github.com/embabel-worlds/realm-domesday and the processed file of https://github.com/Tristan-Hotham/domesday-destiny
- Base map tiles on the page: Esri. Map library: Leaflet.

Because the Domesday data are CC BY-NC-SA, the derived data (`data/`) and the text are released under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). Code (`code/`) is MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) *Gallows Hill: where Britain put its execution places.* Data study and paper. Zenodo. https://doi.org/10.5281/zenodo.23688587

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

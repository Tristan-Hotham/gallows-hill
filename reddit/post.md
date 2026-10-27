# Reddit post: Gallows Hill

## Title

[OC] Where did Britain put its gallows? 340 Gallows and Gibbet place names on the OS map, each compared with 50 ordinary names nearby: 31% lie within 3 km of a town (vs 15%) and 29% within 500 m of an A-road (vs 17%)

## Body

I took every Gallows, Gallow and Gibbet name in OS Open Names (340, mostly hills) and compared each with 50 ordinary names of the same type from the same 50 km square, plus random land points.

They sit near towns but outside them: 31% within 3 km of a town against 15% of matched names, while village stocks and pillories sit a median 266 m from a village centre against 1.7 km for the gallows names. They hug main roads, even against controls just as close to a town. And they are on low rises: a Gallows hill rises a median 7 m above its surroundings, other named hills 15 m.

Caveat: OS points are label points, not gallows sites, and the boundary test (Domesday hundreds) is too rough to show much.

Interactive map: https://tristan-hotham.github.io/gallows-hill/

## Source comment

Source: OS Open Names (Ordnance Survey; contains OS data © Crown copyright and database right 2026; Open Government Licence v3.0) for the place names and towns; AWS Terrain Tiles (Mapzen/Tilezen) for heights and line of sight; OpenStreetMap (© OpenStreetMap contributors, ODbL) for A-roads, stocks and pillories; Itiner-e Roman roads (de Soto et al. 2025, CC BY 4.0); Domesday places and hundreds from the Hull Domesday Project (CC BY-NC-SA); ONS district and county boundaries (Open Government Licence v3.0); Wikidata (CC0) for four documented gallows.

Tools: Python (pandas, NumPy, SciPy, Shapely, pyproj, matplotlib).

Interactive version: https://tristan-hotham.github.io/gallows-hill/
Blog post: https://blog.tristanhotham.com/2026/10/27/gallows-hill/
Paper: https://doi.org/10.5281/zenodo.23688587

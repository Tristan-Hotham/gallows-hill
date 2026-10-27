"""Step 1. Build the sets of points to measure.

Writes ../work/points.csv with one row per point:
  set = obs     OS Open Names features whose name falls in a class of terms.py
        match   matched ordinary names: for each obs feature, K OS features of the same local type
                drawn at random from the same 50 km grid square (100 km, then country, as fallbacks)
        rand    random land points: for each obs feature, K points on land in the same 50 km square
        wd      gallows and gibbets that are items in Wikidata (class "gallows", with coordinates)
        stocks  stocks and pillories mapped in OpenStreetMap (historic=stocks or pillory)
Shared inputs are read in place from the folder above this repository (set HIST to change it).
Run: python3 code/01_points.py
"""
import io, json, os, re
import numpy as np, pandas as pd
from pyproj import Transformer
import shapely
from shapely.geometry import shape
from terms import classify, ANY_GRIM, CLASSES

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
WORK = os.path.join(ROOT, "work"); os.makedirs(WORK, exist_ok=True)
K = 50
rng = np.random.default_rng(20261027)
TR = Transformer.from_crs(4326, 27700, always_xy=True)
TI = Transformer.from_crs(27700, 4326, always_xy=True)

os_ = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", dtype=str, keep_default_na=False)
os_["lat"] = os_.lat.astype(float); os_["lon"] = os_.lon.astype(float)
os_["x"] = os_.x.astype(float); os_["y"] = os_.y.astype(float)
os_["fid"] = np.arange(len(os_))
cls = [classify(a) or (classify(b) if b else None) for a, b in zip(os_.name1, os_.name2)]
os_["cls"] = cls
grim = os_.name1.str.contains(ANY_GRIM) | os_.name2.str.contains(ANY_GRIM)
obs = os_[os_.cls.notna()].copy()
print(obs.cls.value_counts().to_dict())

# grid cells
for s in (50000, 100000):
    os_[f"c{s//1000}"] = (os_.x // s).astype(int).astype(str) + "_" + (os_.y // s).astype(int).astype(str)
obs = os_.loc[obs.index].copy()
pool = os_[~grim]
groups = {s: pool.groupby([f"c{s}", "local_type"]).indices for s in (50, 100)}
gc = pool.groupby(["country", "local_type"]).indices
pool_fid = pool.fid.values

# land polygons for random points
cty = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")))
land = shapely.union_all([shape(f["geometry"]) for f in cty["features"]])
shapely.prepare(land)

rows = []
for r in obs.itertuples():
    rows.append(dict(set="obs", parent=r.fid, fid=r.fid, cls=r.cls, name=r.name1, name2=r.name2, local_type=r.local_type,
                     type=r.type, lat=r.lat, lon=r.lon, x=r.x, y=r.y, country=r.country, county=r.county, stratum=""))
    idx = None
    for s in (50, 100):
        ii = groups[s].get((getattr(r, f"c{s}"), r.local_type))
        if ii is not None and len(ii) >= 20:
            idx, st = ii, f"{s} km"; break
    if idx is None:
        idx, st = gc[(r.country, r.local_type)], "country"
    pick = rng.choice(idx, K, replace=len(idx) < K)
    for j in pick:
        q = pool.iloc[j]
        rows.append(dict(set="match", parent=r.fid, fid=int(q.fid), cls=r.cls, name=q.name1, name2=q.name2, local_type=q.local_type,
                         type=q.type, lat=q.lat, lon=q.lon, x=q.x, y=q.y, country=q.country, county=q.county, stratum=st))
    # random land points in the same 50 km square
    cx, cy = (r.x // 50000) * 50000, (r.y // 50000) * 50000
    got = []
    while len(got) < K:
        xs = cx + rng.random(200) * 50000; ys = cy + rng.random(200) * 50000
        lo, la = TI.transform(xs, ys)
        ok = shapely.contains_xy(land, lo, la)
        got += [(a, b, c, d) for a, b, c, d, o in zip(xs, ys, la, lo, ok) if o]
    for a, b, c, d in got[:K]:
        rows.append(dict(set="rand", parent=r.fid, fid=-1, cls=r.cls, name="", name2="", local_type="", type="",
                         lat=c, lon=d, x=a, y=b, country=r.country, county="", stratum="50 km"))

# Wikidata gallows items and OSM stocks / pillories
B = json.load(open(os.path.join(HIST, "_data8", "uk_bundle_wikidata_osm.json")))
wd = pd.read_csv(io.StringIO(B["wd_structures_tsv"]), sep="\t", dtype=str)
wd = wd[wd["?clsLabel"].str.contains("gallows|gibbet", case=False, na=False)].drop_duplicates("?item")
for w in wd.itertuples():
    lon, lat = map(float, re.findall(r"POINT\(([-\d.]+) ([-\d.]+)\)", w._5)[0])
    x, y = TR.transform(lon, lat)
    qid = w._1.rsplit("/", 1)[1].strip(">")
    rows.append(dict(set="wd", parent=-1, fid=-1, cls="wd", name=w._2.split('"')[1] if '"' in w._2 else w._2.split("@")[0],
                     name2=qid, local_type="", type="", lat=lat, lon=lon, x=x, y=y, country="", county="",
                     stratum="Wikidata " + qid))
st = [o for o in B["osm_uk_features"] if o.get("hist") in ("stocks", "pillory")]
st = pd.DataFrame(st)
st["x"], st["y"] = TR.transform(st.lon.values, st.lat.values)
# keep GB only (drop Northern Ireland and anything outside the land outline)
st = st[shapely.contains_xy(land, st.lon.values, st.lat.values)]
# stocks and a pillory mapped at the same spot count once
keep, seen = [], []
for o in st.itertuples():
    if any((o.x - a) ** 2 + (o.y - b) ** 2 < 50 ** 2 for a, b in seen):
        continue
    seen.append((o.x, o.y)); keep.append(o)
for o in keep:
    rows.append(dict(set="stocks", parent=-1, fid=-1, cls=o.hist, name=o.name or "", name2=o.osm, local_type="", type="",
                     lat=o.lat, lon=o.lon, x=o.x, y=o.y, country="", county="", stratum="OSM " + o.osm))

P = pd.DataFrame(rows)
P.insert(0, "pid", np.arange(len(P)))
P.to_csv(os.path.join(WORK, "points.csv"), index=False)
print(P.groupby(["set", "cls"]).size())
print("strata:", P[P.set == "match"].groupby("stratum").size().to_dict())

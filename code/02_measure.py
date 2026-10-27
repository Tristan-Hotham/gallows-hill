"""Step 2. Measure every point in ../work/points.csv.

Adds, for each point:
  elev_m           ground height (AWS Terrain Tiles, zoom 10, bilinear)
  rel_1km_m        height above the mean of 64 samples on rings of 250, 500, 750 and 1,000 m
  rel_500m_m       the same with rings of 250 and 500 m only
  share_lower_1km  share of those 64 samples that are lower than the point
  slope_deg        slope from samples 100 m either side, east to west and north to south
  town_km, town    nearest OS Open Names populated place of type City or Town
  vill_km, vill    nearest of type Village, Town or City
  seen_town        line of sight from 2 m above the nearest town point to 3 m above the point
                   (only when the town is within 15 km; blank otherwise)
  seen_vill        the same from the nearest village, town or city
  roman_km         nearest Itiner-e Roman road (datum-corrected lines from How Roman Is Your Road)
  aroad_km         nearest OpenStreetMap A-road (motorway, trunk or primary with an A number)
  lad_km           nearest boundary between two local authority districts (ONS); coast excluded
  cty_km           nearest boundary between two counties or unitary authorities (ONS); coast excluded
  dd_in            inside Domesday coverage (England, nearest Domesday place within 3 km)
  hund_km          nearest Domesday hundred boundary, approximated by Voronoi edges between places
                   recorded in different hundreds
  shire_km         the same for edges between places in different Domesday counties
  vill_ratio       d1 / d2, distances to the nearest and second nearest Domesday places
                   (1 = exactly midway between two neighbouring places, 0 = on top of one)
  lad              local authority district code
Writes ../work/measured.csv.
Run: python3 code/02_measure.py
"""
import gzip, json, os, time
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree, Voronoi
import shapely
from shapely.geometry import shape
from dem import DEM, los, haversine

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
WORK = os.path.join(ROOT, "work")
TR = Transformer.from_crs(4326, 27700, always_xy=True)
t0 = time.time()
P = pd.read_csv(os.path.join(WORK, "points.csv"), keep_default_na=False, na_values=[""])
lat, lon, X, Y = P.lat.values, P.lon.values, P.x.values, P.y.values
XY = np.c_[X, Y]

# ---------- terrain ----------
dem = DEM()
gx, gy = dem.to_pix(lat, lon)
ps = 40075016.686 * np.cos(np.radians(lat)) / (1024 * 256)  # metres per pixel
P["elev_m"] = dem.bilinear(gx, gy).astype(float)
ang = np.radians(np.arange(16) * 22.5)
rings = {}
for r in (250, 500, 750, 1000):
    dx = (r * np.cos(ang))[None] / ps[:, None]; dy = (r * np.sin(ang))[None] / ps[:, None]
    rings[r] = dem.bilinear(gx[:, None] + dx, gy[:, None] + dy)
R1 = np.concatenate([rings[r] for r in (250, 500, 750, 1000)], 1)
R5 = np.concatenate([rings[r] for r in (250, 500)], 1)
e = P.elev_m.values
P["rel_1km_m"] = e - R1.mean(1)
P["rel_500m_m"] = e - R5.mean(1)
P["share_lower_1km"] = (R1 < e[:, None]).mean(1)
h = 100.0 / ps
dzx = (dem.bilinear(gx + h, gy) - dem.bilinear(gx - h, gy)) / 200.0
dzy = (dem.bilinear(gx, gy + h) - dem.bilinear(gx, gy - h)) / 200.0
P["slope_deg"] = np.degrees(np.arctan(np.hypot(dzx, dzy)))
print("terrain", round(time.time() - t0))

# ---------- towns and villages, and line of sight from them ----------
os_ = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", dtype=str, keep_default_na=False,
                  usecols=["name1", "type", "local_type", "lat", "lon", "x", "y"])
pp = os_[os_.type == "populatedPlace"]
for key, types in (("town", ["City", "Town"]), ("vill", ["City", "Town", "Village"])):
    T = pp[pp.local_type.isin(types)]
    tx, ty = T.x.astype(float).values, T.y.astype(float).values
    d, i = cKDTree(np.c_[tx, ty]).query(XY)
    P[f"{key}_km"] = d / 1000; P[key] = T.name1.values[i]
    tla, tlo = T.lat.astype(float).values[i], T.lon.astype(float).values[i]
    seen = np.full(len(P), np.nan)
    m = d <= 15000
    tgx, tgy = dem.to_pix(tla[m], tlo[m])
    tz = dem.bilinear(tgx, tgy).astype(np.float64)
    dd = haversine(tla[m], tlo[m], lat[m], lon[m])
    v = los(dem.bilinear, tgx, tgy, tz, gx[m], gy[m], e[m].astype(np.float64), dd, 2.0, 3.0)
    seen[m] = v
    P[f"seen_{key}"] = seen
    print(key, "los done", round(time.time() - t0))


def densify(lines_xy, step=25.0):
    """lines_xy: list of (n,2) arrays in metres. Returns points every <= step m along them."""
    out = []
    for c in lines_xy:
        if len(c) < 2: continue
        a, b = c[:-1], c[1:]
        L = np.hypot(*(b - a).T)
        n = np.maximum(1, np.ceil(L / step).astype(int))
        for (ax, ay), (bx, by), k in zip(a, b, n):
            t = np.arange(k) / k
            out.append(np.c_[ax + (bx - ax) * t, ay + (by - ay) * t])
        out.append(c[-1:])
    return np.concatenate(out)


# ---------- roads ----------
g = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "results", "itinere_gb_corrected.geojson")))
L = []
for f in g["features"]:
    gm = f["geometry"]; cs = gm["coordinates"] if gm["type"] == "MultiLineString" else [gm["coordinates"]]
    for c in cs:
        c = np.array(c); L.append(np.c_[TR.transform(c[:, 0], c[:, 1])])
P["roman_km"] = cKDTree(densify(L)).query(XY)[0] / 1000
a = json.load(gzip.open(os.path.join(HIST, "how-roman-is-your-road", "data", "osm_aroads.json.gz")))
L = []
for w in a:
    c = np.array(w[5], dtype=float).reshape(-1, 2) / 1e5
    L.append(np.c_[TR.transform(c[:, 0], c[:, 1])])
del a
P["aroad_km"] = cKDTree(densify(L, 50.0)).query(XY)[0] / 1000
del L
print("roads", round(time.time() - t0))


# ---------- modern boundaries (internal edges only, so the coast does not count) ----------
def internal_edges(feats):
    """Segments whose two end vertices are both shared with another polygon."""
    owner = {}
    rings_ = []
    for k, f in enumerate(feats):
        gm = shape(f["geometry"])
        polys = [q for q in shapely.get_parts(gm) if q.geom_type == "Polygon"]
        polys += [r for q in shapely.get_parts(gm) if q.geom_type == "MultiPolygon" for r in q.geoms]
        for p in polys:
            for ring in [p.exterior] + list(p.interiors):
                c = np.round(np.array(ring.coords), 6)
                rings_.append((k, c))
                for v in map(tuple, c):
                    owner.setdefault(v, set()).add(k)
    segs = []
    for k, c in rings_:
        sh = np.array([len(owner[tuple(v)]) > 1 for v in c])
        run = []
        for v, s in zip(c, sh):
            if s: run.append(v)
            else:
                if len(run) > 1: segs.append(np.array(run))
                run = []
        if len(run) > 1: segs.append(np.array(run))
    return [np.c_[TR.transform(s[:, 0], s[:, 1])] for s in segs]


lad = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "ons", "ltla.geojson")))["features"]
P["lad_km"] = cKDTree(densify(internal_edges(lad))).query(XY)[0] / 1000
geoms = [shape(f["geometry"]) for f in lad]
tree = shapely.STRtree(geoms)
pi, gi = tree.query(shapely.points(lon, lat), predicate="within")
code = np.array([""] * len(P), dtype=object); code[pi] = [lad[j]["properties"]["areacd"] for j in gi]
P["lad"] = code
cty = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")))["features"]
P["cty_km"] = cKDTree(densify(internal_edges(cty))).query(XY)[0] / 1000
print("modern boundaries", round(time.time() - t0))

# ---------- Domesday hundreds and vills ----------
D = pd.read_csv(os.path.join(HIST, "domesday-destiny", "data", "domesday_places.csv"),
                usecols=["placeId", "name", "county", "hundred", "lat", "lng"]).dropna(subset=["lat", "lng"])
D["x"], D["y"] = TR.transform(D.lng.values, D.lat.values)
D = D.drop_duplicates(subset=["x", "y"]).reset_index(drop=True)
dxy = np.c_[D.x.values, D.y.values]
dd, di = cKDTree(dxy).query(XY, k=2)
P["dd_km"] = dd[:, 0] / 1000
P["vill_ratio"] = dd[:, 0] / dd[:, 1]
P["dd_in"] = (dd[:, 0] <= 3000) & P.lad.str.startswith("E").values
vor = Voronoi(dxy)
hund = (D.county.astype(str) + ":" + D.hundred.astype(str)).values
shire = D.county.astype(str).values
segH, segS = [], []
for (p, q), rv in zip(vor.ridge_points, vor.ridge_vertices):
    if -1 in rv: continue
    seg = vor.vertices[rv]
    if np.hypot(*(seg[1] - seg[0])) > 20000: continue  # skip long edges at the edge of the cloud
    if hund[p] != hund[q]: segH.append(seg)
    if shire[p] != shire[q]: segS.append(seg)
P["hund_km"] = cKDTree(densify(segH)).query(XY)[0] / 1000
P["shire_km"] = cKDTree(densify(segS)).query(XY)[0] / 1000
for c in ("vill_ratio", "hund_km", "shire_km", "dd_km"):
    P.loc[~P.dd_in, c] = np.nan
print("domesday", round(time.time() - t0))
# save the hundred edges (for the page map, simplified)
np.save(os.path.join(WORK, "hund_segs.npy"), np.array(segH))
P.to_csv(os.path.join(WORK, "measured.csv"), index=False)
print("done", round(time.time() - t0))

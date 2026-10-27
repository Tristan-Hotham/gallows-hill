"""Step 3. Compare the execution names with their controls and write the results.

For each group of names and each measure, the observed statistic (a median or a share) is compared
with 2,000 replicate control sets. Each replicate takes one control at random for every name:
  match   an ordinary OS name of the same local type from the same 50 km square
  town    the same, but only the 10 of the 50 matched controls closest to the name in distance to
          the nearest town (so names and controls sit at similar distances from towns)
  rand    a random land point in the same 50 km square
Chance values are two-sided: twice the share of replicates on the far side of the observed value.

Writes ../data/results.json, ../data/execution_names.csv, ../data/documented_gallows.csv,
../data/stocks_pillories.csv, ../data/test_results.csv, ../data/controls.csv.gz and ../work/site.json.
Run: python3 code/03_analyse.py
"""
import json, os, warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
WORK = os.path.join(ROOT, "work"); DATA = os.path.join(ROOT, "data"); os.makedirs(DATA, exist_ok=True)
NREP = 2000
rng = np.random.default_rng(1752)
P = pd.read_csv(os.path.join(WORK, "measured.csv"), keep_default_na=False, na_values=[""])
P["dd_in"] = P.dd_in.astype(str).eq("True")
P["seen_town10"] = np.where(P.town_km <= 10, P.seen_town, np.nan)
P["seen_vill5"] = np.where(P.vill_km <= 5, P.seen_vill, np.nan)

# measure key: (column, statistic, threshold, label)
MEAS = {
    "rel_med":    ("rel_1km_m", "median", None, "Median height above ground within 1 km (m)"),
    "rel_pos":    ("rel_1km_m", "gt", 0.0, "Share higher than the ground within 1 km"),
    "top10":      ("share_lower_1km", "ge", 0.9, "Share higher than 90% of the ground within 1 km"),
    "elev_med":   ("elev_m", "median", None, "Median ground height (m)"),
    "slope_med":  ("slope_deg", "median", None, "Median slope (degrees)"),
    "steep5":     ("slope_deg", "gt", 5.0, "Share on slopes over 5 degrees"),
    "town_med":   ("town_km", "median", None, "Median distance to nearest town (km)"),
    "town_2":     ("town_km", "lt", 2.0, "Share within 2 km of a town"),
    "town_3":     ("town_km", "lt", 3.0, "Share within 3 km of a town"),
    "vill_med":   ("vill_km", "median", None, "Median distance to nearest village or town (km)"),
    "vill_05":    ("vill_km", "lt", 0.5, "Share within 500 m of a village or town"),
    "seen_town":  ("seen_town10", "mean", None, "Share in line of sight of the nearest town (towns within 10 km)"),
    "seen_vill":  ("seen_vill5", "mean", None, "Share in line of sight of the nearest village (within 5 km)"),
    "aroad_med":  ("aroad_km", "median", None, "Median distance to an A-road (km)"),
    "aroad_05":   ("aroad_km", "lt", 0.5, "Share within 500 m of an A-road"),
    "roman_med":  ("roman_km", "median", None, "Median distance to a Roman road (km)"),
    "roman_1":    ("roman_km", "lt", 1.0, "Share within 1 km of a Roman road"),
    "lad_1":      ("lad_km", "lt", 1.0, "Share within 1 km of a district boundary"),
    "lad_med":    ("lad_km", "median", None, "Median distance to a district boundary (km)"),
    "cty_1":      ("cty_km", "lt", 1.0, "Share within 1 km of a county boundary"),
    "hund_med":   ("hund_km", "median", None, "Median distance to a Domesday hundred edge (km)"),
    "hund_05":    ("hund_km", "lt", 0.5, "Share within 500 m of a Domesday hundred edge"),
    "hund_1":     ("hund_km", "lt", 1.0, "Share within 1 km of a Domesday hundred edge"),
    "shire_1":    ("shire_km", "lt", 1.0, "Share within 1 km of a Domesday county edge"),
    "ratio_med":  ("vill_ratio", "median", None, "Median position between neighbouring Domesday places (0 to 1)"),
    "ratio_08":   ("vill_ratio", "gt", 0.8, "Share in the outer fifth between neighbouring Domesday places"),
}


def stat(v, kind, thr):
    """v: array (..., n). Statistic over the last axis, ignoring NaN."""
    ok = ~np.isnan(v)
    if kind == "median": return np.nanmedian(v, -1)
    if kind == "mean": return np.nanmean(v, -1)
    if kind == "gt": return np.where(ok, v > thr, False).sum(-1) / ok.sum(-1)
    if kind == "ge": return np.where(ok, v >= thr, False).sum(-1) / ok.sum(-1)
    if kind == "lt": return np.where(ok, v < thr, False).sum(-1) / ok.sum(-1)


obs = P[P.set == "obs"].set_index("fid")
ctrl = {s: P[P.set == s] for s in ("match", "rand")}
# control matrices (rows in the order of obs.index, K columns)
CM = {s: {c: ctrl[s][c].values.reshape(len(obs), -1) for c in set(m[0] for m in MEAS.values())} for s in ctrl}
assert (ctrl["match"].parent.values.reshape(len(obs), -1)[:, 0] == obs.index.values).all()
# town-matched: the 10 matched controls nearest in distance to town
tk = CM["match"]["town_km"]
near = np.argsort(np.abs(tk - obs.town_km.values[:, None]), 1)[:, :10]
CM["town"] = {c: np.take_along_axis(v, near, 1) for c, v in CM["match"].items()}

# clusters: names of the same class family within 1 km of each other count once (sensitivity)
def clusters(df):
    xy = np.c_[df.x.values, df.y.values]
    pairs = cKDTree(xy).query_pairs(1000)
    lab = np.arange(len(df))
    def find(a):
        while lab[a] != a: a = lab[a]
        return a
    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb: lab[max(ra, rb)] = min(ra, rb)
    return np.array([find(a) for a in range(len(df))])


obs["strong"] = obs.cls.isin(["gallows", "gibbet"])
obs["cluster"] = -1
m = obs.strong.values
obs.loc[m, "cluster"] = clusters(obs[m])
# representative: prefer a hill, then the first
rep = obs[m].assign(h=(obs[m].local_type != "Hill Or Mountain").astype(int)).sort_values(["cluster", "h"]).groupby("cluster").head(1).index
obs["cluster_rep"] = obs.index.isin(rep)

GROUPS = {
    "strong": obs.strong.values,
    "gallows": (obs.cls == "gallows").values,
    "gibbet": (obs.cls == "gibbet").values,
    "hangman": (obs.cls == "hangman").values,
    "hanging": (obs.cls == "hanging").values,
    "strong_england": (obs.strong & (obs.country == "England")).values,
    "strong_scotland": (obs.strong & (obs.country == "Scotland")).values,
    "strong_hills": (obs.strong & (obs.local_type == "Hill Or Mountain")).values,
    "strong_clusters": obs.cluster_rep.values,
}


def test(mask, mk, cs):
    col, kind, thr, _ = MEAS[mk]
    o = obs[col].values[mask]
    if np.isnan(o).all():
        return dict(obs=None, base=None, base_lo=None, base_hi=None, p=None, n=0, ratio=None)
    ov = float(stat(o[None], kind, thr)[0])
    C = CM[cs][col][mask]
    pick = rng.integers(0, C.shape[1], size=(NREP, C.shape[0]))
    b = stat(np.take_along_axis(np.broadcast_to(C, (NREP,) + C.shape), pick[..., None], 2)[..., 0], kind, thr)
    allc = float(stat(C.ravel()[None], kind, thr)[0])
    p = min(1.0, 2 * min((b >= ov).mean(), (b <= ov).mean()))
    return dict(obs=ov, base=allc, base_lo=float(np.percentile(b, 2.5)), base_hi=float(np.percentile(b, 97.5)), p=float(p),
                n=int((~np.isnan(o)).sum()), ratio=(ov / allc if allc else None))


R = {"n_rep": NREP, "k_controls": int(CM["match"]["town_km"].shape[1]), "groups": {}}
rows = []
for g, mask in GROUPS.items():
    R["groups"][g] = {"n": int(mask.sum())}
    for mk in MEAS:
        R["groups"][g][mk] = {}
        for cs in ("match", "rand", "town"):
            r = test(mask, mk, cs)
            R["groups"][g][mk][cs] = r
            rows.append(dict(group=g, measure=mk, label=MEAS[mk][3], control=cs, **r))
    print(g, "done")
T = pd.DataFrame(rows)
T.to_csv(os.path.join(DATA, "test_results.csv"), index=False, float_format="%.4f")

# ---------- counts ----------
o = obs
R["n_names"] = int(len(o))
R["n_measures"] = len(MEAS)
R["n_os_features"] = int(sum(1 for _ in open(os.path.join(os.environ.get("HIST", os.path.dirname(ROOT)), "osnames_gb.tsv"))) - 1)
R["n_strong"] = int(o.strong.sum())
R["n_clusters"] = int(o.cluster_rep.sum())
R["by_class"] = o.cls.value_counts().to_dict()
R["by_class_country"] = {k: v for k, v in pd.crosstab(o.cls, o.country).to_dict(orient="index").items()}
R["strong_by_country"] = o[o.strong].country.value_counts().to_dict()
R["strong_by_type"] = o[o.strong].local_type.value_counts().to_dict()
R["strong_hill_share"] = float((o[o.strong].local_type == "Hill Or Mountain").mean())
R["strong_wood_share"] = float(o[o.strong].local_type.isin(["Woodland Or Forest"]).mean())
R["top_names"] = o[o.strong].name.value_counts().head(12).to_dict()
R["gallow_hill_scot"] = int(((o.name == "Gallow Hill") & (o.country == "Scotland")).sum())
R["gallow_hill_all"] = int((o.name == "Gallow Hill").sum())
R["gallows_hill_eng"] = int(((o.name == "Gallows Hill") & (o.country == "England")).sum())
R["gallows_hill_all"] = int((o.name == "Gallows Hill").sum())
R["strong_dd_in"] = int(o[o.strong].dd_in.sum())
R["strong_eng_dd_in_share"] = float(o[o.strong & (o.country == "England")].dd_in.mean())
R["hanging_wood_share"] = float(o[o.cls == "hanging"].local_type.eq("Woodland Or Forest").mean())
R["hangman_names"] = o[o.cls == "hangman"].name.value_counts().head(6).to_dict()
R["n_counties_strong"] = int(o[o.strong].county.replace("", np.nan).nunique())
# names per 10,000 named features, by country
R["strong_by_county_top"] = o[o.strong].county.replace("", np.nan).dropna().value_counts().head(8).to_dict()

# ---------- distance curves for charts ----------
def hist(col, edges, mask, cs="match"):
    ob = obs[col].values[mask]; ob = ob[~np.isnan(ob)]
    cb = CM[cs][col][mask].ravel(); cb = cb[~np.isnan(cb)]
    clip = lambda v: np.clip(v, edges[0], edges[-1] - 1e-9)
    return dict(edges=list(map(float, edges)), obs=(np.histogram(clip(ob), edges)[0] / len(ob)).round(4).tolist(),
                ctrl=(np.histogram(clip(cb), edges)[0] / len(cb)).round(4).tolist(), n_obs=int(len(ob)))


S = GROUPS["strong"]
R["curves"] = {
    "town": hist("town_km", np.arange(0, 16, 1.0), S),
    "rel": hist("rel_1km_m", np.arange(-30, 61, 5.0), S),
    "aroad": hist("aroad_km", np.arange(0, 5.5, 0.5), S),
    "hund": hist("hund_km", np.arange(0, 4.5, 0.5), S),
    "ratio": hist("vill_ratio", np.arange(0, 1.01, 0.1), S),
    "rel_rand": hist("rel_1km_m", np.arange(-30, 61, 5.0), S, "rand"),
    "slope_hanging": hist("slope_deg", np.arange(0, 16, 1.0), GROUPS["hanging"]),
}

# ---------- documented gallows (Wikidata) and stocks ----------
SRC = {"Q1271020": "https://en.wikipedia.org/wiki/Execution_Dock", "Q26293145": "https://en.wikipedia.org/wiki/Winter%27s_Gibbet",
       "Q5055267": "https://en.wikipedia.org/wiki/Caxton_Gibbet", "Q5150761": "https://en.wikipedia.org/wiki/Combe_Gibbet"}
W = P[P.set == "wd"].copy()
W["wikidata"] = W.name2; W["coord_source"] = "Wikidata " + W.name2 + " (P625)"; W["wikipedia"] = W.wikidata.map(SRC)
keepc = ["name", "wikidata", "wikipedia", "coord_source", "lat", "lon", "elev_m", "rel_1km_m", "share_lower_1km", "town", "town_km",
         "vill", "vill_km", "seen_town", "seen_vill", "roman_km", "aroad_km", "lad_km", "cty_km", "hund_km", "shire_km", "vill_ratio"]
W[keepc].round(4).to_csv(os.path.join(DATA, "documented_gallows.csv"), index=False)
R["famous"] = {r.wikidata: {k: (None if pd.isna(getattr(r, k)) else (round(float(getattr(r, k)), 4) if not isinstance(getattr(r, k), str) else getattr(r, k)))
                            for k in keepc} for r in W.itertuples()}
ST = P[P.set == "stocks"].copy()
ST["osm"] = ST.name2
ST[["osm", "cls", "name", "lat", "lon", "elev_m", "rel_1km_m", "town", "town_km", "vill", "vill_km", "seen_vill", "aroad_km"]].round(4).to_csv(
    os.path.join(DATA, "stocks_pillories.csv"), index=False)
R["stocks"] = dict(n=int(len(ST)), n_stocks=int((ST.cls == "stocks").sum()), n_pillory=int((ST.cls == "pillory").sum()),
                   vill_med=float(ST.vill_km.median()), vill_05=float((ST.vill_km < 0.5).mean()), town_med=float(ST.town_km.median()),
                   rel_med=float(ST.rel_1km_m.median()), seen_vill=float(ST.seen_vill5.mean() if "seen_vill5" in ST else np.nan),
                   aroad_med=float(ST.aroad_km.median()))
R["stocks"]["seen_vill"] = float(np.nanmean(np.where(ST.vill_km <= 5, ST.seen_vill, np.nan)))

# ---------- tables ----------
out = obs.reset_index()
out["os_feature_row"] = out.fid
cols = ["os_feature_row", "name", "name2", "cls", "local_type", "lat", "lon", "x", "y", "country", "county", "stratum", "cluster", "cluster_rep",
        "elev_m", "rel_1km_m", "rel_500m_m", "share_lower_1km", "slope_deg", "town", "town_km", "vill", "vill_km", "seen_town", "seen_vill",
        "roman_km", "aroad_km", "lad", "lad_km", "cty_km", "dd_in", "dd_km", "hund_km", "shire_km", "vill_ratio"]
out[cols].round(4).to_csv(os.path.join(DATA, "execution_names.csv"), index=False)
cc = P[P.set.isin(["match", "rand"])][["set", "parent", "name", "local_type", "lat", "lon", "elev_m", "rel_1km_m", "share_lower_1km", "slope_deg",
                                       "town_km", "vill_km", "seen_town", "seen_vill", "roman_km", "aroad_km", "lad_km", "cty_km", "hund_km",
                                       "shire_km", "vill_ratio"]]
cc.round(3).to_csv(os.path.join(DATA, "controls.csv.gz"), index=False, compression="gzip")

# a few named examples for the text
def ex(q, n=6):
    return [dict(name=r.name, county=r.county, town=r.town, town_km=round(r.town_km, 2), rel=round(r.rel_1km_m, 1), seen=r.seen_town,
                 aroad_km=round(r.aroad_km, 2)) for r in q.head(n).itertuples()]
st_ = obs[obs.strong]
R["examples_near_town_seen"] = ex(st_[(st_.seen_town == 1) & (st_.local_type == "Hill Or Mountain")].sort_values("town_km"))
R["examples_highest_rel"] = ex(st_.sort_values("rel_1km_m", ascending=False))

json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, default=lambda v: None if v != v else v)

# ---------- compact data for the page ----------
site = dict(
    pts=[[round(r.lat, 5), round(r.lon, 5), r.name, r.cls, r.local_type, r.county or r.country, round(r.elev_m), round(r.rel_1km_m, 1),
          r.town, round(r.town_km, 2), (None if pd.isna(r.seen_town) else int(r.seen_town)), round(r.aroad_km, 2), round(r.roman_km, 2),
          (None if pd.isna(r.hund_km) else round(r.hund_km, 2))] for r in obs.itertuples()],
    wd=[[round(r.lat, 5), round(r.lon, 5), r.name, r.wikidata, r.wikipedia] for r in W.itertuples()],
    stocks=[[round(r.lat, 5), round(r.lon, 5), r.cls, r.name] for r in ST.itertuples()],
)
json.dump(site, open(os.path.join(WORK, "site.json"), "w"), separators=(",", ":"))
print("results written")

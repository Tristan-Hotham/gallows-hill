"""Step 4. Build ../index.html from page_template.html, and ../README.md from README_template.md.

Every number in the text is a placeholder like {{groups.strong.town_3.match.obs|pct0}}, filled from
../data/results.json. Map points (../work/site.json), the chart numbers, the Domesday hundred edges and
the Roman roads are embedded in the page as `const D = ...`.
Formats: int (thousands commas), pct0, pct1, f1, f2, km1, km2, x1 (ratio), words, Words, raw.
Run: python3 code/04_build_site.py
"""
import json, os, re
import numpy as np
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HIST = os.environ.get("HIST", os.path.dirname(ROOT))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
site = json.load(open(os.path.join(ROOT, "work", "site.json")))
TI = Transformer.from_crs(27700, 4326, always_xy=True)

# chart numbers
keep_groups = ["strong", "strong_hills", "strong_england", "strong_scotland", "gibbet", "gallows", "hangman", "hanging", "strong_clusters"]
site["G"] = {g: R["groups"][g] for g in keep_groups}
site["C"] = R["curves"]
site["stocks_summary"] = R["stocks"]
site["F"] = R["famous"]
# Domesday hundred edges, rounded to about 100 m
seg = np.load(os.path.join(ROOT, "work", "hund_segs.npy"))
lo, la = TI.transform(seg[..., 0].ravel(), seg[..., 1].ravel())
site["hund"] = np.round(np.c_[la, lo].reshape(-1, 4), 3).tolist()
# Roman roads (Itiner-e, datum corrected), rounded to about 10 m
g = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "results", "itinere_gb_corrected.geojson")))
rr = []
for f in g["features"]:
    gm = f["geometry"]; cs = gm["coordinates"] if gm["type"] == "MultiLineString" else [gm["coordinates"]]
    for c in cs:
        rr.append([[round(p[1], 4), round(p[0], 4)] for p in c])
site["roman"] = rr


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "km1": return f"{v:.1f} km"
    if f == "km2": return f"{v:.2f} km"
    if f == "m0": return f"{v:.0f} m"
    if f == "m": return f"{v * 1000:.0f} m"
    if f == "x1": return f"{v:.1f}"
    if f == "p": return "below 0.001" if v < 0.001 else f"{v:.3f}"
    if f == "words":
        w = "zero one two three four five six seven eight nine ten eleven twelve".split()
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    if f == "Words": return fmt(v, "words").capitalize()
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


def ratio(a, b):
    return get(a) / get(b)


t = open(os.path.join(HERE, "page_template.html")).read()
# derived ratios used in the text: {{ratio:path_a/path_b|fmt}}
t = re.sub(r"\{\{ratio:(.+?)/(.+?)\|(.+?)\}\}", lambda m: fmt(ratio(m.group(1), m.group(2)), m.group(3)), t)
t = re.sub(r"\{\{(.+?)\}\}", sub, t)
data = json.dumps(site, separators=(",", ":"), ensure_ascii=False).replace("–", "-").replace("—", "-").replace("</", "<\\/")
t = t.replace("/*DATA*/", "const D = " + data + ";")
open(os.path.join(ROOT, "index.html"), "w").write(t)
print("index.html", len(t.encode()) // 1024, "KB")
md = open(os.path.join(HERE, "README_template.md")).read()
md = re.sub(r"\{\{ratio:(.+?)/(.+?)\|(.+?)\}\}", lambda m: fmt(ratio(m.group(1), m.group(2)), m.group(3)), md)
md = re.sub(r"\{\{(.+?)\}\}", sub, md)
open(os.path.join(ROOT, "README.md"), "w").write(md)
print("README.md written")

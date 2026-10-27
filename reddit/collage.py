"""r/dataisbeautiful collage for Gallows Hill. 2400 x 3000 px.
Every number comes from ../data/results.json and ../data/execution_names.csv.
Run from this folder: python3 collage.py
"""
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.path import Path
from pyproj import Transformer
import shapely
from shapely.geometry import shape

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); HIST = os.path.dirname(ROOT)
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts") + "/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, RULE = "#E9E6EF", "#1E1C26", "#5E5A70", "#D6D2DF", "#C9C4D5"
HOT, VIO, BAND, MOSS = "#8E1F2B", "#5B3F95", "#A9A3BA", "#3F7A45"

R = json.load(open(os.path.join(ROOT, "data", "results.json"))); G = R["groups"]
N = pd.read_csv(os.path.join(ROOT, "data", "execution_names.csv"), keep_default_na=False, na_values=[""])
TR = Transformer.from_crs(4326, 27700, always_xy=True)
cty = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")))["features"]
land = shapely.union_all([shape(f["geometry"]) for f in cty]).simplify(0.003)
polys = []
for p in shapely.get_parts(land):
    if p.geom_type != "Polygon" or p.area < 0.0003: continue
    c = np.array(p.exterior.coords); x, y = TR.transform(c[:, 0], c[:, 1]); polys.append((x, y))
road = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "results", "itinere_gb_corrected.geojson")))["features"]

# a small gallows glyph: post, beam, brace and rope
GAL = Path([(-0.5, -1), (-0.5, 1), (-0.5, 1), (0.55, 1), (-0.5, 0.55), (-0.05, 1), (0.42, 1), (0.42, 0.45)],
           [Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO, Path.MOVETO, Path.LINETO])

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
pc = lambda v: f"{v*100:.0f}%"

# ---------- title ----------
fig.text(0.045, 0.968, "Where did Britain put its gallows?", fontproperties=DISP, fontsize=43, color=FG, va="top")
fig.text(0.045, 0.918, f"Every Gallows and Gibbet name on the Ordnance Survey map of Great Britain ({R['n_strong']} of them),\n"
         f"each compared with {R['k_controls']} ordinary names of the same kind (hills with hills, woods with woods) nearby.",
         family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.35)
fig.text(0.045, 0.868, "Near the town.  By the road.  On a low hill.", family=SER, fontsize=21, color=HOT, va="top", style="italic")

# ---------- map ----------
ax = fig.add_axes([0.0, 0.30, 0.56, 0.545]); ax.set_aspect("equal"); ax.axis("off")
for x, y in polys: ax.fill(x, y, color=LAND, lw=0)
for f in road:
    gm = f["geometry"]; cs = gm["coordinates"] if gm["type"] == "MultiLineString" else [gm["coordinates"]]
    for c in cs:
        c = np.array(c); x, y = TR.transform(c[:, 0], c[:, 1]); ax.plot(x, y, color="#B7B1C6", lw=0.7, zorder=1)
for cls, col in (("gallows", HOT), ("gibbet", VIO)):
    q = N[N.cls == cls]
    ax.scatter(q.x, q.y, s=70, marker=GAL, facecolors="none", edgecolors=col, linewidths=1.5, zorder=3)
ax.set_xlim(-5000, 670000); ax.set_ylim(0, 1000000)
ax.scatter([], [], s=150, marker=GAL, facecolors="none", edgecolors=HOT, linewidths=1.8, label=f"Gallows / Gallow  {R['by_class']['gallows']}")
ax.scatter([], [], s=150, marker=GAL, facecolors="none", edgecolors=VIO, linewidths=1.8, label=f"Gibbet  {R['by_class']['gibbet']}")
ax.plot([], [], color="#B7B1C6", lw=2, label="Roman roads (Itiner-e)")
fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.035, 0.852), ncol=3, frameon=False, prop={"family": MONO, "size": 11.5}, labelcolor=FG, handletextpad=0.5, columnspacing=1.6)
ax.text(0.03, 0.37, f"Scotland  {R['strong_by_country']['Scotland']}\nEngland   {R['strong_by_country']['England']}\nWales     {R['strong_by_country']['Wales']}",
        transform=ax.transAxes, family=MONO, fontsize=12, color=MUT, va="top", linespacing=1.5)

# ---------- big numbers ----------
tx = fig.add_axes([0.585, 0.30, 0.39, 0.545]); tx.axis("off")
st = R["stocks"]
notes = [
    (pc(G["strong"]["town_3"]["match"]["obs"]), f"lie within 3 km of a town.\nMatched ordinary names: {pc(G['strong']['town_3']['match']['base'])}."),
    (pc(G["strong"]["aroad_05"]["match"]["obs"]), f"lie within 500 m of an A-road, against\n{pc(G['strong']['aroad_05']['match']['base'])} of matched names and {pc(G['strong']['aroad_05']['town']['base'])} of names\njust as close to a town."),
    (f"{G['strong_hills']['rel_med']['match']['obs']:.0f} m", f"median rise of a Gallows hill above the\nground within 1 km. Other named hills\nnearby: {G['strong_hills']['rel_med']['match']['base']:.0f} m. The first rise, not the summit."),
    (f"{st['vill_med']*1000:.0f} m", f"median distance of village stocks and\npillories from a village centre. Gallows\nnames: {G['strong']['vill_med']['match']['obs']:.1f} km. Shame in the village,\ndeath outside it."),
]
for (big, small), y in zip(notes, [0.97, 0.75, 0.50, 0.26]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=42, color=HOT, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=13.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.25)

# ---------- small multiples ----------
def axstyle(a):
    for k in ("top", "right", "left"): a.spines[k].set_visible(False)
    a.spines["bottom"].set_color(MUT); a.tick_params(colors=FG, length=0, labelsize=10.5)
    for t in a.get_xticklabels() + a.get_yticklabels(): t.set_family(MONO)
    a.set_facecolor(BG)


def histp(a, cur, step, xl, title):
    o, c = np.array(cur["obs"]) * 100, np.array(cur["ctrl"]) * 100; x = np.arange(len(o))
    a.bar(x - 0.2, c, 0.4, color=BAND); a.bar(x + 0.2, o, 0.4, color=HOT)
    a.set_xticks(x[::step]); a.set_xticklabels([f"{v:g}" for v in np.array(cur["edges"][:-1])[::step]])
    a.set_yticks([]); axstyle(a)
    a.set_xlabel(xl, family=MONO, fontsize=10.5, color=MUT)
    a.set_title(title, family=SER, fontsize=14, color=FG, loc="left", pad=8, fontweight="semibold")


a1 = fig.add_axes([0.05, 0.135, 0.27, 0.115]); histp(a1, R["curves"]["town"], 2, "km to the nearest town", "Distance to town")
a2 = fig.add_axes([0.375, 0.135, 0.27, 0.115]); histp(a2, R["curves"]["aroad"], 2, "km to the nearest A-road", "Distance to a main road")
a3 = fig.add_axes([0.70, 0.135, 0.27, 0.115])
b = [("Gallows", G["strong"]["hund_05"]["match"]["obs"], HOT), ("matched", G["strong"]["hund_05"]["match"]["base"], BAND),
     ("random", G["strong"]["hund_05"]["rand"]["base"], BAND)]
a3.barh([2, 1, 0], [v * 100 for _, v, _ in b], color=[c for *_, c in b], height=0.62)
for i, (l, v, c) in enumerate(b):
    a3.text(-1, 2 - i, l, ha="right", va="center", family=MONO, fontsize=10.5, color=FG)
    a3.text(v * 100 + 0.8, 2 - i, pc(v), va="center", family=MONO, fontsize=10.5, color=FG)
a3.set_xlim(0, 34); a3.set_yticks([]); a3.set_xticks([]); axstyle(a3); a3.spines["bottom"].set_visible(False)
a3.set_title("Near a Domesday hundred edge?", family=SER, fontsize=14, color=FG, loc="left", pad=8, fontweight="semibold", x=-0.02)
a3.text(0, -0.9, f"within 500 m (England); chance {G['strong']['hund_05']['match']['p']:.2f}", family=MONO, fontsize=10, color=MUT, va="top")
fig.text(0.05, 0.287, "Red: Gallows and Gibbet names.   Grey: matched ordinary names of the same type from the same 50 km square.",
         family=MONO, fontsize=10.5, color=MUT)

# ---------- footer ----------
fig.add_artist(plt.Line2D([0.045, 0.955], [0.095, 0.095], color=FG, lw=1.2))
foot = ("Sources: OS Open Names (contains OS data © Crown copyright and database right 2026, OGL v3); AWS Terrain Tiles (Mapzen/Tilezen);\n"
        "OpenStreetMap A-roads, stocks and pillories (© OpenStreetMap contributors, ODbL); Itiner-e Roman roads (de Soto et al. 2025, CC BY 4.0);\n"
        "Domesday places and hundreds, Hull Domesday Project (CC BY-NC-SA); ONS boundaries (OGL v3). Names are label points, not gallows sites;\n"
        "OS Open Names omits field names. Analysis and chart: Tristan Hotham, with Python and matplotlib.\n"
        "Interactive map: tristan-hotham.github.io/gallows-hill")
fig.text(0.045, 0.086, foot, family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.45)
fig.savefig(os.path.join(HERE, "gallows_hill.png"), dpi=200, facecolor=BG)
print("saved")

"""East Asia base map: GSI prefectures for Japan + Natural Earth 1:50m for other countries.
Mercator, projected to SVG path strings with relative commands on a 0.1 grid."""
import json, math, sys

jp_src, ne_src, out = sys.argv[1], sys.argv[2], sys.argv[3]

LON_W, LON_E, LAT_S, LAT_N, K = 66.0, 162.0, 8.0, 58.0, 20.0
def merc(lat): return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
MY0 = merc(LAT_N)
W, H = (LON_E - LON_W) * K, (MY0 - merc(LAT_S)) * K
def proj(lon, lat): return ((lon - LON_W) * K, (MY0 - merc(lat)) * K)

def decode(t):
    sx, sy = t["transform"]["scale"]; tx, ty = t["transform"]["translate"]
    arcs = []
    for a in t["arcs"]:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs

def dp(pts, eps):
    if len(pts) < 3 or eps <= 0: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy)
        best, bi = -1, -1
        for k in range(i + 1, j):
            px, py = pts[k]
            d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / L if L else math.hypot(px - x1, py - y1)
            if d > best: best, bi = d, k
        if best > eps:
            keep[bi] = True; stack += [(i, bi), (bi, j)]
    return [p for p, k in zip(pts, keep) if k]

def clip(ring, x0, y0, x1, y1):
    """Sutherland-Hodgman against the map rectangle."""
    def run(pts, inside, cut):
        if not pts: return pts
        res = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev): res.append(cut(prev, cur))
                res.append(cur)
            elif inside(prev):
                res.append(cut(prev, cur))
        return res
    def at_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def at_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    r = run(ring, lambda p: p[0] >= x0, at_x(x0))
    r = run(r, lambda p: p[0] <= x1, at_x(x1))
    r = run(r, lambda p: p[1] >= y0, at_y(y0))
    r = run(r, lambda p: p[1] <= y1, at_y(y1))
    return r

def area(r): return 0.5 * abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r))))

def fmt(r):
    q = [(round(x * 10), round(y * 10)) for x, y in r]
    def n(v): return f"{v / 10:g}"
    s = f"M{n(q[0][0])},{n(q[0][1])}l"
    s += " ".join(f"{n(b[0] - a[0])},{n(b[1] - a[1])}" for a, b in zip(q, q[1:]) if b != a)
    return s + "z"

def shapes(t, obj, tol_for):
    """Yield (geometry, [rings in projected coords]) per polygon, clipped to the map."""
    raw = decode(t)
    cache = {}
    def arc(i, tol):
        key = (i if i >= 0 else ~i, tol)
        if key not in cache:
            cache[key] = dp([proj(*p) for p in raw[key[0]]], tol)
        return cache[key] if i >= 0 else cache[key][::-1]
    for g in t["objects"][obj]["geometries"]:
        tol = tol_for(g)
        if tol is None or g["type"] not in ("Polygon", "MultiPolygon"): continue
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        for poly in polys:
            lonlat = [p for i in poly[0] for p in raw[i if i >= 0 else ~i]]
            clon = sum(p[0] for p in lonlat) / len(lonlat); clat = sum(p[1] for p in lonlat) / len(lonlat)
            rings = []
            for ridx in poly:
                pts = []
                for i in ridx:
                    seg = arc(i, tol)
                    pts += seg if not pts else seg[1:]
                pts = clip(pts, 0, 0, W, H)
                if len(pts) >= 3: rings.append(pts)
            if rings and area(rings[0]) >= 0.25:
                yield g, (clon, clat), rings

# Japan: prefectures (地球地図日本)
jp = json.load(open(jp_src, encoding="utf-8"))
prefs = {}
for g, (clon, clat), rings in shapes(jp, "japan", lambda g: 0.1):
    prefs.setdefault(g["properties"]["nam_ja"], []).append("".join(fmt(r) for r in rings))
prefs = {k: "".join(v) for k, v in prefs.items()}

# Other countries (Natural Earth 1:50m)
TARGET = {"156": "CN", "158": "TW", "410": "KR", "344": "HK", "446": "MO"}
# 1:10m for the countries people zoom into, 1:50m for the backdrop
ne50 = json.load(open(ne_src, encoding="utf-8"))
ne10 = json.load(open(sys.argv[4], encoding="utf-8"))
def bg_tol(g):
    return None if g.get("id") in TARGET or g.get("id") == "392" else 0.45
def target_tol(g):
    return 0.1 if g.get("id") in TARGET else None
lands = {}
for g, (clon, clat), rings in [*shapes(ne50, "countries", bg_tol), *shapes(ne10, "countries", target_tol)]:
    gid = g.get("id")
    # southern Kurils are already drawn from the GSI Hokkaido data
    if gid == "643" and 145.0 < clon < 150.0 and 43.0 < clat < 46.6: continue
    key = TARGET.get(gid, "bg")
    lands.setdefault(key, []).append("".join(fmt(r) for r in rings))
lands = {k: "".join(v) for k, v in lands.items()}

res = {"w": round(W, 1), "h": round(H, 1), "lonW": LON_W, "my0": MY0, "k": K, "japan": prefs, "lands": lands}
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("W,H", round(W), round(H), "jp bytes", sum(map(len, prefs.values())), "prefs", len(prefs),
      {k: len(v) for k, v in lands.items()})

"""Generate the DP-600 build write-up graphics as standalone SVGs (light + dark via prefers-color-scheme).

Every number here comes from DP600_BUILD_GUIDE.md (measured during the build) or from the gold tables
read from OneLake on 2026-09-24 (chartdata.json). Run: python3 make_graphics.py
Palette: the dataviz skill's validated default (slots 1-4 pass CVD checks in both modes)."""
import json, os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "chartdata.json")))
FONT = "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

STYLE = """
.bg{fill:#fcfcfb}.card{fill:#fcfcfb;stroke:rgba(11,11,11,.12)}.panel{fill:#f4f3f0;stroke:rgba(11,11,11,.08)}
.t1{fill:#0b0b0b}.t2{fill:#52514e}.t3{fill:#898781}.grid{stroke:#e1e0d9}.axis{stroke:#c3c2b7}
.s1{fill:#2a78d6}.s2{fill:#eb6834}.s3{fill:#1baf7a}.s4{fill:#eda100}.mut{fill:#c3c2b7}
.l1{stroke:#2a78d6}.l2{stroke:#eb6834}.lmut{stroke:#c3c2b7}.ln{stroke:#898781}
.good{fill:#0ca30c}.bad{fill:#d03b3b}.warn{fill:#b77900}.okbg{fill:#e3f3e3}.badbg{fill:#fbe4e4}.warnbg{fill:#fbf0d6}
.box{fill:#ffffff;stroke:#c3c2b7}.boxa{fill:#e8f0fb;stroke:#2a78d6}.boxb{fill:#fdeee7;stroke:#eb6834}.boxc{fill:#e4f5ee;stroke:#1baf7a}.boxd{fill:#fdf3dc;stroke:#eda100}
.halo{stroke:#fcfcfb;stroke-width:4px;stroke-linejoin:round;paint-order:stroke}.edge{stroke:#898781;fill:none}.edgeb{stroke:#898781;fill:none;stroke-dasharray:5 4}
@media (prefers-color-scheme: dark){
.bg{fill:#1a1a19}.card{fill:#1a1a19;stroke:rgba(255,255,255,.14)}.panel{fill:#232322;stroke:rgba(255,255,255,.08)}
.t1{fill:#ffffff}.t2{fill:#c3c2b7}.t3{fill:#898781}.grid{stroke:#2c2c2a}.axis{stroke:#383835}
.s1{fill:#3987e5}.s2{fill:#d95926}.s3{fill:#199e70}.s4{fill:#c98500}.mut{fill:#52514e}
.l1{stroke:#3987e5}.l2{stroke:#d95926}.lmut{stroke:#52514e}
.good{fill:#0ca30c}.bad{fill:#e66767}.warn{fill:#fab219}.okbg{fill:#1f3320}.badbg{fill:#3a2020}.warnbg{fill:#3a3120}
.box{fill:#232322;stroke:#52514e}.boxa{fill:#1c2a3d;stroke:#3987e5}.boxb{fill:#3a2519;stroke:#d95926}.boxc{fill:#17302a;stroke:#199e70}.boxd{fill:#352a14;stroke:#c98500}
.halo{stroke:#1a1a19}.edge{stroke:#898781}.edgeb{stroke:#898781}}
"""


def T(x, y, s, size=13, cls="t1", anchor="start", weight="normal", mono=False, italic=False, halo=True):
    fam = MONO if mono else FONT
    cls = cls + (" halo" if halo and cls != "bg" else "")
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}"'
            f' class="{cls}" text-anchor="{anchor}"{st}>{escape(str(s))}</text>')


def R(x, y, w, h, cls, rx=4):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w,0):.1f}" height="{max(h,0):.1f}" rx="{rx}" class="{cls}"/>'


def L(x1, y1, x2, y2, cls="grid", w=1):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" stroke-width="{w}"/>'


def wrap(s, width_px, size):
    per = max(4, int(width_px / (size * 0.53)))
    out, cur = [], ""
    for w in str(s).split():
        if len(cur) + len(w) + 1 > per and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return out + ([cur] if cur else [])


def TW(x, y, s, width, size=13, cls="t1", lh=None, **kw):
    lh = lh or size * 1.35
    lines = wrap(s, width, size)
    return "".join(T(x, y + i * lh, ln, size, cls, **kw) for i, ln in enumerate(lines)), len(lines) * lh


def svg(name, w, h, title, subtitle, body, source):
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
            f"<title>{escape(title)}</title><desc>{escape(subtitle)}</desc><style>{STYLE}</style>",
            R(0.5, 0.5, w - 1, h - 1, "card", 12), T(24, 38, title, 21, "t1", weight="600")]
    sub, _ = TW(24, 62, subtitle, w - 48, 13, "t2")
    foot = T(24, h - 14, source, 11, "t3")
    open(os.path.join(HERE, name), "w").write("".join(head) + sub + body + foot + "</svg>")
    print("wrote", name)


def fmt(n, d=0):
    return f"{n:,.{d}f}"


# ---------------------------------------------------------------- charts
def practice_scores():
    doms = [("Maintain a data analytics solution", 23, 54), ("Prepare data", 57, 74),
            ("Implement and manage semantic models", 64, 93), ("Overall", 50, 74)]
    w, h = 900, 380; x0, x1 = 330, 860; y = 120
    sx = lambda v: x0 + (x1 - x0) * v / 100
    b = [L(sx(v), 100, sx(v), 320, "grid") for v in range(0, 101, 25)]
    b += [T(sx(v), 336, f"{v}%", 11, "t3", "middle") for v in range(0, 101, 25)]
    b += [L(sx(78), 92, sx(78), 320, "ln", 1.5), T(sx(78) + 5, 102, "78% — Microsoft's bar", 11, "t2")]
    for i, (d, a, c) in enumerate(doms):
        yy = y + i * 52 + (14 if d == "Overall" else 0)
        if d == "Overall":
            b.append(L(24, yy - 26, x1, yy - 26, "axis"))
        b.append(T(24, yy + 5, d, 13, "t1", weight="600" if d == "Overall" else "normal"))
        b.append(L(sx(a), yy, sx(c), yy, "lmut", 3))
        b.append(f'<circle cx="{sx(a):.1f}" cy="{yy}" r="6" class="mut"/>')
        b.append(f'<rect x="{sx(c)-6:.1f}" y="{yy-6}" width="12" height="12" rx="2" class="s1"/>')
        b.append(T(sx(a) - 10, yy + 5, f"{a}%", 12, "t2", "end"))
        b.append(T(sx(c) + 11, yy + 5, f"{c}%  (+{c-a})", 12, "t1", weight="600"))
    b += [f'<circle cx="340" cy="356" r="5" class="mut"/>', T(350, 360, "Sep 3 — taken cold", 12, "t2"),
          R(484, 351, 10, 10, "s1", 2), T(500, 360, "Sep 24 — after the 25-day build", 12, "t2")]
    svg("practice-scores.svg", w, h + 12, "DP-600 practice assessment: 50% → 74% in three weeks",
        "Same question ranges on both attempts. Semantic models, built in Weeks 2–3, rose most. "
        "23 of Sep 24's 50 questions were repeats. On the 27 unseen ones the score was 67%.",
        "".join(b), "Source: Microsoft Learn practice assessment results, 2026-09-03 and 2026-09-24")


def delta_maintenance():
    stages = [("30 appends × 8 files", 240, 240), ("OPTIMIZE", 19, 19), ("OPTIMIZE ZORDER BY seller_sk", 10, 2),
              ("VACUUM RETAIN 0 HOURS", 10, 2)]
    w, h = 900, 420; x0, x1, y0 = 270, 740, 110
    sx = lambda v: x0 + (x1 - x0) * v / 240
    b = [L(sx(v), y0 - 8, sx(v), y0 + 4 * 62, "grid") for v in (0, 60, 120, 180, 240)]
    b += [T(sx(v), y0 + 4 * 62 + 16, str(v), 11, "t3", "middle") for v in (0, 60, 120, 180, 240)]
    for i, (s, f, sp) in enumerate(stages):
        yy = y0 + i * 62
        b.append(T(24, yy + 22, s, 13, "t1", mono=("OPTIMIZE" in s or "VACUUM" in s)))
        b.append(R(x0, yy + 4, sx(f) - x0, 18, "s1", 3)); b.append(T(sx(f) + 6, yy + 18, f"{f} files", 12, "t1"))
        b.append(R(x0, yy + 26, sx(sp) - x0, 18, "s2", 3)); b.append(T(sx(sp) + 6, yy + 40, f"busiest seller in {sp}", 12, "t2"))
    b += [R(24, 396, 10, 10, "s1", 2), T(40, 405, "Files in the table", 12, "t2"),
          R(180, 396, 10, 10, "s2", 2), T(196, 405, "Files holding the busiest seller's rows (what a filter must open)", 12, "t2")]
    svg("delta-maintenance-files.svg", w, h + 14, "OPTIMIZE compacts, Z-Order co-locates, VACUUM does neither",
        "gold.lab_fragmented, 112,650 rows. Compaction cut 240 files to 19, but the seller still sat in all 19. "
        "Z-Order put it in 2. VACUUM changed nothing a query sees. It only destroyed version 0.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md Day 14, measured 2026-09-22")


def dax_costs():
    rows = [("Filter on a column", 47, 18, "s1"), ("Measure inside FILTER", 313, 8150, "s2"),
            ("Column expression in SUMX", 47, 1, "s1"), ("Measure inside SUMX", 377, 10100, "s2")]
    w, h = 960, 372; b = []
    for p, (title, idx, mx, unit, x0) in enumerate([("Query time — median of 3 cold runs", 1, 400, "ms", 250),
                                                     ("Data shipped out of the storage engine", 2, 10100, "KB", 650)]):
        x1 = x0 + (280 if p == 0 else 210)
        b.append(T(x0, 112, title, 13, "t1", weight="600"))
        for i, r in enumerate(rows):
            yy = 128 + i * 46 + (16 if i >= 2 else 0)
            v = r[idx]; bw = max(2, (x1 - x0) * v / mx)
            b.append(R(x0, yy, bw, 22, r[3], 3))
            b.append(T(x0 + bw + 6, yy + 16, f"{fmt(v)} {unit}", 12, "t1"))
            if p == 0:
                b.append(T(24, yy + 16, r[0], 13, "t1"))
    b += [T(24, 120, "Day 18 Step 3", 11, "t3"), T(24, 228, "Day 18 Step 4", 11, "t3"),
          L(24, 212, 930, 212, "axis")]
    b += [R(24, 322, 10, 10, "s1", 2), T(40, 331, "Column condition: stays in one storage-engine scan", 12, "t2"),
          R(400, 322, 10, 10, "s2", 2), T(416, 331, "Measure per row: context transition drags every column to the formula engine", 12, "t2")]
    svg("dax-filter-iterator-cost.svg", w, h, "A measure evaluated per row: ~8–9× slower, ~450× more data moved",
        "Same answer both ways (9,874,530.84 and 36,145.28). The cost only shows in DAX Studio's Server Timings. "
        "A simpler FILTER(fact, RELATED(col) = x) was optimized into the good form and cost nothing.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md Day 18, DAX Studio with Clear on Run, Olist Model (Direct Lake on OneLake), 2026-09-23")


def fallback():
    w, h = 900, 300; x0, x1 = 250, 860; mx = 10057
    sx = lambda v: (x1 - x0) * v / mx
    b = [T(24, 128, "fact_orders (Delta table)", 13), R(x0, 114, max(3, sx(17)), 22, "s1", 3),
         T(x0 + 8, 130, "17 ms · Scan (Direct Lake)", 12, "t1"),
         T(24, 188, "v_delivered_orders (SQL view)", 13),
         R(x0, 174, sx(9329), 22, "s2", 3), R(x0 + sx(9329) + 2, 174, sx(704), 22, "s4", 3),
         T(x0, 214, "9,329 ms opening the DirectQuery connection  +  704 ms running the SQL  =  10,057 ms", 12, "t1"),
         T(24, 250, "Same model (Direct Lake on SQL), same count, cold. DirectLakeBehavior = Automatic hides this;", 12, "t2"),
         T(24, 268, "DirectLakeOnly turns it into an error: “would require a fallback to DirectQuery … fallback is disabled.”", 12, "t2")]
    svg("direct-lake-fallback.svg", w, h + 10, "A SQL view silently cost ~600× a Direct Lake query",
        "Direct Lake on SQL falls back to DirectQuery for views, SQL-endpoint RLS/CLS and over-guardrail tables. "
        "Direct Lake on OneLake never falls back. It errors instead.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md Day 25, DAX Studio Server Timings, 2026-09-24")


def model_size():
    imp = [("customer_unique_id", 11.2, 0), ("customer_name", 9.1, 1), ("product_id", 4.3, 0), ("product_name", 4.3, 1), ("order_key (INT)", 3.6, 3)]
    bad = [("customer_id", 11.3, 0), ("order_id", 11.3, 0), ("customer_unique_id", 11.3, 0), ("review_comment_message", 7.5, 2), ("product_id", 4.4, 0)]
    kinds = [("s1", "Text ID (32-char hex)"), ("s4", "Name text"), ("s2", "Free text"), ("s3", "Integer key")]
    w, h = 960, 400; b = []
    for p, (title, sub, cols, x0) in enumerate([("Olist Model Import — the star", "73.15 MiB · 13 tables · 83 columns", imp, 190),
                                              ("Olist Model Bad — one flat table", "85.56 MiB (+17%) · 2 tables · 42 columns", bad, 660)]):
        lx = 24 if p == 0 else 494
        b += [T(lx, 110, title, 14, "t1", weight="600"), T(lx, 128, sub, 12, "t2")]
        for i, (c, mb, k) in enumerate(cols):
            yy = 146 + i * 36; bw = 200 * mb / 11.3
            b.append(T(x0 - 8, yy + 15, c, 12, "t1", "end", mono=True))
            b.append(R(x0, yy, bw, 20, kinds[k][0], 3)); b.append(T(x0 + bw + 6, yy + 15, f"{mb} MB", 12, "t1"))
    b.append(L(478, 100, 478, 330, "axis"))
    for i, (c, lab) in enumerate(kinds):
        b += [R(24 + i * 200, 346, 10, 10, c, 2), T(40 + i * 200, 355, lab, 12, "t2")]
    b.append(T(24, 378, "Refresh 17.9 s vs 16.8 s · the same query 17 ms in both. At 113k rows the flaws cost size, not speed.", 12, "t2"))
    svg("good-vs-bad-model.svg", w, h + 12, "The deliberately bad model: +17% size, same speed",
        "The five largest columns in each Import model, from VertiPaq Analyzer. Text keys cost ~3× an integer key. "
        "The flaws that hurt queries (bi-directional filtering, measures in FILTER) only show when a query exercises them.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md Day 21, DAX Studio View Metrics, 2026-09-24")


def pareto():
    st = DATA["state"]; tot = sum(v for _, v in st)
    w, h = 960, 380; x0, y0, y1 = 70, 110, 300; bw = 30; gap = 8
    mx = st[0][1] / tot
    sy = lambda f: y1 - (y1 - y0) * f / 0.7
    b = [L(x0, sy(v), x0 + len(st) * (bw + gap), sy(v), "grid") for v in (0, .2, .4, .6)]
    b += [T(x0 - 8, sy(v) + 4, f"{int(v*100)}%", 11, "t3", "end") for v in (0, .2, .4, .6)]
    cum = 0
    for i, (s, v) in enumerate(st):
        f = v / tot; cum += f; x = x0 + i * (bw + gap)
        cls = "s1" if i < 3 else "mut"
        b.append(R(x, sy(f), bw, y1 - sy(f), cls, 3))
        b.append(T(x + bw / 2, y1 + 16, s, 11, "t2", "middle"))
        if i < 3:
            b.append(T(x + bw / 2, sy(f) - 8, f"{f*100:.1f}%", 12, "t1", "middle", weight="600"))
    ax = x0 + 4 * (bw + gap)
    b.append(T(ax, sy(0.62), "Three states hold 81% of revenue; SP alone is 7× PR.", 13, "t1", weight="600"))
    b.append(T(ax, sy(0.62) + 20, "Cumulative Revenue %:  SP 64.4%  →  PR 73.7%  →  MG 81.1%", 12, "t1"))
    b.append(T(ax, sy(0.62) + 40, "Built with WINDOW (running %), OFFSET (gap to the state above) and INDEX (% of top). No calendar twin exists.", 12, "t2"))
    svg("seller-state-pareto.svg", w, h, "Window functions where there's no calendar: the seller-state Pareto",
        f"Share of line revenue by seller state, 23 states, total R$ {tot:,.2f}. Dimension: dim_seller[seller_state].",
        "".join(b), "Source: gold.fact_order_items × gold.dim_seller, read from OneLake 2026-09-24; measures from Day 18 Step 1d")


def rls_leak():
    meas = ["Revenue", "Order Count", "Customers", "Payment Value"]
    base = [13591643.70, 99441, 96096, 16008872.12]
    views = [("Seller SP (static role on dim_seller)", [8753396.21, 99441, 96096, 16008872.12]),
             ("test.north — dynamic role, SP customers", [5204108.34, 41749, 40299, 5999513.86]),
             ("test.analyst — dynamic role, RJ customers", [1824182.58, 12852, 12382, 2144487.88])]
    w, h = 960, 380; b = []
    for p, (title, vals) in enumerate(views):
        x0 = 24 + p * 312; bx = x0 + 104; bwmax = 150
        b.append(T(x0, 112, title, 13, "t1", weight="600"))
        for i, m in enumerate(meas):
            f = vals[i] / base[i]; yy = 132 + i * 44
            leak = f > 0.999 and p == 0
            b.append(T(x0, yy + 15, m, 12, "t1"))
            b.append(R(bx, yy, bwmax, 20, "panel", 3))
            b.append(R(bx, yy, bwmax * f, 20, "s2" if leak else "s1", 3))
            b.append(T(bx + bwmax + 6, yy + 15, f"{f*100:.0f}%", 12, "t1", weight="600" if leak else "normal"))
            if leak:
                b.append(T(bx + 6, yy + 34, "unchanged: leaks", 11, "t2"))
    b += [R(24, 332, 10, 10, "s1", 2), T(40, 341, "Share of the no-role total the user sees", 12, "t2"),
          R(330, 332, 10, 10, "s2", 2), T(346, 341, "Not filtered at all", 12, "t2")]
    svg("rls-leak.svg", w, h, "Model RLS: put the rule at the top of what you protect",
        "Signed in as each test user (Test as role doesn't work with SSO on Direct Lake on OneLake). A seller rule filters only the lines. "
        "Orders, customers and payments sit uphill and leak. A customer rule secures all four.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md Day 19, Olist Report page RLS OLS, 2026-09-23")


def scd2_waterfall():
    steps = [("Snapshot at the watermark (2017-12-31)", 44034), ("Brand-new customers in the 2018 batch", 52062),
             ("Existing customers who moved", 99), ("Moves inside the batch (islands)", 68)]
    w, h = 900, 380; x0, x1 = 330, 790; mx = 96263
    sx = lambda v: x0 + (x1 - x0) * v / mx
    b = []; run = 0
    for i, (s, v) in enumerate(steps):
        yy = 112 + i * 40
        b.append(T(24, yy + 15, s, 13))
        b.append(R(sx(run), yy, max(3, sx(run + v) - sx(run)), 20, "s1" if i == 0 else "s3", 3))
        b.append(T(sx(run + v) + 6, yy + 15, f"+{fmt(v)}", 12, "t1"))
        run += v
    yy = 112 + 4 * 40 + 10
    b += [L(24, yy - 6, 860, yy - 6, "axis"), T(24, yy + 15, "Versions in gold.dim_customer", 13, "t1", weight="600"),
          R(x0, yy, sx(mx) - x0, 20, "s1", 3), T(x1 + 6, yy + 15, "96,263", 12, "t1", weight="600"),
          T(24, yy + 50, "96,263 − 96,096 people = 167 closed versions (99 expired + 68 in-batch first addresses).", 12, "t2"),
          T(24, yy + 68, "The real check is current_rows = people. The first run had people = 96,195: lazy evaluation re-read", 12, "t2"),
          T(24, yy + 86, "“current” after the expire merge and gave 99 movers a second durable key. Fix: .localCheckpoint().", 12, "t2")]
    svg("scd2-versions.svg", w, h + 26, "SCD2 on real address changes: where 96,263 versions come from",
        "Olist has no change log, but 252 people ordered from a new address. That's real change, inferred between orders. "
        "Tracked: zip prefix, city, state. Event time, not load time, sets valid_from.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md Day 12, verified in OneLake 2026-09-21")


def yoy():
    mo = dict(DATA["month"])
    months = [f"{m:02d}" for m in range(1, 13)]
    ytd = {}
    for y in ("2017", "2018"):
        c, arr = 0, []
        for m in months:
            if y == "2018" and m > "09":
                break
            c += mo.get(f"{y}-{m}", 0); arr.append(c)
        ytd[y] = arr
    w, h = 900, 420; x0, x1, y0, y1 = 80, 600, 110, 340; mx = 8e6
    sx = lambda i: x0 + (x1 - x0) * i / 11
    sy = lambda v: y1 - (y1 - y0) * v / mx
    b = [L(x0, sy(v), x1, sy(v), "grid") for v in range(0, 8000001, 2000000)]
    b += [T(x0 - 8, sy(v) + 4, f"{v/1e6:.0f}M", 11, "t3", "end") for v in range(0, 8000001, 2000000)]
    b += [T(sx(i), y1 + 16, "JFMAMJJASOND"[i], 11, "t3", "middle") for i in range(12)]
    for y, cls, lab in (("2017", "l1", "s1"), ("2018", "l2", "s2")):
        pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(ytd[y]))
        b.append(f'<polyline points="{pts}" class="{cls}" fill="none" stroke-width="2.5"/>')
        for i, v in enumerate(ytd[y]):
            b.append(f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="3.5" class="{lab}"/>')
    b += [T(sx(11) + 8, sy(ytd["2017"][11]) + 4, "2017: 6.16M", 12, "t1", weight="600"),
          T(sx(8) + 8, sy(ytd["2018"][8]) - 8, "2018: 7.39M (ends Sep 3)", 12, "t1", weight="600"),
          L(sx(7), sy(ytd["2017"][7]), sx(7), sy(ytd["2018"][7]), "ln", 1.5),
          T(sx(7) + 8, (sy(ytd["2017"][7]) + sy(ytd["2018"][7])) / 2 + 20, "Aug YTD: +137%", 12, "t1", weight="600"),
          T(730, 150, "Year vs year: +20.0%", 13, "t1", weight="600"),
          T(730, 170, "Like for like (Jan–Aug):", 12, "t2"), T(730, 188, "+137.3%", 13, "t1", weight="600"),
          T(730, 222, "SAMEPERIODLASTYEAR is", 12, "t2"), T(730, 238, "correct. The question isn't:", 12, "t2"),
          T(730, 254, "2018 is 8 months against 12.", 12, "t2"),
          R(80, 380, 10, 10, "s1", 2), T(96, 389, "2017 revenue, cumulative", 12, "t2"),
          R(280, 380, 10, 10, "s2", 2), T(296, 389, "2018 revenue, cumulative", 12, "t2")]
    svg("yoy-partial-year.svg", w, h + 8, "The calculation group was right. The YoY number was still misleading",
        "Revenue YTD by month from the Time Intelligence calculation group. Olist's last sale is 2018-09-03, "
        "so a full-year comparison sets 8 months of 2018 against 12 months of 2017.",
        "".join(b), "Source: gold.fact_order_items × fact_orders[purchase_date], read from OneLake 2026-09-24; Day 16")


def headline_numbers():
    tiles = [("53 : 1", "1,000,163 GPS points → 19,010 zip prefixes (median, not mean: 199 prefixes moved >11 km)"),
             ("4.5×", "Dataflow Gen2 staging on vs off: 1m 07s vs 15s. Nothing downstream used the staged copy"),
             ("1 of 112,651", "rows skipped by Copy fault tolerance. Without logging, which row stays unknown"),
             ("96,195", "people after SCD2 run 1: 99 too many. A lazy DataFrame re-read the table it had just changed"),
             ("3,713", "COUNT(*) at a VACUUMed version still answers, from the log. SUM(price) gets a 404"),
             ("8× · 450×", "slower and more data moved when a measure sits inside FILTER over the fact"),
             ("~600×", "a SQL view's silent DirectQuery fallback vs a Direct Lake scan: 10,057 ms vs 17 ms"),
             ("+17%", "model size from a flat table of text keys. Same refresh, same query speed at 113k rows")]
    w, h = 960, 420; b = []
    for i, (big, txt) in enumerate(tiles):
        c, r = i % 4, i // 4; x = 24 + c * 232; y = 96 + r * 150
        b.append(R(x, y, 216, 136, "panel", 8))
        b.append(T(x + 14, y + 42, big, 26, "t1", weight="700"))
        t, _ = TW(x + 14, y + 68, txt, 190, 12, "t2"); b.append(t)
    svg("headline-numbers.svg", w, h, "Measured, not assumed: eight numbers from the build",
        "Every one was recorded against an expected value in the build guide. Several corrected the guide itself.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md, Days 9–25")


def partitions():
    w, h = 960, 330; b = []
    items = [(str(y), "year") for y in range(2015, 2025)] + [f"2025Q{q}" for q in (1, 2, 3)] + [f"M{m}" for m in range(12)]
    items = [(x if isinstance(x, tuple) else (x, "q" if "Q" in x else "m")) for x in items]
    rows = {"2016": 329, "2017": 45101, "2018": 54011}
    x = 24; y = 150
    for name, kind in items:
        wd = {"year": 50, "q": 44, "m": 24}[kind]
        filled = name in rows
        b.append(R(x, y, wd - 3, 44, "s1" if filled else ("s2" if kind == "m" else "panel"), 3))
        if kind != "m":
            b.append(T(x + (wd - 3) / 2, y + 60, name, 10, "t2", "middle"))
        if filled:
            b.append(T(x + (wd - 3) / 2, y - 8, fmt(rows[name]), 11, "t1", "middle", weight="600"))
        x += wd
    b += [T(24 + 13 * 50, y + 60, "", 10), T(770, y + 60, "Oct 2025 → Sep 2026", 10, "t2", "middle"),
          T(24, 118, "Archive: 10 yearly + 3 quarterly partitions, refreshed once", 12, "t2"),
          T(w - 24, 118, "Incremental window: 12 monthly, refreshed every time", 12, "t2", "end"),
          R(24, 250, 10, 10, "s1", 2), T(40, 259, "Holds rows (99,441 total)", 12, "t2"),
          R(230, 250, 10, 10, "s2", 2), T(246, 259, "Re-processed by the second refresh (RefreshedTime moved)", 12, "t2"),
          R(640, 250, 10, 10, "panel", 2), T(656, 259, "Empty, left alone", 12, "t2"),
          T(24, 288, "The window counts back from today (2026-09-23), not from the data — so archiving 3 years would have kept 2023–2026 and dropped every row.", 12, "t2")]
    svg("incremental-refresh-partitions.svg", w, h, "Incremental refresh: 25 partitions, and only the 12 recent ones reprocess",
        "Olist IR Lab, an Import copy of fact_orders. RangeStart/RangeEnd folded to a WHERE on purchase_date. "
        "Published on an explicit OAuth cloud connection, since the SSO default can't refresh Import.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md Day 20, DAX Studio partitions + TMSCHEMA_PARTITIONS, 2026-09-23")


# ---------------------------------------------------------------- diagrams
def box(x, y, w, h, title, lines=(), cls="box", size=13):
    out = [R(x, y, w, h, cls, 8), T(x + 10, y + 20, title, size, "t1", weight="600")]
    for i, ln in enumerate(lines):
        out.append(T(x + 10, y + 38 + i * 16, ln, 11, "t2"))
    return "".join(out)


def arrow(x1, y1, x2, y2, dashed=False):
    import math
    a = math.atan2(y2 - y1, x2 - x1); hx, hy = x2 - 8 * math.cos(a), y2 - 8 * math.sin(a)
    p1 = (hx - 4 * math.sin(a), hy + 4 * math.cos(a)); p2 = (hx + 4 * math.sin(a), hy - 4 * math.cos(a))
    return (f'<line x1="{x1}" y1="{y1}" x2="{hx:.1f}" y2="{hy:.1f}" class="{"edgeb" if dashed else "edge"}" stroke-width="1.5"/>'
            f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" class="t3"/>')


def architecture():
    w, h = 1100, 640; b = []
    b.append(box(24, 100, 170, 96, "Olist CSVs · 9 files", ["~100k orders, 2016–2018", "Kaggle, CC BY-NC-SA 4.0", "+ 3 synthetic name files"]))
    b.append(T(234, 92, "OlistLH — schema-enabled lakehouse, OneLake-first (user's identity mode)", 13, "t1", weight="600"))
    b.append(R(224, 100, 620, 250, "panel", 10))
    b.append(box(240, 116, 140, 110, "bronze", ["12 tables, all-string", "raw == bronze: 9/9 OK", "1,000,163 geo points"], "boxd"))
    b.append(box(400, 116, 140, 110, "silver", ["8 tables, typed", "natural grain, source IDs", "geo → 19,173 prefixes"], "boxc"))
    b.append(box(560, 116, 140, 110, "gold", ["star schema, INT keys", "SCD2 dim_customer", "header → lines + bridge"], "boxa"))
    b.append(box(720, 116, 110, 110, "meta", ["profile", "watermark", "load errors"]))
    b.append(box(240, 240, 290, 96, "Notebooks (PySpark)", ["Bronze → Silver → SCD2 → Gold", "P2 Rebuild pipeline ≈ 7½ min", "key sums identical before/after"]))
    b.append(box(546, 240, 284, 96, "Pipelines", ["P2 Incremental: Lookup → If → merge", "P2 Maintenance: OPTIMIZE if > 20 files", "P2 Fault Tolerance: Copy, skip rows"]))
    b += [arrow(194, 150, 240, 150), arrow(380, 170, 400, 170), arrow(540, 170, 560, 170)]
    b.append(box(24, 230, 170, 106, "Dataflow Gen2", ["Profile Bronze: profiling,", "folding, staging lab", "M Drill"]))
    b.append(box(24, 380, 170, 96, "OlistWH (Warehouse)", ["CTAS copies from gold", "view, 2 functions, proc", "constraints NOT ENFORCED"]))
    b.append(box(224, 380, 290, 96, "OlistEH (Eventhouse, KQL)", ["orders + customers, 198,882 rows", "OneLake availability → shortcut", "silver.kql_orders (99,441)"]))
    b.append(T(560, 372, "Semantic models", 13, "t1", weight="600"))
    b.append(box(546, 380, 284, 60, "Olist Model", ["Direct Lake on OneLake · LakehousePath param"], "boxa"))
    b.append(box(546, 448, 138, 60, "Olist DL SQL", ["DL on SQL · fallback lab"]))
    b.append(box(692, 448, 138, 60, "Olist IR Lab", ["Import · incr. refresh"]))
    b.append(box(546, 516, 138, 60, "Olist Model Import", ["built via Git/TMDL"]))
    b.append(box(692, 516, 138, 60, "Olist Model Bad", ["flat table, 113,314 rows"]))
    b += [arrow(700, 350, 700, 380, True), T(708, 368, "Direct Lake reads gold", 11, "t2"), arrow(830, 410, 870, 410)]
    b.append(box(870, 380, 206, 96, "Olist Report", ["RLS / OLS · calc group", "field parameters", "windowing · info functions"], "boxa"))
    b.append(box(870, 100, 206, 110, "Git: fabric-p2-olist", ["GitHub · main · /fabric", "connected at creation", "62 real-dated commits", "definitions only, no data"], "boxb"))
    b.append(box(870, 226, 206, 110, "Deployment pipeline", ["Dev: P2 Olist", "Test: P2 Olist [Test]", "parameter rule → Test's", "own (empty) lakehouse"], "boxb"))
    b += [arrow(844, 150, 870, 150, True), arrow(844, 280, 870, 280, True), arrow(514, 428, 546, 428, True)]
    b.append(T(24, 612, "Solid arrows move data. Dashed arrows are reads, syncs or promotions: they move definitions, never data.", 12, "t2"))
    svg("architecture.svg", w, h, "P2 Olist — what was built, and how the pieces connect",
        "One workspace, Git-connected and pipeline-attached from its first minute. Lakehouse for files, Spark and Direct Lake; "
        "Warehouse for the T-SQL surface; Eventhouse for the KQL day.",
        "".join(b), "Source: P2 Olist workspace inventory (44 items) via the Fabric API, 2026-09-24")


def gold_model():
    w, h = 1000, 548; b = []
    b.append(box(40, 110, 200, 92, "dim_date", ["1,096 days · 2016–2018", "key: date_key (DATE)", "marked date table"], "boxa"))
    b.append(box(40, 250, 200, 92, "dim_customer", ["96,264 rows · SCD2", "customer_sk per version", "customer_key per person"], "boxa"))
    b.append(box(360, 190, 230, 110, "fact_orders (header)", ["99,441 orders", "status, dates, durations,", "payment total, review score", "775 with no lines"], "boxc"))
    b.append(box(700, 190, 250, 110, "fact_order_items (lines)", ["112,650 lines", "price, freight, distance_km,", "is_same_state", "no date column of its own"], "boxc"))
    b.append(box(700, 360, 120, 92, "dim_product", ["32,952", "Type 1"], "boxa"))
    b.append(box(830, 360, 120, 92, "dim_seller", ["3,096 · Type 1", "geo copied in"], "boxa"))
    b.append(box(360, 380, 230, 92, "bridge_order_payment", ["103,886 payments", "2,246 orders, 2 types"], "boxd"))
    b.append(box(40, 400, 200, 72, "dim_payment_type", ["5 types + Unknown"], "boxa"))
    b += [arrow(240, 150, 360, 220), T(250, 150, "purchase_date · active", 11, "t2"),
          arrow(240, 170, 360, 250, True), T(246, 222, "delivered, estimated", 11, "t2"), T(246, 236, "(inactive)", 11, "t2"),
          arrow(240, 296, 360, 270), T(256, 300, "customer_sk", 11, "t2"),
          arrow(590, 245, 700, 245), T(612, 238, "order_key", 11, "t2"),
          arrow(760, 360, 780, 300), arrow(890, 360, 870, 300),
          arrow(475, 300, 475, 380), T(482, 344, "order_key", 11, "t2"),
          arrow(240, 436, 360, 426), T(250, 452, "payment_type_sk", 11, "t2")]
    t, _ = TW(40, 494, "All one-to-many, single direction: filters flow downhill. “Orders containing a category” and “orders by payment type” go two-way inside the measure only (CROSSFILTER).", 920, 12, "t2"); b.append(t)
    svg("gold-star-schema.svg", w, h + 12, "The gold model: header → lines, a payments bridge, SCD2 customers",
        "No dim_order: fact_orders is both the order-level fact and the “one” side for the lines. No geo dimension: city, state "
        "and lat/lng are copied onto each dimension, so “state” can't silently mean the wrong one. Every -1 Unknown count is 0.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md “Before Day 10” and Days 13–15; row counts from OneLake, 2026-09-24")


def pipelines():
    w, h = 1000, 560; b = [T(24, 100, "P2 Incremental — watermark-driven, idempotent", 14, "t1", weight="600")]
    b += [box(24, 112, 150, 64, "Get watermark", ["Lookup · load_watermark"]),
          box(200, 112, 160, 64, "Count New Orders", ["Notebook · exit(str(n))"]),
          box(386, 112, 140, 64, "If new > 0", ["int(exitValue) > 0"], "boxd"),
          box(560, 104, 190, 56, "Load Orders Increment", ["MERGE orders + lines"], "boxc"),
          box(560, 168, 190, 40, "False: nothing", [], "box"),
          box(790, 104, 180, 56, "Log Error", ["On fail → meta.load_errors"], "boxb"),
          box(24, 196, 500, 44, "Land raw CSVs — ForEach × 9 → Copy data → staging (runs alongside)", [])]
    b += [arrow(174, 144, 200, 144), arrow(360, 144, 386, 144), arrow(526, 132, 560, 132), arrow(526, 170, 560, 186),
          arrow(750, 132, 790, 132, True)]
    b.append(T(24, 262, "Run 1: 45,430 orders / 51,234 lines · increment 54,011 / 61,416 · run again: 0 / 0. Gotchas: connect the arrow before the expression; toggle the parameter cell or the defaults re-run.", 11, "t2"))
    b.append(T(24, 300, "P2 Rebuild — the one button", 14, "t1", weight="600"))
    xs = [24, 234, 444, 654]
    for x, (n, t) in zip(xs, [("Bronze Build", "2m 16s"), ("Silver Build", "2m 10s"), ("Dim Customer SCD2", "1m 12s"), ("Gold Build", "1m 41s")]):
        b.append(box(x, 312, 190, 56, n, [t], "boxc"))
    b += [arrow(214, 340, 234, 340), arrow(424, 340, 444, 340), arrow(634, 340, 654, 340)]
    b.append(T(24, 390, "One shared Spark session (high concurrency + session tag), or the 8-core trial refuses the second notebook with HTTP 430. Key sums identical before and after: nothing re-keyed.", 11, "t2"))
    b.append(T(24, 428, "P2 Maintenance — OPTIMIZE only when it's needed", 14, "t1", weight="600"))
    b += [box(24, 440, 170, 56, "Check Files", ["DESCRIBE DETAIL → numFiles"]), box(220, 440, 150, 56, "If > 20 files", [], "boxd"),
          box(400, 440, 170, 56, "Optimize Table", ["Run 1: 1m 16s + 1m 5s"], "boxc"), box(400, 500, 170, 36, "False: skipped (run 2)", [])]
    b += [arrow(194, 468, 220, 468), arrow(370, 462, 400, 462), arrow(370, 480, 400, 514)]
    svg("pipelines.svg", w, h + 10, "Three pipelines, four control-flow pieces: Lookup, If Condition, ForEach, On-fail",
        "Pipeline incremental load decides which rows move; model incremental refresh (Day 20) decides which partitions reprocess.", "".join(b), "Source: DP600_BUILD_GUIDE.md Days 11, 13, 14 — Monitor hub runs, 2026-09-21/22")


def matrix(name, title, subtitle, cols, rows, source, colw=None, firstw=260, rowh=46, note=None):
    colw = colw or [(1000 - 48 - firstw) / len(cols)] * len(cols)
    w = int(48 + firstw + sum(colw)); h = 120 + rowh * len(rows) + (64 if note else 0) + 30
    b = []; x = 24 + firstw
    for c, cw in zip(cols, colw):
        t, _ = TW(x + 8, 108, c, cw - 12, 12, "t1", weight="600"); b.append(t); x += cw
    y = 124
    for r in rows:
        b.append(L(24, y, w - 24, y, "grid"))
        t, _ = TW(32, y + 18, r[0], firstw - 16, 12, "t1"); b.append(t)
        x = 24 + firstw
        for cell, cw in zip(r[1:], colw):
            kind, txt = cell if isinstance(cell, tuple) else ("", cell)
            if kind:
                bg = {"y": "okbg", "n": "badbg", "w": "warnbg"}[kind]
                gl = {"y": "✓", "n": "✕", "w": "!"}[kind]
                b.append(R(x + 2, y + 3, cw - 4, rowh - 6, bg, 4))
                b.append(T(x + 10, y + 19, gl, 14, {"y": "good", "n": "bad", "w": "warn"}[kind], weight="700"))
                t, _ = TW(x + 28, y + 18, txt, cw - 36, 11, "t1", lh=14); b.append(t)
            else:
                t, _ = TW(x + 8, y + 18, txt, cw - 14, 11, "t2", lh=14); b.append(t)
            x += cw
        y += rowh
    if note:
        t, _ = TW(24, y + 24, note, w - 48, 12, "t2"); b.append(t)
    svg(name, w, h, title, subtitle, "".join(b), source)


def security_by_path():
    matrix("security-by-query-path.svg", "Security is enforced where the query runs, as whom",
           "Warehouse table with T-SQL RLS (West only for this user) and dynamic data masking on email and salary. "
           "The same user, a workspace Viewer, opened a report through each path.",
           ["Rows filtered?", "Values masked?", "Why"],
           [["Import", ("n", "All rows"), ("n", "Real values"), "Refresh ran as the owner; viewers query that copy"],
            ["DirectQuery", ("y", "West only"), ("y", "Masked"), "Each query runs in SQL as the viewer (needs SSO on the connection)"],
            ["Direct Lake on SQL endpoint", ("y", "West only"), ("y", "Masked"), "RLS or masking forces fallback to DirectQuery, so SQL applies it"],
            ["Direct Lake on OneLake, over the Warehouse", ("n", "All rows"), ("n", "Real values"), "Reads Parquet with the viewer's ReadAll; SQL security never runs"],
            ["Direct Lake on OneLake, over a Lakehouse", ("y", "West only"), ("y", "Columns removed"), "OneLake security role (row filter + column list) applies"],
            ["Same user promoted to Contributor", ("n", "Reports unmasked"), ("w", "Direct SQL still masked"), "Contributor gains OneLake read; no SQL CONTROL, so T-SQL still masks"]],
           "Source: DP600_BUILD_GUIDE.md Day 1 Step 5, all paths verified for test.analyst 2026-09-17",
           colw=[150, 170, 330], firstw=300, rowh=50,
           note="Granting ReadAll on a warehouse undoes its T-SQL security for that user. A delegated-identity shortcut hands every reader the creator's access: test.north read all 5 rows, unfiltered and unmasked.")


def ten_layers():
    rows = [["1 · Entra directory roles", "Who administers the tenant", "Entra ID, not Fabric", "tenant admin, not data"],
            ["2 · Workspace roles", "Who gets into the workspace", "The workspace", "too coarse for “protect data”"],
            ["3 · Item permissions", "Who opens one item (Read, Build, ReadData, ReadAll)", "The item", "“build a report, don't touch the model” → Build"],
            ["4 · T-SQL GRANT / DENY", "Which objects", "Warehouse / SQL endpoint", "“specific objects in the warehouse”"],
            ["5 · T-SQL RLS", "Which rows, via SQL", "Warehouse / SQL endpoint", "“users see only their region” in T-SQL"],
            ["6 · T-SQL CLS", "Which columns, via SQL", "Warehouse / SQL endpoint", "SELECT * errors, column list works"],
            ["7 · Dynamic data masking", "What values look like. Not access control", "Warehouse / SQL endpoint", "“without changing the application layer”"],
            ["8 · OneLake security roles", "Tables, rows, columns in every engine", "Lakehouse", "“consistently across engines”"],
            ["9 · Model RLS / OLS", "Rows, tables, columns in reports", "Semantic model", "“only User1 sees this measure” → OLS"],
            ["10 · Sensitivity labels", "Classification that travels. Not access control", "Every item, inherited downstream", "“classify for compliance”"]]
    matrix("security-ten-layers.svg", "Ten security layers, each built and tested as a real Viewer",
           "The practice test's most-missed pattern was answering a data question with a workspace role. Read the question for the layer, then answer from that layer.",
           ["Decides", "Lives on", "Question wording that points here"], rows,
           "Source: DP600_BUILD_GUIDE.md Week 1 close; practice assessments 2026-09-03 and 2026-09-24",
           colw=[270, 200, 280], firstw=230, rowh=40,
           note="Model RLS is default-deny: once a model has any role, a Viewer in none is refused. Roles add up (OR). Hidden ≠ secured: a hidden table is still queryable; OLS makes it not exist.")


def what_travels():
    Y, N, W = "y", "n", "w"
    rows = [["Item definitions (models, reports, notebooks, pipelines)", (Y, "Yes"), (Y, "Yes"), "n/a"],
            ["Data, Files/, table schemas", (N, "No"), (N, "No: Test starts empty"), "Read in place, never copied"],
            ["Warehouse RLS policy, masks, roles", (Y, "Yes (SQL project)"), (Y, "Yes"), (N, "Never enforced through it")],
            ["Warehouse GRANT / DENY", (N, "No"), (N, "No"), (N, "No")],
            ["Warehouse users, role members", (N, "No"), (N, "No: compare stays “Different”"), "n/a"],
            ["Model roles, filters, OLS", (Y, "Yes"), (Y, "Yes"), "n/a"],
            ["Model role members", (N, "Never"), (N, "Never"), "n/a"],
            ["OneLake security roles", (W, "Off by default (DataAccessRoles)"), (N, "No"), (W, "Defined at the target only")],
            ["Connection bindings, credentials", (N, "No"), (N, "No: re-map per stage"), "Passthrough or delegated identity"],
            ["SQL endpoint identity mode", (N, "No"), (N, "No: Test came back delegated"), "n/a"],
            ["Direct Lake source path", (Y, "As text"), (W, "Only via a parameter rule"), "n/a"]]
    matrix("what-travels.svg", "What travels, and who doesn't",
           "Git, deployment pipelines and shortcuts all carry definitions. None carry identity: members, users, grants, "
           "connections and access modes are redone per environment.",
           ["Git integration", "Deployment pipeline", "OneLake shortcut"], rows,
           "Source: DP600_BUILD_GUIDE.md Days 1, 3, 4, 15 and 19 (read from the repos and the Test workspace)",
           colw=[210, 240, 230], firstw=300, rowh=40,
           note="Two traps from the Test deploy: a parameter rule changed the parameter while the Source line still held Dev's literal URL, so nothing moved. And a workspace Commit after a Git edit wrote the old definition back.")


def direct_lake_flavors():
    Y, N, W = "y", "n", "w"
    rows = [["Reads", "Delta files directly (AzureStorage.DataLake)", "Through the SQL endpoint (Sql.Database)"],
            ["Sources", (Y, "One or more Fabric items"), (W, "One item")],
            ["SQL views", (N, "Can't add them"), (W, "Allowed, but always DirectQuery")],
            ["When it can't read Delta", (Y, "Errors (no fallback)"), (W, "Falls back to DirectQuery, silently")],
            ["SQL-endpoint RLS / CLS", (W, "Ignored: reads the files"), (Y, "Applied, via fallback")],
            ["Composite with Import tables", (Y, "Yes"), (N, "No")],
            ["Calculated columns", (Y, "Preview: user-context, not stored"), (N, "Grayed out")],
            ["Deployment rebind", (W, "Parameter rule on the path only"), (Y, "Data source rule")],
            ["Test as role", (N, "Blocked by SSO: sign in as the user"), (Y, "Works")]]
    matrix("direct-lake-onelake-vs-sql.svg", "Direct Lake on OneLake vs Direct Lake on SQL, built both ways",
           "Olist Model (on OneLake) and Olist DL SQL over the same gold tables. The dialog defaults to “on OneLake”; the lakehouse's New semantic model button makes that flavor.",
           ["On OneLake", "On SQL endpoint"], rows,
           "Source: DP600_BUILD_GUIDE.md Days 15, 19, 24, 25; Microsoft's Direct Lake overview (2026-09-18)",
           colw=[330, 330], firstw=260, rowh=40,
           note="Also found: Edit tables fails while the OneLake path is a parameter (add tables first), lists new tables only after the SQL endpoint syncs, "
                "and after any Git update a Direct Lake model answers nothing until Refresh now reframes it.")


def spark_math():
    w, h = 960, 360; b = []
    b.append(box(24, 110, 200, 84, "Trial capacity: FTL4", ["4 capacity units (CU)", "F2 would be 2 CU"], "boxd"))
    b.append(box(264, 110, 200, 84, "8 Spark vCores", ["1 CU = 2 Spark vCores", "F2: 4 vCores"], "boxa"))
    b += [arrow(224, 152, 264, 152), arrow(464, 152, 504, 130), arrow(464, 152, 504, 214)]
    b.append(box(504, 96, 430, 70, "Starter pool, Medium node = 8 vCores", ["One session fills all 8. The next notebook gets HTTP 430.", "Jobs tab: 8/8 used by one session"], "boxb"))
    b.append(box(504, 180, 430, 70, "Custom pool, Small node = 4 vCores", ["Two sessions fit (Monitor: two In progress).", "Price: not pre-warmed, 30 s – 5 min to start"], "boxc"))
    b.append(T(24, 290, "The hidden holders: a closed lakehouse “New Spark SQL query” tab keeps a LivySession for its 20-minute idle timeout.", 12, "t2"))
    b.append(T(24, 308, "The pipeline fix: high concurrency + one session tag, so notebook activities share a session (their Monitor names carry HC_).", 12, "t2"))
    b.append(T(24, 326, "Not Spark (own engines, still CU): Copy activity, Dataflow Gen2, SQL endpoint/Warehouse, semantic models, KQL, Python/T-SQL notebooks.", 12, "t2"))
    svg("spark-capacity-math.svg", w, h, "Why only one notebook could run: the capacity arithmetic",
        "Days 11–14 hit HTTP 430 TooManyRequestsForCapacity again and again. The cause was one line of arithmetic, found on exam-4's Jobs tab.",
        "".join(b), "Source: DP600_BUILD_GUIDE.md exam-4, 2026-09-24")


if __name__ == "__main__":
    for f in (practice_scores, headline_numbers, delta_maintenance, dax_costs, fallback, model_size, pareto, rls_leak,
              scd2_waterfall, yoy, partitions, architecture, gold_model, pipelines, security_by_path, ten_layers,
              what_travels, direct_lake_flavors, spark_math):
        f()

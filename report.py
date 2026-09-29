"""Charts (shared by the on-screen dashboard) and the one-page JPG export."""
import base64
import datetime as dt
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgb  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

LOGO_PATH = Path(__file__).parent / "logo.png"
COMPANY = "METRO M.D.F. CO., LTD"


def reject_over_target(reject_pct):
    """True when %Reject (rounded to the 2 decimals that are displayed) is above the target."""
    return reject_pct is not None and round(reject_pct, 2) > REJECT_TARGET


def logo_data_uri():
    try:
        return "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()
    except OSError:
        return None


# ---- palette: METRO logo (lime / olive / greys) + deep greens ----
GREEN_DD = "#032618"   # darkest green (banner start)
GREEN_D = "#113B25"    # dark green (headings, key numbers)
GREEN = "#276239"      # main green (table headers, bars)
GREEN_L = "#538761"    # light green
OLIVE = "#A3B21B"      # logo olive
LIME = "#DCE673"       # logo lime
GREY_D = "#606062"     # logo dark grey
GREY = "#8C8C8C"       # logo mid grey
CREAM = "#F5F7EC"      # page background (very light lime tint)
INK = "#25292A"
MUTED = "#6B6E6A"
LINE = "#DDE4C5"
ZEBRA = "#F8FAF1"
SIDEBAR = "#E8EDD3"
ROW_LINE = "#E9EEDB"
TOT_BG = "#E6EDCB"
SOFT = "#EEF3C6"       # light text on the dark banner
RED = "#C62828"        # alert colour (reject above target)
REJECT_TARGET = 1.0    # % Reject after press target; above it the KPI turns red
OTHERS = "#BFC2BA"
PIE_COLORS = [GREEN_D, OLIVE, GREEN, LIME, GREY_D, GREEN_L, GREY, "#C7D68B", "#8FB89A"]


def _pick_font():
    have = {f.name for f in fm.fontManager.ttflist}
    for n in ("Segoe UI", "Inter", "Calibri", "Arial", "Liberation Sans", "DejaVu Sans"):
        if n in have:
            return n
    return "sans-serif"


plt.rcParams["font.family"] = _pick_font()
plt.rcParams["axes.unicode_minus"] = False


def _text_color_on(hex_color):
    r, g, b = to_rgb(hex_color)
    return INK if (0.299 * r + 0.587 * g + 0.114 * b) > 0.5 else "white"


# =====================================================================
# Chart drawing (works on any Axes)
# =====================================================================
def draw_resin_bar(ax, gt, label_fs=10.5):
    ax.set_facecolor("none")
    if gt.empty:
        ax.text(0.5, 0.5, "No resin usage in the selected period", ha="center", va="center",
                color=MUTED, transform=ax.transAxes)
        ax.axis("off")
        return
    labels = list(gt["Resin"])
    vals = gt["Net used (kg)"].to_numpy(float)
    shares = gt["Share (%)"].to_numpy(float)
    n = len(labels)
    y = np.arange(n)[::-1]
    mx = vals.max()
    colors = [GREEN_D if i == 0 else OLIVE if i > 2 else GREEN for i in range(n)]
    ax.barh(y, vals, height=0.62, color=colors, zorder=3)
    for yi, v, s in zip(y, vals, shares):
        ax.text(v + mx * 0.012, yi, f"{v:,.0f} kg  ({s:.1f}%)", va="center", ha="left",
                fontsize=label_fs, color=INK, zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=label_fs + 0.5, color=INK, fontweight="semibold")
    ax.set_xlim(0, mx * 1.30)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.tick_params(axis="x", labelsize=label_fs - 1, colors=MUTED, length=0)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Resin usage (kg)", fontsize=label_fs, color=MUTED, labelpad=8)
    ax.set_ylabel("Resin code", fontsize=label_fs, color=MUTED, labelpad=8)
    ax.grid(axis="x", color=LINE, linewidth=0.9, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)


def draw_pie(ax, labels, values, aspect, legend_fs=10, pct_fs=10):
    """Pie on the left of the axes, legend (name + share) on the right. aspect = axes width / height."""
    total = float(sum(values))
    ax.set_facecolor("none")
    if total <= 0:
        ax.text(0.5, 0.5, "No data in the selected period", ha="center", va="center",
                color=MUTED, transform=ax.transAxes)
        ax.axis("off")
        return
    colors = []
    for i, lab in enumerate(labels):
        colors.append(OTHERS if lab.startswith("Others (") else PIE_COLORS[i % len(PIE_COLORS)])
    wedges, _, autotexts = ax.pie(
        values, colors=colors, startangle=90, counterclock=False, radius=1.0, center=(0, 0),
        autopct=lambda p: f"{p:.1f}%" if p >= 4 else "", pctdistance=0.72,
        wedgeprops=dict(edgecolor="white", linewidth=1.8),
        textprops=dict(fontsize=pct_fs, fontweight="bold"))
    for w, t in zip(wedges, autotexts):
        t.set_color(_text_color_on(matplotlib.colors.to_hex(w.get_facecolor())))
    ax.set_xlim(-1.1, -1.1 + 2.2 * aspect)
    ax.set_ylim(-1.1, 1.1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(wedges, [f"{l}   {v / total * 100:.1f}%" for l, v in zip(labels, values)],
              loc="center left", bbox_to_anchor=(1 / aspect + 0.03, 0.5), frameon=False,
              fontsize=legend_fs, labelcolor=INK, handlelength=1.1, handleheight=1.1,
              borderaxespad=0, labelspacing=0.7)


def draw_table(ax, headers, rows, col_x, aligns, width, row_h=0.3, head_h=0.38, fs=9):
    """Draw a simple styled table. Axes units are inches; col_x = left edge (or right edge for 'r')."""
    height = head_h + row_h * len(rows)
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), width, head_h, fc=GREEN, ec="none"))
    for h, x, a in zip(headers, col_x, aligns):
        ax.text(x, head_h / 2, h, ha="left" if a == "l" else "right", va="center",
                color="white", fontsize=fs, fontweight="bold")
    for i, row in enumerate(rows):
        y0 = head_h + i * row_h
        if i % 2 == 1:
            ax.add_patch(Rectangle((0, y0), width, row_h, fc=ZEBRA, ec="none"))
        for v, x, a in zip(row, col_x, aligns):
            ax.text(x, y0 + row_h / 2, v, ha="left" if a == "l" else "right", va="center",
                    color=INK, fontsize=fs)
    ax.plot([0, width], [height, height], color=LINE, lw=1)


# =====================================================================
# On-screen figures
# =====================================================================
def fig_resin(gt):
    n = max(len(gt), 1)
    fig, ax = plt.subplots(figsize=(11, max(3.0, 0.46 * n + 1.1)), dpi=150)
    fig.patch.set_facecolor("white")
    draw_resin_bar(ax, gt)
    fig.tight_layout()
    return fig


def fig_pie(labels, values, width=6.4, height=4.2):
    fig = plt.figure(figsize=(width, height), dpi=150)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    draw_pie(ax, labels, values, aspect=width / height)
    return fig


def draw_product_trend(ax, tbl, compact=False):
    """Draw monthly consumption (kg/m³) of one product on ax. tbl comes from data_loader.product_monthly."""
    ax.set_facecolor("none")
    y = tbl["Consumption (kg/m³)"].to_numpy(float)
    x = np.arange(len(tbl))
    ok = ~np.isnan(y)
    if not ok.any():
        ax.text(0.5, 0.5, "No production in the file", ha="center", va="center", color=MUTED,
                fontsize=9 if compact else 11, transform=ax.transAxes)
        ax.axis("off")
        return
    fs_val, fs_tick = (8.5, 8.5) if compact else (10, 9.5)
    ax.plot(x, y, color=GREEN, lw=2.0 if compact else 2.4, marker="o", ms=5.5 if compact else 7,
            mfc="white", mec=GREEN, mew=2.0 if compact else 2.2, zorder=3)
    lo, hi = float(np.nanmin(y)), float(np.nanmax(y))
    pad = max((hi - lo) * 0.25, 4.0)
    ax.set_ylim(max(0.0, lo - pad), hi + pad)
    for xi, yi in zip(x[ok], y[ok]):
        ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(0, 9 if compact else 11),
                    ha="center", fontsize=fs_val, fontweight="bold", color=GREEN_D)
    if compact:
        ticks = list(tbl["Month"])
    else:
        prod = tbl["Production (m³)"].to_numpy(float)
        ticks = [f"{m}\n{p:,.0f} m³" if not np.isnan(v) else f"{m}\n–"
                 for m, p, v in zip(tbl["Month"], prod, y)]
    ax.set_xticks(x)
    ax.set_xticklabels(ticks, fontsize=fs_tick, color=INK)
    ax.set_xlim(-0.4, len(tbl) - 0.6)
    ax.set_ylabel("Consumption (kg/m³)" if not compact else "kg/m³", fontsize=fs_tick + 0.5,
                  color=MUTED, labelpad=6)
    ax.tick_params(axis="y", labelsize=fs_tick, colors=MUTED, length=0)
    ax.tick_params(axis="x", length=0)
    ax.grid(axis="y", color=LINE, linewidth=0.9, zorder=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(LINE)


def fig_product_trend(tbl, label, year=None):
    """On-screen line chart: monthly resin consumption (kg/m³) of one product."""
    fig, ax = plt.subplots(figsize=(11, 3.9), dpi=150)
    fig.patch.set_facecolor("white")
    draw_product_trend(ax, tbl)
    ax.set_xlabel("Month" + (f" {year}" if year else "") + "   (production volume of the product shown under each month)",
                  fontsize=9.5, color=MUTED, labelpad=8)
    fig.tight_layout()
    return fig


# =====================================================================
# Two-page export (PDF and JPG): page 1 = summary, page 2 = products + top-6 monthly charts
# =====================================================================
PAGE_W, PAGE_M, BANNER_H = 14.0, 0.5, 1.95


def _text_width_in(text, fontsize, weight="bold"):
    """Width of a text in inches, measured without a renderer (works with any matplotlib backend/version)."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    return TextPath((0, 0), text, size=fontsize, prop=FontProperties(weight=weight)).get_extents().width / 72.0


class _Canvas:
    """One export page. All coordinates are in inches, y grows downwards."""

    def __init__(self, height, dpi):
        self.W, self.H, self.M, self.dpi = PAGE_W, height, PAGE_M, dpi
        self.CW = PAGE_W - 2 * PAGE_M
        self.fig = plt.figure(figsize=(self.W, self.H), dpi=dpi)
        self.fig.patch.set_facecolor(CREAM)
        self.bg = self.fig.add_axes([0, 0, 1, 1])
        self.bg.set_xlim(0, self.W)
        self.bg.set_ylim(self.H, 0)
        self.bg.axis("off")

    def sub(self, x, y, w, h):
        return self.fig.add_axes([x / self.W, 1 - (y + h) / self.H, w / self.W, h / self.H])

    def card(self, x, y, w, h):
        self.bg.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.14",
                                         fc="white", ec=LINE, lw=1.2))

    def section(self, y, text):
        self.bg.add_patch(Rectangle((self.M, y), 0.09, 0.32, fc=GREEN, ec="none"))
        self.bg.text(self.M + 0.24, y + 0.16, text, fontsize=15, fontweight="bold", color=GREEN_D, va="center")


def _draw_banner(cv, line, period, page):
    W, M, bg, sub = cv.W, cv.M, cv.bg, cv.sub
    cmap = LinearSegmentedColormap.from_list("brand", [GREEN_DD, GREEN_D, GREEN, GREEN_L])
    bg.imshow(np.linspace(0, 1, 512).reshape(1, -1), extent=[0, W, BANNER_H, 0], aspect="auto",
              cmap=cmap, zorder=0)
    for k, col in enumerate((LIME, OLIVE, GREY_D, GREY)):  # 4-colour strip echoing the logo
        bg.add_patch(Rectangle((k * W / 4, BANNER_H - 0.09), W / 4, 0.09, fc=col, ec="none", zorder=1))
    bg.set_xlim(0, W)
    bg.set_ylim(cv.H, 0)
    sub_txt = f"{line}  |  {period}"
    bg.text(M + 0.1, 0.68, "Monthly Resin Utilization Dashboard", fontsize=27, fontweight="bold", color="white", va="center")
    bg.text(M + 0.1, 1.38, sub_txt, fontsize=27 if len(sub_txt) <= 32 else 21, fontweight="bold",
            color=SOFT, va="center")
    logo_w, logo_h = 1.0, 1.3
    lx, ly = W - M - 0.05 - logo_w, (BANNER_H - logo_h) / 2
    try:
        from PIL import Image
        limg = Image.open(LOGO_PATH).convert("RGB")
        lw, lh = limg.size
        logo_w = logo_h * lw / lh
        lx = W - M - 0.05 - logo_w
        bg.add_patch(FancyBboxPatch((lx, ly), logo_w, logo_h, boxstyle="round,pad=0,rounding_size=0.1",
                                    fc="white", ec="none", zorder=3))
        axl = sub(lx + 0.08, ly + 0.08, logo_w - 0.16, logo_h - 0.16)
        axl.imshow(limg)
        axl.axis("off")
        tx_r = lx - 0.3
    except Exception:  # noqa: BLE001
        tx_r = W - M - 0.1
    bg.text(tx_r, 0.80, COMPANY, fontsize=15, fontweight="bold", color="white", va="center", ha="right")
    bg.text(tx_r, 1.28, f"Generated {dt.date.today():%d %b %Y}   |   Page {page} of 2", fontsize=11,
            color=SOFT, va="center", ha="right")


def _draw_footer(cv, foot_y, line):
    bg, M, W = cv.bg, cv.M, cv.W
    bg.plot([M, W - M], [foot_y, foot_y], color=LINE, lw=1)
    bg.text(M, foot_y + 0.25, f"Source: {line} production report (Excel). Resin = net used (TT) per resin code; "
            "Reject % = Reject after press ÷ Production output × 100.", fontsize=8.5, color=MUTED, va="center")


def _page1(kp, gt, bt, thk, thk_info, line, period, dpi):
    M = PAGE_M
    n_res = max(len(gt), 1)
    n_bt = len(bt)
    kpi_y, kpi_h = BANNER_H + 0.4, 1.25
    s1_y = kpi_y + kpi_h + 0.4
    card1_y = s1_y + 0.45
    card1_h = max(3.2, 0.44 * n_res + 1.4)
    s2_y = card1_y + card1_h + 0.4
    card2_y = s2_y + 0.45
    card2_h = max(4.5, 0.38 + 0.31 * n_bt + 1.0)
    s3_y = card2_y + card2_h + 0.4
    card3_y = s3_y + 0.45
    card3_h = 4.5
    foot_y = card3_y + card3_h + 0.3
    cv = _Canvas(foot_y + 0.55, dpi)
    fig, bg, sub, card, section, CW, W = cv.fig, cv.bg, cv.sub, cv.card, cv.section, cv.CW, cv.W

    _draw_banner(cv, line, period, 1)

    # ---- KPI cards ----
    gap = 0.3
    kw = (CW - 2 * gap) / 3
    pct = "-" if kp["reject_pct"] is None else f"{kp['reject_pct']:.2f}"
    kpi_items = [("PRODUCTION OUTPUT", f"{kp['prod']:,.2f}", "m³", GREEN),
                 ("REJECT AFTER PRESS", f"{kp['reject']:,.2f}", "m³", GREEN_D),
                 ("% REJECT AFTER PRESS", pct, "%", RED if reject_over_target(kp["reject_pct"]) else GREEN_D)]
    for i, (lab, val, unit, col) in enumerate(kpi_items):
        x = M + i * (kw + gap)
        card(x, kpi_y, kw, kpi_h)
        bg.add_patch(Rectangle((x, kpi_y + 0.12), 0.09, kpi_h - 0.24, fc=col, ec="none"))
        bg.text(x + 0.35, kpi_y + 0.38, lab, fontsize=11, color=MUTED, fontweight="semibold", va="center")
        bg.text(x + 0.35, kpi_y + 0.86, val, fontsize=27, fontweight="bold", color=col, va="center")
        w_in = _text_width_in(val, 27)
        bg.text(x + 0.35 + w_in + 0.12, kpi_y + 0.9, unit, fontsize=13, color=MUTED, va="center")

    # ---- resin bar chart ----
    section(s1_y, "Total Resin Usage Summary (kg)")
    card(M, card1_y, CW, card1_h)
    total_kg = float(gt["Net used (kg)"].sum()) if len(gt) else 0.0
    bg.text(W - M - 0.3, s1_y + 0.16, f"Total: {total_kg:,.0f} kg", fontsize=12, fontweight="bold",
            color=INK, va="center", ha="right")
    ax = sub(M + 1.75, card1_y + 0.2, CW - 2.05, card1_h - 0.4)
    draw_resin_bar(ax, gt, label_fs=10.5)

    # ---- board type ----
    section(s2_y, "Production by Board Type")
    card(M, card2_y, CW, card2_h)
    labels, values = _top_n(bt)
    pie_w, pie_h = 5.9, 3.9
    axp = sub(M + 0.25, card2_y + (card2_h - pie_h) / 2, pie_w, pie_h)
    draw_pie(axp, labels, values, aspect=pie_w / pie_h, legend_fs=9.5)
    tw = CW - pie_w - 0.25 - 0.3 - 0.25
    tx = M + 0.25 + pie_w + 0.3
    label_col = bt.columns[1]
    heads = ["#", label_col.replace(" Group", ""), "Prod. (m³)", "Resin (kg)", "Share %", "kg/m³"]
    rows = [[str(int(r["Rank"])), str(r[label_col]), f"{r['Production (m³)']:,.1f}",
             f"{r['Resin (kg)']:,.0f}", f"{r['Share (%)']:.1f}",
             "-" if r["Consumption (kg/m³)"] != r["Consumption (kg/m³)"] else f"{r['Consumption (kg/m³)']:.1f}"]
            for _, r in bt.iterrows()]
    cx = [0.12, 0.5, tw * 0.62, tw * 0.79, tw * 0.90, tw - 0.08]
    th_h = 0.38 + 0.31 * len(rows)
    axt = sub(tx, card2_y + 0.3, tw, th_h)
    draw_table(axt, heads, rows, cx, ["l", "l", "r", "r", "r", "r"], tw, row_h=0.31, head_h=0.38, fs=9)
    bg.text(tx, card2_y + 0.3 + th_h + 0.2,
            "Consumption (kg/m³) = total resin used ÷ production volume of the same board type.",
            fontsize=8.5, color=MUTED, va="center")

    # ---- thickness ----
    section(s3_y, "Production by Thickness Range")
    card(M, card3_y, CW, card3_h)
    tl = list(thk["Thickness Range"])
    tv = [float(v) for v in thk["Production (m³)"]]
    keep = [i for i, v in enumerate(tv) if v > 0]
    axp2 = sub(M + 0.25, card3_y + 0.3, pie_w, pie_h)
    if keep:
        draw_pie(axp2, [tl[i] for i in keep], [tv[i] for i in keep], aspect=pie_w / pie_h, legend_fs=10)
    else:
        draw_pie(axp2, [], [], aspect=pie_w / pie_h)
    trows = [[r["Thickness Range"], f"{r['Production (m³)']:,.1f}", f"{r['Share (%)']:.1f}"]
             for _, r in thk.iterrows()]
    tot = float(thk["Production (m³)"].sum())
    trows.append(["Total (in ranges)", f"{tot:,.1f}", "100.0" if tot else "-"])
    cx3 = [0.12, tw * 0.72, tw - 0.1]
    th3 = 0.42 + 0.36 * len(trows)
    ax3 = sub(tx, card3_y + 0.55, tw, th3)
    draw_table(ax3, ["Thickness range", "Production (m³)", "Share (%)"], trows, cx3, ["l", "r", "r"], tw,
               row_h=0.36, head_h=0.42, fs=10)
    note = f"Shares are based on the volume inside the ranges ({thk_info['classified']:,.1f} m³)."
    bg.text(tx, card3_y + 0.55 + th3 + 0.22, note, fontsize=8.5, color=MUTED, va="center")
    if thk_info["outside_m3"] > 0.05:
        vals = ", ".join(f"{v:g}" for v in thk_info["outside_values"])
        bg.text(tx, card3_y + 0.55 + th3 + 0.48,
                f"Not in any range (thickness {vals} mm): {thk_info['outside_m3']:,.1f} m³",
                fontsize=8.5, color=GREEN_D, va="center", fontweight="semibold")

    _draw_footer(cv, foot_y, line)
    return fig


def _page2(prod, trends, year, line, period, dpi):
    M = PAGE_M
    n_half = (len(prod) + 1) // 2
    s1_y = BANNER_H + 0.4
    card1_y = s1_y + 0.45
    card1_h = 0.3 + 0.36 + 0.27 * n_half + 0.75
    n_tr = len(trends)
    n_rows = min(3, n_tr)                       # left column = first 3, right column = next 3
    ch_h, ch_gap = 2.65, 0.15
    s2_y = card1_y + card1_h + 0.4
    card2_y = s2_y + 0.45
    card2_h = (0.25 + n_rows * ch_h + (n_rows - 1) * ch_gap + 0.55) if n_tr else 0.0
    foot_y = (card2_y + card2_h + 0.3) if n_tr else (card1_y + card1_h + 0.3)
    cv = _Canvas(foot_y + 0.55, dpi)
    bg, sub, card, section, CW = cv.bg, cv.sub, cv.card, cv.section, cv.CW

    _draw_banner(cv, line, period, 2)

    # ---- product table (2 columns) ----
    section(s1_y, "Production by Product (Thickness + Board Type Group)")
    card(M, card1_y, CW, card1_h)
    colw = (CW - 0.5 - 0.35) / 2
    heads = ["#", "Product", "Prod. (m³)", "kg/m³"]
    cxp = [0.10, 0.45, colw * 0.80, colw - 0.08]
    for k in range(2):
        part = prod.iloc[k * n_half:(k + 1) * n_half]
        if part.empty:
            continue
        rws = [[str(int(q["Rank"])), str(q["Product"]), f"{q['Production (m³)']:,.1f}",
                "-" if q["Consumption (kg/m³)"] != q["Consumption (kg/m³)"] else f"{q['Consumption (kg/m³)']:.1f}"]
               for _, q in part.iterrows()]
        hh = 0.36 + 0.27 * len(rws)
        axk = sub(M + 0.25 + k * (colw + 0.35), card1_y + 0.3, colw, hh)
        draw_table(axk, heads, rws, cxp, ["l", "l", "r", "r"], colw, row_h=0.27, head_h=0.36, fs=8.5)
    bg.text(M + 0.25, card1_y + card1_h - 0.28,
            "Product = thickness (mm) + board type group. Consumption (kg/m³) = total resin used ÷ production volume of the same product.",
            fontsize=8.5, color=MUTED, va="center")

    # ---- top-6 monthly consumption charts: 3 on the left, 3 on the right ----
    if n_tr:
        section(s2_y, f"Monthly Resin Consumption by Product – Top {n_tr}")
        card(M, card2_y, CW, card2_h)
        cw = (CW - 0.5 - 0.35) / 2
        for i, (label, tbl) in enumerate(trends):
            col, row = (0, i) if i < 3 else (1, i - 3)
            x0 = M + 0.25 + col * (cw + 0.35)
            y0 = card2_y + 0.25 + row * (ch_h + ch_gap)
            bg.text(x0 + 0.08, y0 + 0.16, f"#{i + 1}   {label}", fontsize=11, fontweight="bold",
                    color=GREEN_D, va="center")
            ax = sub(x0 + 0.65, y0 + 0.42, cw - 0.8, ch_h - 0.42 - 0.42)
            draw_product_trend(ax, tbl, compact=True)
        bg.text(M + 0.25, card2_y + card2_h - 0.27,
                f"Consumption per month = resin used ÷ production volume of the product in that month; all months in the file ({year}). "
                "Months without production are left blank.", fontsize=8.5, color=MUTED, va="center")

    _draw_footer(cv, foot_y, line)
    return cv.fig


def build_exports(kp, gt, bt, thk, thk_info, line, period, prod, trends, year, dpi=150):
    """Return (jpg_page1, jpg_page2, pdf_2_pages) as bytes."""
    from matplotlib.backends.backend_pdf import PdfPages
    matplotlib.rcParams["pdf.fonttype"] = 42
    figs = [_page1(kp, gt, bt, thk, thk_info, line, period, dpi),
            _page2(prod, trends, year, line, period, dpi)]
    jpgs = []
    for f in figs:
        buf = io.BytesIO()
        f.savefig(buf, format="jpeg", dpi=dpi, facecolor=CREAM, pil_kwargs={"quality": 92})
        jpgs.append(buf.getvalue())
    pbuf = io.BytesIO()
    with PdfPages(pbuf) as pdf:
        for f in figs:
            pdf.savefig(f, facecolor=CREAM)
    for f in figs:
        plt.close(f)
    return jpgs[0], jpgs[1], pbuf.getvalue()


def _top_n(bt, n=8):
    label_col = bt.columns[1]
    top = bt.head(n)
    labels = list(top[label_col])
    values = [float(v) for v in top["Production (m³)"]]
    rest = float(bt["Production (m³)"].iloc[n:].sum())
    if rest > 0:
        labels.append(f"Others ({len(bt) - n})")
        values.append(rest)
    return labels, values

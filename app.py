import html
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

import data_loader as dl
import report as rp

GROUP_CSV = Path(__file__).parent / "board_groups.csv"
GREEN_DD, GREEN_D, GREEN, GREEN_L = rp.GREEN_DD, rp.GREEN_D, rp.GREEN, rp.GREEN_L

st.set_page_config(page_title="Monthly Resin Utilization Dashboard", page_icon="🌲", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input {{ font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important; }}
.stApp {{ background: {rp.CREAM}; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1320px; }}
[data-testid="stSidebar"] {{ background: {rp.SIDEBAR}; border-right: 1px solid {rp.LINE}; }}
[data-testid="stSidebar"] h2 {{ color: {GREEN_D}; font-weight: 700; }}
header[data-testid="stHeader"] {{ background: transparent; }}

.banner {{ background: linear-gradient(90deg, {rp.LIME} 0 25%, {rp.OLIVE} 25% 50%, {rp.GREY_D} 50% 75%, {rp.GREY} 75% 100%) left bottom / 100% 7px no-repeat,
                       linear-gradient(105deg, {GREEN_DD} 0%, {GREEN_D} 35%, {GREEN} 70%, {GREEN_L} 100%);
           border-radius: 18px; padding: 28px 36px; color: #fff; display: flex;
           justify-content: space-between; align-items: center; box-shadow: 0 6px 18px rgba(17,59,37,.22); }}
.banner .t {{ font-size: 30px; font-weight: 800; letter-spacing: .5px; line-height: 1.15; }}
.banner .s {{ font-size: 30px; font-weight: 800; letter-spacing: .5px; line-height: 1.15; color: {rp.SOFT}; margin-top: 8px; }}
.banner .s .sep {{ color: rgba(255,255,255,.55); font-weight: 400; margin: 0 12px; }}
@media (max-width: 900px) {{ .banner .t, .banner .s {{ font-size: 21px; }} .banner .s .sep {{ margin: 0 7px; }} }}
.banner .rw {{ display:flex; align-items:center; gap:22px; }}
.banner .r {{ text-align: right; font-size: 16px; font-weight: 700; letter-spacing:.3px; }}
.banner .logo {{ background:#fff; border-radius:14px; padding:8px 12px; height:96px; display:flex; align-items:center; box-shadow:0 2px 8px rgba(0,0,0,.18); }}
.banner .logo img {{ height:80px; width:auto; display:block; }}
.banner .r small {{ display:block; font-weight: 400; color:{rp.SOFT}; margin-top:6px; font-size: 13px; }}

.kpi {{ background:#fff; border:1px solid {rp.LINE}; border-left:7px solid {GREEN}; border-radius:14px;
        padding:18px 24px; box-shadow:0 2px 8px rgba(17,59,37,.07); }}
.kpi.d {{ border-left-color:{GREEN_D}; }}
.kpi .lbl {{ font-size:12.5px; color:{rp.MUTED}; font-weight:600; letter-spacing:.8px; text-transform:uppercase; }}
.kpi .val {{ font-size:36px; font-weight:800; color:{GREEN}; line-height:1.2; margin-top:4px; }}
.kpi.d .val {{ color:{GREEN_D}; }}
.kpi.alert {{ border-left-color:{rp.RED}; }}
.kpi.alert .val {{ color:{rp.RED}; }}
.kpi .unit {{ font-size:16px; font-weight:500; color:{rp.MUTED}; margin-left:8px; }}

.sec {{ display:flex; align-items:center; justify-content:space-between; margin:2px 0 10px 0; }}
.sec .n {{ font-size:19px; font-weight:700; color:{GREEN_D}; border-left:6px solid {GREEN}; padding-left:12px; }}
.sec .x {{ font-size:14px; font-weight:600; color:{rp.INK}; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{ background:#fff; border:1px solid {rp.LINE} !important;
        border-radius:16px; box-shadow:0 2px 8px rgba(17,59,37,.06); }}

.tbl-wrap {{ overflow:auto; border:1px solid {rp.LINE}; border-radius:10px; }}
table.tbl {{ width:100%; border-collapse:collapse; font-size:13.5px; color:{rp.INK}; }}
table.tbl th {{ background:{GREEN}; color:#fff; font-weight:600; padding:9px 12px; text-align:left;
                position:sticky; top:0; white-space:nowrap; }}
table.tbl td {{ padding:8px 12px; border-bottom:1px solid {rp.ROW_LINE}; white-space:nowrap; }}
table.tbl tr:nth-child(even) td {{ background:{rp.ZEBRA}; }}
table.tbl .num {{ text-align:right; font-variant-numeric: tabular-nums; }}
table.tbl tr.tot td {{ font-weight:700; background:{rp.TOT_BG} !important; }}
.note {{ font-size:12.5px; color:{rp.MUTED}; margin-top:8px; }}
.note.warn {{ color:{GREEN_D}; font-weight:600; }}

span[data-baseweb="tag"] {{ background-color:{GREEN} !important; color:#fff !important; }}
.stDownloadButton button {{ background:{GREEN}; color:#fff; border:0; border-radius:10px; font-weight:600;
                            padding:.55rem 1.2rem; }}
.stDownloadButton button:hover {{ background:{GREEN_D}; color:#fff; }}
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value, unit, dark=False, alert=False):
    st.markdown(f'<div class="kpi{" d" if dark else ""}{" alert" if alert else ""}"><div class="lbl">{label}</div>'
                f'<div class="val">{value}<span class="unit">{unit}</span></div></div>',
                unsafe_allow_html=True)


def section(title, right=""):
    st.markdown(f'<div class="sec"><div class="n">{html.escape(title)}</div>'
                f'<div class="x">{html.escape(right)}</div></div>', unsafe_allow_html=True)


def html_table(df, fmt=None, max_height=None, total_last=False):
    fmt = fmt or {}
    num_cols = {c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])}
    head = "".join(f'<th class="{"num" if c in num_cols else ""}">{html.escape(str(c))}</th>' for c in df.columns)
    rows = []
    for i, (_, r) in enumerate(df.iterrows()):
        tds = []
        for c in df.columns:
            v = r[c]
            if v is None or (isinstance(v, float) and pd.isna(v)):
                txt = "-"
            elif c in fmt:
                txt = fmt[c].format(v)
            else:
                txt = str(v)
            tds.append(f'<td class="{"num" if c in num_cols else ""}">{html.escape(txt)}</td>')
        cls = ' class="tot"' if (total_last and i == len(df) - 1) else ""
        rows.append(f"<tr{cls}>{''.join(tds)}</tr>")
    style = f' style="max-height:{max_height}px"' if max_height else ""
    return (f'<div class="tbl-wrap"{style}><table class="tbl"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def show_fig(fig):
    st.pyplot(fig)
    plt.close(fig)


@st.cache_data(show_spinner="Reading Excel file ...")
def load(file_bytes, line):
    return dl.parse_workbook(file_bytes, line)


@st.cache_data(show_spinner="Preparing PDF / JPG ...")
def make_exports(kp, gt, bt, thk, thk_info, line, period, prod, trends, year):
    return rp.build_exports(kp, gt, bt, thk, thk_info, line, period, prod, trends, year)


def period_label(months, year):
    ms = sorted(months)
    if len(ms) == 1:
        return f"{dl.MONTH_LABEL[ms[0]]} {year}"
    if ms == list(range(ms[0], ms[-1] + 1)):
        return f"{dl.MONTH_LABEL[ms[0]]} – {dl.MONTH_LABEL[ms[-1]]} {year}"
    return ", ".join(dl.MONTH_LABEL[m] for m in ms) + f" {year}"


# ---------------- Sidebar: inputs ----------------
with st.sidebar:
    st.header("Settings")
    line = st.selectbox("Production line", list(dl.LINE_CONFIG.keys()))
    st.caption("Choose the line that matches the uploaded Excel file.")
    up = st.file_uploader("Upload Excel file (Jan–Dec)", type=["xlsx", "xlsm"])
    group_on = st.checkbox("Group board types", value=True)
    gup = st.file_uploader("Board-type grouping file (optional — overrides the built-in grouping)",
                           type=["xlsx"], key="grp")

if up is None:
    st.markdown(f'<div class="banner"><div><div class="t">Monthly Resin Utilization Dashboard</div>'
                f'<div class="s">{html.escape(line)}</div></div><div class="rw"><div class="r">{rp.COMPANY}</div></div></div>', unsafe_allow_html=True)
    st.info("Upload the production report (Excel) in the sidebar to get started.")
    st.stop()

try:
    df, resin_names, notes = load(up.getvalue(), line)
except Exception as e:  # noqa: BLE001
    st.error(f"Could not read the file: {e}")
    st.stop()

try:
    gmap = dl.read_group_map_xlsx(gup.getvalue()) if gup else dl.read_group_map_csv(GROUP_CSV)
except Exception as e:  # noqa: BLE001
    st.sidebar.error(f"Could not read the grouping file: {e}")
    gmap = {}
df, ungrouped = dl.apply_groups(df, gmap)
notes = list(notes)
if ungrouped:
    notes.append("Board types not yet grouped (own name used as group): " + " | ".join(ungrouped))

# ---------------- Sidebar: period ----------------
with st.sidebar:
    mode = st.radio("Select data by", ["Month", "Date range"], horizontal=True)
    if mode == "Month":
        year = int(df["date"].dt.year.mode().iat[0])
        avail = sorted(int(m) for m in df["month"].unique())
        chosen = st.multiselect("Months", avail, default=avail,
                                format_func=lambda m: f"{dl.MONTH_LABEL[m]} {year}")
        d = dl.filter_rows(df, months=chosen) if chosen else df.iloc[0:0]
        period = period_label(chosen, year) if chosen else "-"
    else:
        lo, hi = df["date"].min().date(), df["date"].max().date()
        rng = st.date_input("Date range", value=(lo, hi), min_value=lo, max_value=hi, format="DD/MM/YYYY")
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            d = dl.filter_rows(df, date_range=rng)
            period = f"{rng[0]:%d %b %Y} – {rng[1]:%d %b %Y}"
        else:
            st.caption("Pick the end date to continue.")
            st.stop()
    if notes:
        with st.expander(f"Data notes ({len(notes)})"):
            for n in notes:
                st.write("• " + n)

if d.empty:
    st.warning("No data in the selected period.")
    st.stop()

# ---------------- Calculations ----------------
kp = dl.kpis(d)
gt, gtotal = dl.glue_table(d, resin_names)
bt = dl.board_table(d, by="group" if group_on else "board")
thk, thk_info = dl.thickness_table(d)
prod = dl.product_table(d, by="group" if group_on else "board")
year_all = int(df["date"].dt.year.mode().iat[0])
# monthly consumption of the top-6 products (all months in the file) for the export page 2
trends = [(p, dl.product_monthly(df, p, by="group" if group_on else "board")) for p in prod["Product"].head(6)]

# ---------------- Header ----------------
_logo = rp.logo_data_uri()
_logo_html = f'<div class="logo"><img src="{_logo}" alt="METRO"></div>' if _logo else ""
st.markdown(
    f'<div class="banner"><div><div class="t">Monthly Resin Utilization Dashboard</div>'
    f'<div class="s">{html.escape(line)}<span class="sep">|</span>{html.escape(period)}<span class="sep">|</span>{len(d):,} records</div></div>'
    f'<div class="rw"><div class="r">{rp.COMPANY}<small>Executive summary</small></div>{_logo_html}</div></div>',
    unsafe_allow_html=True)
st.write("")
_jpg1, _jpg2, _pdf = make_exports(kp, gt, bt, thk, thk_info, line, period, prod, trends, year_all)
_fn = f"Monthly_Resin_Utilization_{line.replace(' ', '')}"
_sp, b1, b2, b3 = st.columns([1.3, 1.1, 1, 1])
with b1:
    st.download_button("⬇ Export PDF (2 pages)", data=_pdf, file_name=f"{_fn}.pdf",
                       mime="application/pdf", use_container_width=True)
with b2:
    st.download_button("⬇ JPG – Page 1", data=_jpg1, file_name=f"{_fn}_Page1.jpg",
                       mime="image/jpeg", use_container_width=True)
with b3:
    st.download_button("⬇ JPG – Page 2", data=_jpg2, file_name=f"{_fn}_Page2.jpg",
                       mime="image/jpeg", use_container_width=True)
st.write("")

# ---------------- KPI cards ----------------
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    kpi_card("Production Output", f"{kp['prod']:,.2f}", "m³")
with c2:
    kpi_card("Reject After Press", f"{kp['reject']:,.2f}", "m³", dark=True)
with c3:
    kpi_card("% Reject After Press", "-" if kp["reject_pct"] is None else f"{kp['reject_pct']:.2f}", "%", dark=True,
             alert=rp.reject_over_target(kp["reject_pct"]))
st.write("")

# ---------------- Resin usage ----------------
with st.container(border=True):
    section("Total Resin Usage Summary (kg)", f"Total: {gtotal:,.0f} kg")
    show_fig(rp.fig_resin(gt))
    st.markdown('<div class="note">Net resin used (TT columns) per resin code. Only resins used in the selected period are shown.</div>',
                unsafe_allow_html=True)
st.write("")

# ---------------- Board type ----------------
with st.container(border=True):
    section("Production by Board Type", f"{len(bt)} {'groups' if group_on else 'board types'}")
    pc, tc = st.columns([1, 1.15], gap="large")
    with pc:
        labels, values = dl.top_n_with_others(bt, 8)
        show_fig(rp.fig_pie(labels, values))
        st.markdown('<div class="note">Pie shows the top 8; the rest are combined as “Others”. The table lists all.</div>',
                    unsafe_allow_html=True)
    with tc:
        st.markdown(html_table(bt, fmt={"Production (m³)": "{:,.2f}", "Resin (kg)": "{:,.0f}",
                                        "Share (%)": "{:.1f}", "Consumption (kg/m³)": "{:.2f}"},
                               max_height=470), unsafe_allow_html=True)
        st.markdown('<div class="note">Consumption = total resin used ÷ production volume of the same board type.</div>',
                    unsafe_allow_html=True)
st.write("")

# ---------------- Thickness ----------------
with st.container(border=True):
    section("Production by Thickness Range", "m³ and share of volume inside the ranges")
    pc, tc = st.columns([1, 1.15], gap="large")
    with pc:
        keep = thk[thk["Production (m³)"] > 0]
        show_fig(rp.fig_pie(list(keep["Thickness Range"]), [float(v) for v in keep["Production (m³)"]]))
    with tc:
        tt = thk.copy()
        tot = pd.DataFrame([{"Thickness Range": "Total (in ranges)",
                             "Production (m³)": tt["Production (m³)"].sum(),
                             "Share (%)": 100.0 if tt["Production (m³)"].sum() else 0.0}])
        st.write("")
        st.markdown(html_table(pd.concat([tt, tot], ignore_index=True),
                               fmt={"Production (m³)": "{:,.1f}", "Share (%)": "{:.1f}"}, total_last=True),
                    unsafe_allow_html=True)
        st.markdown(f'<div class="note">Shares are based on the volume inside the ranges ({thk_info["classified"]:,.1f} m³).</div>',
                    unsafe_allow_html=True)
        if thk_info["outside_m3"] > 0.05:
            vals = ", ".join(f"{v:g}" for v in thk_info["outside_values"])
            st.markdown(f'<div class="note warn">Not in any range (thickness {vals} mm): '
                        f'{thk_info["outside_m3"]:,.1f} m³</div>', unsafe_allow_html=True)
st.write("")

# ---------------- Product table ----------------
with st.container(border=True):
    section("Production by Product (Thickness + Board Type Group)", f"{len(prod)} products")
    st.markdown(html_table(prod, fmt={"Production (m³)": "{:,.2f}", "Consumption (kg/m³)": "{:.2f}"},
                           max_height=560), unsafe_allow_html=True)
    st.markdown('<div class="note">Product = thickness (mm) + board type group, e.g. “2.5 E1/P2 EPA”. '
                'Sorted from highest to lowest production. Consumption = total resin used ÷ production volume of the same product.</div>',
                unsafe_allow_html=True)

    # ---- monthly consumption trend of one product (all months in the file) ----
    st.write("")
    section("Monthly Resin Consumption by Product", "all months in the file")
    sel = st.selectbox("Select a product", list(prod["Product"]), key="prod_trend")
    _by = "group" if group_on else "board"
    trend = dl.product_monthly(df, sel, by=_by)
    show_fig(rp.fig_product_trend(trend, sel, year_all))
    _gaps = [m for m, v in zip(trend["Month"], trend["Consumption (kg/m³)"]) if pd.isna(v)]
    st.markdown('<div class="note">Consumption per month = resin used ÷ production volume of this product in that month. '
                'Shows every month in the file, regardless of the period selected in the sidebar.'
                + (f' Not produced in: {", ".join(_gaps)}.' if _gaps else "") + '</div>', unsafe_allow_html=True)

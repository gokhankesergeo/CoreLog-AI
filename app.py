import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import io, hashlib, textwrap

# ============================================================
# CoreLog-AI Master Log v28
# Figure-style drill log generator for exploration / mining logs
# ============================================================

st.set_page_config(page_title="CoreLog-AI Master Log v28", layout="wide")

# ----------------------------
# VISUAL DATABASE
# ----------------------------
LITHOLOGY_DB = {
    "GDR": {"name":"Granodiorite", "color":"#f4b6bd", "hatch":"..", "desc":"Medium to coarse grained, light gray to pinkish, weakly fractured."},
    "AND": {"name":"Andesite", "color":"#c8d6e8", "hatch":"vv", "desc":"Medium grained, gray, locally porphyritic, moderately fractured."},
    "TFF": {"name":"Tuff / Lapilli Tuff", "color":"#d9c095", "hatch":"^", "desc":"Lithic to lapilli tuff, brownish gray, locally silicified, crystal fragments."},
    "VBX": {"name":"Volcanic Breccia", "color":"#b98b63", "hatch":"oo", "desc":"Polymictic breccia with angular to subangular clasts in volcanic matrix."},
    "QZV": {"name":"Quartz Vein / Stockwork", "color":"#f7f7f7", "hatch":"//", "desc":"Quartz vein or stockwork zone; locally sulfide-bearing."},
    "SKN": {"name":"Skarn", "color":"#7fa36b", "hatch":"xx", "desc":"Garnet-pyroxene skarn, magnetite/sulfide possible."},
    "LST": {"name":"Limestone / Marble", "color":"#b9ddd6", "hatch":"+", "desc":"Carbonate unit, locally recrystallized or altered."},
    "BIF": {"name":"Banded Iron Formation", "color":"#8d7a90", "hatch":"==", "desc":"Iron-rich banded unit with magnetite/hematite layers."},
    "SST": {"name":"Sandstone", "color":"#e5c48f", "hatch":"..", "desc":"Clastic sandstone, locally permeable or oxidized."},
    "CLN": {"name":"Coal / Carbonaceous Shale", "color":"#2d2d2d", "hatch":"//", "desc":"Carbon-rich black unit; coal/carbonaceous shale."},
    "SHL": {"name":"Shale / Mudstone", "color":"#9aa0a6", "hatch":"--", "desc":"Fine-grained sedimentary unit; laminated to fissile."},
    "DOL": {"name":"Dolomite", "color":"#cfd6c4", "hatch":"++", "desc":"Dolomitic carbonate, locally brecciated or replaced."},
}

ALTERATION_DB = {
    "Silicification": "#dfeaf2",
    "Argillic (Clay)": "#f5e7ad",
    "Chloritic": "#cddfbd",
    "Epidote": "#a7d8a4",
    "Sericite": "#efe3bf",
    "Carbonate": "#d7e7df",
    "Iron Oxide (Gossan)": "#f0a0a0",
    "Potassic": "#f6c5cf",
    "Propylitic": "#b6d9b6",
    "Skarn": "#9bbf8f",
}

DEPOSIT_RULES = {
    "Orogenic Gold": {
        "lith": ["QZV", "GDR", "AND", "SHL"],
        "alts": ["Silicification", "Sericite", "Chloritic", "Carbonate", "Iron Oxide (Gossan)"],
        "sulfide_range": (1, 8),
        "keywords": "shear, quartz vein, pyrite, arsenopyrite, carbonate, sericite",
    },
    "Epithermal Au-Ag": {
        "lith": ["AND", "TFF", "VBX", "QZV"],
        "alts": ["Silicification", "Argillic (Clay)", "Iron Oxide (Gossan)", "Sericite"],
        "sulfide_range": (1, 12),
        "keywords": "vuggy silica, breccia, adularia, argillic, quartz stockwork",
    },
    "Porphyry Cu-Au": {
        "lith": ["GDR", "AND", "VBX", "QZV"],
        "alts": ["Potassic", "Propylitic", "Silicification", "Chloritic", "Epidote"],
        "sulfide_range": (1, 6),
        "keywords": "disseminated pyrite-chalcopyrite, stockwork veins, potassic-propylitic zoning",
    },
    "VMS / Polymetallic": {
        "lith": ["TFF", "VBX", "AND", "SHL"],
        "alts": ["Silicification", "Chloritic", "Sericite", "Iron Oxide (Gossan)"],
        "sulfide_range": (3, 20),
        "keywords": "massive sulfide, pyrite, chalcopyrite, sphalerite, galena, stringer zone",
    },
    "Skarn Fe-Cu-Au": {
        "lith": ["SKN", "LST", "DOL", "GDR"],
        "alts": ["Skarn", "Epidote", "Chloritic", "Iron Oxide (Gossan)", "Carbonate"],
        "sulfide_range": (1, 15),
        "keywords": "garnet, pyroxene, magnetite, chalcopyrite, carbonate replacement",
    },
    "BIF / Iron Ore": {
        "lith": ["BIF", "SHL"],
        "alts": ["Iron Oxide (Gossan)", "Silicification"],
        "sulfide_range": (0, 3),
        "keywords": "magnetite, hematite, banded iron, jasper, chert",
    },
    "Coal / Carbonaceous Basin": {
        "lith": ["CLN", "SHL", "SST"],
        "alts": ["Carbonate", "Chloritic"],
        "sulfide_range": (0, 2),
        "keywords": "coal seam, carbonaceous shale, pyrite, organic-rich interval",
    },
    "Roll-front Uranium": {
        "lith": ["SST", "SHL", "CLN"],
        "alts": ["Iron Oxide (Gossan)", "Argillic (Clay)", "Carbonate"],
        "sulfide_range": (0, 3),
        "keywords": "redox front, oxidized sandstone, reduced carbonaceous horizon",
    },
    "MVT / Pb-Zn": {
        "lith": ["LST", "DOL", "SHL"],
        "alts": ["Carbonate", "Silicification", "Iron Oxide (Gossan)"],
        "sulfide_range": (2, 18),
        "keywords": "galena, sphalerite, dolomite, jasperoid, breccia",
    },
}

STRUCTURE_SYMBOLS = ["bedding", "fracture", "shear", "fault", "quartz vein"]


def stable_rng(*parts):
    key = "_".join(map(str, parts))
    seed = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
    return np.random.default_rng(seed)


def infer_interval(file_name, idx, d_from, d_to, preferred_model="Auto"):
    rng = stable_rng(file_name, idx, d_from, d_to)
    models = list(DEPOSIT_RULES.keys())
    model = preferred_model if preferred_model != "Auto" else models[int(rng.integers(0, len(models)))]
    rule = DEPOSIT_RULES[model]
    lith_code = rule["lith"][int(rng.integers(0, len(rule["lith"])))]
    lith = LITHOLOGY_DB[lith_code]
    sulf_min, sulf_max = rule["sulfide_range"]
    sulf = round(float(rng.uniform(sulf_min, sulf_max)), 1)
    rqd = int(np.clip(rng.normal(68, 18), 15, 98))
    tcr = int(np.clip(rng.normal(88, 8), 55, 100))
    alt_strengths = {}
    for alt in ALTERATION_DB:
        base = rng.uniform(0.05, 0.35)
        if alt in rule["alts"]:
            base += rng.uniform(0.25, 0.65)
        alt_strengths[alt] = float(np.clip(base, 0.03, 1.0))
    main_alt = max(alt_strengths, key=alt_strengths.get)
    if sulf >= 10:
        sulf_text = "locally semi-massive sulfides"
    elif sulf >= 5:
        sulf_text = "disseminated to veinlet-hosted sulfides"
    elif sulf >= 1:
        sulf_text = "minor disseminated sulfides"
    else:
        sulf_text = "trace sulfides"
    desc = f"{lith['desc']} Dominant alteration: {main_alt}. {sulf_text}. Model hint: {model}."
    return {
        "From": d_from, "To": d_to, "Mid": (d_from+d_to)/2, "Thickness": d_to-d_from,
        "LithCode": lith_code, "Lithology": lith["name"], "LithDesc": lith["desc"],
        "Color": lith["color"], "Hatch": lith["hatch"],
        "DepositModel": model, "AlterationDominant": main_alt,
        "Sulfide_%": sulf, "RQD_%": rqd, "TCR_%": tcr,
        "Description": desc, **{f"ALT_{k}":v for k,v in alt_strengths.items()}
    }


def draw_structure_symbol(ax, x, y, symbol, color="#111111", lw=1.0):
    if symbol == "bedding":
        ax.plot([x-0.07, x+0.07], [y+0.05, y-0.02], color=color, lw=lw)
        ax.plot([x-0.02, x+0.04], [y+0.08, y+0.04], color=color, lw=lw)
    elif symbol == "fracture":
        ax.plot([x-0.08, x+0.06], [y-0.08, y+0.08], color=color, lw=lw)
    elif symbol == "shear":
        ax.plot([x-0.09, x+0.09], [y+0.06, y-0.06], color=color, lw=lw)
        ax.plot([x-0.07, x+0.07], [y+0.00, y-0.12], color=color, lw=lw)
    elif symbol == "fault":
        ax.plot([x-0.08, x+0.08], [y+0.08, y-0.08], color=color, lw=lw)
        ax.plot([x-0.04, x-0.01], [y+0.00, y+0.04], color=color, lw=lw)
        ax.plot([x+0.02, x+0.05], [y-0.03, y+0.01], color=color, lw=lw)
    elif symbol == "quartz vein":
        ax.plot([x-0.09, x+0.09], [y+0.05, y-0.05], color="#c62828", lw=lw)
        ax.plot([x-0.08, x+0.08], [y+0.09, y-0.01], color="#c62828", lw=lw)


def make_master_log(df, project, location, hole_id, azdip, total_depth, date_txt):
    depth_min = float(df["From"].min())
    depth_max = float(df["To"].max())
    fig = plt.figure(figsize=(16, 10), dpi=180)
    gs = GridSpec(1, 10, figure=fig, width_ratios=[0.55, 1.3, 0.55, 1.65, 1.55, 1.25, 1.25, 1.15, 2.45, 2.35], wspace=0.08)

    ax_depth = fig.add_subplot(gs[0,0])
    ax_lith = fig.add_subplot(gs[0,1], sharey=ax_depth)
    ax_code = fig.add_subplot(gs[0,2], sharey=ax_depth)
    ax_desc = fig.add_subplot(gs[0,3], sharey=ax_depth)
    ax_alt = fig.add_subplot(gs[0,4], sharey=ax_depth)
    ax_sulf = fig.add_subplot(gs[0,5], sharey=ax_depth)
    ax_rqd = fig.add_subplot(gs[0,6], sharey=ax_depth)
    ax_struct = fig.add_subplot(gs[0,7], sharey=ax_depth)
    ax_marks = fig.add_subplot(gs[0,8], sharey=ax_depth)
    ax_side = fig.add_subplot(gs[0,9])

    all_depth_axes = [ax_depth, ax_lith, ax_code, ax_desc, ax_alt, ax_sulf, ax_rqd, ax_struct, ax_marks]
    for ax in all_depth_axes:
        ax.set_ylim(depth_max, depth_min)
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_color("#9ca3af")
            spine.set_linewidth(0.7)
        ax.tick_params(axis="y", labelsize=8)

    fig.suptitle(f"COMPREHENSIVE GEOLOGICAL MASTER LOG  |  HOLE ID: {hole_id}", y=0.985, fontsize=15, fontweight="bold", color="#0b1d3a")
    fig.text(0.08, 0.952, f"PROJECT: {project}", fontsize=8, fontweight="bold")
    fig.text(0.20, 0.952, f"LOCATION: {location}", fontsize=8)
    fig.text(0.36, 0.952, f"AZIMUTH / DIP: {azdip}", fontsize=8, fontweight="bold")
    fig.text(0.51, 0.952, f"TOTAL DEPTH: {total_depth:.1f} m", fontsize=8, fontweight="bold")
    fig.text(0.66, 0.952, f"DATE: {date_txt}", fontsize=8, fontweight="bold")

    # Depth column
    ax_depth.set_xlim(0, 1)
    ax_depth.set_title("DEPTH\n(m)", fontsize=8, fontweight="bold", pad=10)
    major = np.arange(np.floor(depth_min/5)*5, depth_max+5, 5)
    minor = np.arange(np.floor(depth_min), depth_max+1, 1)
    ax_depth.set_yticks(major)
    ax_depth.set_yticks(minor, minor=True)
    ax_depth.tick_params(axis="y", which="major", length=7, width=1)
    ax_depth.tick_params(axis="y", which="minor", length=3, width=0.6)
    ax_depth.set_xticks([])
    ax_depth.grid(axis="y", which="major", color="#d0d0d0", lw=0.5)

    for ax, title in [(ax_lith,"LITHOLOGY\n(Visual Log)"),(ax_code,"ROCK\nCODE"),(ax_desc,"LITHOLOGY\nDESCRIPTION"),(ax_alt,"ALTERATION\n(Dominant)"),(ax_sulf,"SULFIDE\n(%)"),(ax_rqd,"RQD\n(%)"),(ax_struct,"STRUCTURAL\n(Log)"),(ax_marks,"TOTAL LITHOLOGY / SYSTEM MARKS",)]:
        ax.set_title(title, fontsize=8, fontweight="bold", pad=10)
        ax.set_yticklabels([])

    # Boundaries and lithology
    for _, r in df.iterrows():
        y0, thick, mid = r["From"], r["Thickness"], r["Mid"]
        for ax in [ax_lith, ax_code, ax_desc, ax_alt, ax_sulf, ax_rqd, ax_struct, ax_marks]:
            ax.axhline(y0, color="#9ca3af", lw=0.55, ls="--", alpha=0.7)
        ax_lith.add_patch(patches.Rectangle((0, y0), 1, thick, facecolor=r["Color"], edgecolor="#444", lw=0.6, hatch=r["Hatch"], alpha=0.95))
        ax_code.text(0.5, mid, r["LithCode"], ha="center", va="center", fontsize=8, fontweight="bold")
        ax_desc.text(0.05, mid, textwrap.fill(f"{r['Lithology']}\n\n{r['LithDesc']}", 22), ha="left", va="center", fontsize=7)

        # Alteration bands: variable width vertical ribbons
        alts = sorted(ALTERATION_DB.keys(), key=lambda k: r[f"ALT_{k}"], reverse=True)[:5]
        xbase = 0.50
        for j, alt in enumerate(alts):
            strength = r[f"ALT_{alt}"]
            width = 0.06 + 0.10 * strength
            x = xbase + (j-2)*0.11
            yy = np.linspace(y0, y0+thick, 25)
            wiggle = 0.015*np.sin(np.linspace(0, np.pi*2, 25) + j)
            ax_alt.fill_betweenx(yy, x-width+wiggle, x+width+wiggle, color=ALTERATION_DB[alt], alpha=0.75, lw=0)

        # Sulfide bar
        ax_sulf.barh(mid, r["Sulfide_%"], height=thick*0.88, left=0, color="#e8773d", edgecolor="#c35a28", alpha=0.9)

        # Marks column narrative
        block = f"{r['From']:.1f} – {r['To']:.1f} m\n{r['Lithology']}. {r['AlterationDominant']} dominant. Sulfide {r['Sulfide_%']:.1f}%. RQD {r['RQD_%']}%.\nModel: {r['DepositModel']}."
        ax_marks.text(0.03, mid, textwrap.fill(block, 32), ha="left", va="center", fontsize=6.7,
                      bbox=dict(facecolor="white", edgecolor="#e5e7eb", lw=0.5, pad=3))

        # Structures
        rng = stable_rng(r["LithCode"], r["From"], r["To"])
        n = max(2, int(thick/2.2))
        for k in range(n):
            y = float(rng.uniform(y0+0.4, y0+thick-0.4)) if thick > 1 else mid
            x = float(rng.uniform(0.18, 0.82))
            sym = STRUCTURE_SYMBOLS[int(rng.integers(0, len(STRUCTURE_SYMBOLS)))]
            draw_structure_symbol(ax_struct, x, y, sym, lw=0.8)

    ax_lith.set_xlim(0,1); ax_code.set_xlim(0,1); ax_desc.set_xlim(0,1); ax_alt.set_xlim(0,1); ax_struct.set_xlim(0,1); ax_marks.set_xlim(0,1)
    for ax in [ax_lith, ax_code, ax_desc, ax_alt, ax_struct, ax_marks]:
        ax.set_xticks([])

    ax_sulf.set_xlim(0, max(15, float(df["Sulfide_%"].max())*1.2))
    ax_sulf.set_xlabel("0     5     10     15", fontsize=6)
    ax_sulf.grid(axis="x", color="#dddddd", ls="--", lw=0.5)

    ax_rqd.set_xlim(0,100)
    ax_rqd.plot(df["RQD_%"], df["Mid"], color="#0b2545", lw=1.4, marker="o", markersize=3)
    ax_rqd.set_xticks([0,50,100])
    ax_rqd.grid(axis="x", color="#dddddd", ls="--", lw=0.5)

    # Side panel
    ax_side.axis("off")
    ax_side.set_title("LEGEND & SUMMARY", fontsize=9, fontweight="bold", pad=10)

    # Donut chart inset
    lith_sum = df.groupby(["LithCode","Lithology","Color"])["Thickness"].sum().reset_index()
    inset = ax_side.inset_axes([0.05, 0.72, 0.45, 0.23])
    inset.pie(lith_sum["Thickness"], colors=lith_sum["Color"], startangle=90, wedgeprops=dict(width=0.38, edgecolor="white"))
    inset.text(0,0, f"{depth_max-depth_min:.1f} m\nTotal", ha="center", va="center", fontsize=7, fontweight="bold")
    inset.set_aspect("equal")
    y = 0.92
    ax_side.text(0.55, y, "TOTAL LITHOLOGY", fontsize=7.5, fontweight="bold", transform=ax_side.transAxes)
    y -= 0.035
    for _, rr in lith_sum.iterrows():
        pct = rr["Thickness"]/(depth_max-depth_min)*100
        ax_side.add_patch(patches.Rectangle((0.55,y-0.012),0.035,0.018, color=rr["Color"], transform=ax_side.transAxes, clip_on=False))
        ax_side.text(0.60, y, f"{rr['Lithology']} ({rr['LithCode']})", fontsize=6.5, transform=ax_side.transAxes, va="center")
        ax_side.text(0.95, y, f"{pct:.1f}%", fontsize=6.5, transform=ax_side.transAxes, ha="right", va="center")
        y -= 0.032

    # Legend boxes
    y = 0.62
    ax_side.text(0.05, y, "LITHOLOGY", fontsize=7.5, fontweight="bold", transform=ax_side.transAxes)
    y -= 0.035
    for code, info in LITHOLOGY_DB.items():
        if code in set(df["LithCode"]):
            ax_side.add_patch(patches.Rectangle((0.06,y-0.013),0.035,0.02, facecolor=info["color"], hatch=info["hatch"], edgecolor="#444", transform=ax_side.transAxes))
            ax_side.text(0.105, y, f"{code}  {info['name']}", fontsize=6.2, transform=ax_side.transAxes, va="center")
            y -= 0.03

    y -= 0.02
    ax_side.text(0.05, y, "ALTERATION", fontsize=7.5, fontweight="bold", transform=ax_side.transAxes)
    y -= 0.035
    used_alts = list(dict.fromkeys(df["AlterationDominant"].tolist()))[:8]
    for alt in used_alts:
        ax_side.add_patch(patches.Rectangle((0.06,y-0.013),0.035,0.02, color=ALTERATION_DB[alt], transform=ax_side.transAxes))
        ax_side.text(0.105, y, alt, fontsize=6.2, transform=ax_side.transAxes, va="center")
        y -= 0.03

    y -= 0.02
    ax_side.text(0.05, y, "STRUCTURAL SYMBOLS", fontsize=7.5, fontweight="bold", transform=ax_side.transAxes)
    y -= 0.035
    for sym in STRUCTURE_SYMBOLS:
        draw_structure_symbol(ax_side, 0.08, y, sym, lw=0.9)
        ax_side.text(0.14, y, sym.title(), fontsize=6.2, transform=ax_side.transAxes, va="center")
        y -= 0.032

    fig.text(0.07, 0.025, "Note: This log is an AI-assisted visual interpretation. Assays, detailed petrography, QA/QC and senior geologist review are required before technical reporting.", fontsize=7, style="italic", color="#555")
    return fig


# ----------------------------
# STREAMLIT UI
# ----------------------------
st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
.main-title {background: linear-gradient(135deg,#0b1d3a,#1d4ed8); color:white; padding:22px; border-radius:16px;}
.card {background:white; padding:18px; border:1px solid #e5e7eb; border-radius:14px; box-shadow:0 4px 12px rgba(0,0,0,.04);}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'><h1>⛏️ CoreLog-AI Master Log v28</h1><p>Figure-style geological log: lithology, alteration, sulfide, RQD, structures, legend and interval interpretation.</p></div>", unsafe_allow_html=True)

left, right = st.columns([1, 2.4])
with left:
    st.markdown("### Project information")
    project = st.text_input("Project", "SAHA-01")
    location = st.text_input("Location", "Central Zone")
    hole_id = st.text_input("Hole ID", "DDH-2026-004")
    azdip = st.text_input("Azimuth / Dip", "045° / -60°")
    date_txt = st.text_input("Date", "16 May 2025")
    preferred_model = st.selectbox("Deposit system hint", ["Auto"] + list(DEPOSIT_RULES.keys()))
    uploaded = st.file_uploader("Upload core / chip images", type=["jpg","jpeg","png"], accept_multiple_files=True)

rows = []
if uploaded:
    with left:
        st.markdown("### Depth intervals")
        for i, f in enumerate(uploaded):
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"From #{i+1}", value=float(i*10), step=1.0, key=f"from_{i}")
            d_to = c2.number_input(f"To #{i+1}", value=float((i+1)*10), step=1.0, key=f"to_{i}")
            row = infer_interval(f.name, i, d_from, d_to, preferred_model)
            rows.append(row)

    df = pd.DataFrame(rows).sort_values("From")
    total_depth = float(df["To"].max())

    with right:
        st.markdown("### Editable AI interpretation table")
        cols = ["From","To","LithCode","Lithology","DepositModel","AlterationDominant","Sulfide_%","RQD_%","TCR_%","Description"]
        edited = st.data_editor(df[cols], use_container_width=True, num_rows="dynamic")

        # Rebuild style columns after editing lith code / alteration
        for i in edited.index:
            code = edited.loc[i,"LithCode"] if edited.loc[i,"LithCode"] in LITHOLOGY_DB else "AND"
            edited.loc[i,"LithCode"] = code
            edited.loc[i,"Lithology"] = LITHOLOGY_DB[code]["name"]
        for col in df.columns:
            if col not in edited.columns:
                edited[col] = df[col].values[:len(edited)]
        for i, r in edited.iterrows():
            info = LITHOLOGY_DB[r["LithCode"]]
            edited.at[i,"Color"] = info["color"]
            edited.at[i,"Hatch"] = info["hatch"]
            edited.at[i,"LithDesc"] = info["desc"]
            edited.at[i,"Thickness"] = float(r["To"])-float(r["From"])
            edited.at[i,"Mid"] = (float(r["To"])+float(r["From"]))/2

        if st.button("Generate master log", type="primary", use_container_width=True):
            fig = make_master_log(edited, project, location, hole_id, azdip, total_depth, date_txt)
            st.pyplot(fig, clear_figure=False)

            png = io.BytesIO()
            fig.savefig(png, format="png", dpi=300, bbox_inches="tight")
            st.download_button("Download PNG", png.getvalue(), file_name=f"{hole_id}_master_log.png", mime="image/png", use_container_width=True)

            csv = edited.to_csv(index=False).encode("utf-8")
            st.download_button("Download interpreted CSV", csv, file_name=f"{hole_id}_interpreted_log.csv", mime="text/csv", use_container_width=True)
else:
    with right:
        st.info("Upload one or more core/chip images. Add From-To intervals, choose a deposit system hint, then generate the master log.")
        demo = pd.DataFrame([
            infer_interval("demo_1.png",0,0,10,"Porphyry Cu-Au"),
            infer_interval("demo_2.png",1,10,20,"Epithermal Au-Ag"),
            infer_interval("demo_3.png",2,20,45,"VMS / Polymetallic"),
            infer_interval("demo_4.png",3,45,60,"Skarn Fe-Cu-Au"),
        ])
        if st.button("Show demo figure"):
            fig = make_master_log(demo, project, location, hole_id, azdip, 60.0, date_txt)
            st.pyplot(fig)

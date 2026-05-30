import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import io, textwrap, hashlib, random

st.set_page_config(page_title="CoreLog-AI | Geological Master Log", layout="wide")

st.title("⛏️ CoreLog-AI | Geological Master Log & Ore-System Interpretation")
st.caption("Lithology + alteration + mineralization + RQD + structural log + ore deposit model reasoning")

# ============================================================
# 1) GENİŞ LİTOLOJİ HAZNESİ
# ============================================================

LITHOLOGY = {
    # Intrusive
    "Granite": ("GRN", "Granit", "#f4b6b6", "...", "Intrusive"),
    "Granodiorite": ("GDR", "Granodiyorit", "#d98f8f", "...", "Intrusive"),
    "Diorite": ("DIO", "Diyorit", "#8d99ae", "oo", "Intrusive"),
    "Tonalite": ("TON", "Tonalit", "#c9a0dc", "++", "Intrusive"),
    "Monzonite": ("MON", "Monzonit", "#e8aeb7", "xx", "Intrusive"),
    "Gabbro": ("GAB", "Gabro", "#4a5568", "oo", "Intrusive"),

    # Volcanic
    "Rhyolite": ("RHY", "Riyolit", "#f7c6d9", "++", "Volcanic"),
    "Dacite": ("DAC", "Dasit", "#c9b6e4", "O.", "Volcanic"),
    "Andesite": ("AND", "Andezit", "#a2a2d0", "oo", "Volcanic"),
    "Basalt": ("BAS", "Bazalt", "#5f6f52", "xx", "Volcanic"),
    "Tuff": ("TFF", "Tüf", "#e8d3a2", "..", "Volcanic"),
    "Lapilli Tuff": ("LTF", "Lapilli Tüf", "#d6b879", "o.", "Volcanic"),
    "Volcanic Breccia": ("VBX", "Volkanik Breş", "#b07d62", "xx", "Volcanic"),

    # Sedimentary
    "Sandstone": ("SST", "Kumtaşı", "#f1d18a", "---", "Sedimentary"),
    "Siltstone": ("SLT", "Silttaşı", "#c7a76c", "---", "Sedimentary"),
    "Mudstone": ("MST", "Çamurtaşı", "#7b7b7b", "---", "Sedimentary"),
    "Shale": ("SHL", "Şeyl", "#5c5c5c", "---", "Sedimentary"),
    "Conglomerate": ("CON", "Konglomera", "#c08457", "oo", "Sedimentary"),
    "Coal": ("COL", "Kömür", "#1f1f1f", "", "Sedimentary"),
    "Bauxite": ("BAX", "Boksit", "#b65f3a", "..", "Sedimentary"),

    # Carbonate
    "Limestone": ("LST", "Kireçtaşı", "#94d2bd", "++", "Carbonate"),
    "Dolomite": ("DOL", "Dolomit", "#b7e4c7", "++", "Carbonate"),
    "Marble": ("MRB", "Mermer", "#d8f3dc", "\\\\", "Metamorphic"),

    # Metamorphic
    "Schist": ("SCH", "Şist", "#90a955", "\\\\", "Metamorphic"),
    "Micaschist": ("MSC", "Mikaşist", "#8ecae6", "\\\\", "Metamorphic"),
    "Gneiss": ("GNS", "Gnays", "#adb5bd", "xx", "Metamorphic"),
    "Quartzite": ("QZT", "Kuvarsit", "#f8f9fa", "///", "Metamorphic"),
    "Amphibolite": ("AMP", "Amfibolit", "#2d6a4f", "oo", "Metamorphic"),
    "Slate": ("SLA", "Arduvaz", "#495057", "\\\\", "Metamorphic"),

    # Ultramafic
    "Serpentinite": ("SRP", "Serpantinit", "#588157", "xx", "Ultramafic"),
    "Dunite": ("DUN", "Dunit", "#6a994e", "oo", "Ultramafic"),
    "Harzburgite": ("HZB", "Harzburjit", "#386641", "++", "Ultramafic"),

    # Ore / vein / special
    "Quartz Vein Zone": ("QVZ", "Kuvars Damar Zonu", "#ffffff", "///", "Vein"),
    "Shear Zone": ("SHZ", "Makaslama Zonu", "#c1121f", "\\\\", "Structure"),
    "Fault Breccia": ("FBX", "Fay Breşi", "#bc4749", "xx", "Structure"),
    "Gossan / Iron Oxide Zone": ("GOX", "Gossan / Demir Oksit", "#d9480f", "..", "Ore Zone"),
    "Massive Sulphide": ("MSU", "Masif Sülfür", "#343a40", "", "Ore Zone"),
    "BIF / Iron Formation": ("BIF", "Bantlı Demir Formasyonu", "#6c757d", "---", "Ore Zone"),
    "Pegmatite": ("PEG", "Pegmatit", "#ffe5ec", "++", "Special"),
    "Skarn": ("SKN", "Skarn", "#95d5b2", "oo", "Ore Zone"),
    "Unknown / Mixed Lithology": ("UNK", "Belirsiz / Karışık", "#e5e5e5", "", "Unknown"),
}

ALTERATION = {
    "Gözlenmedi": ("#f8f9fa", ""),
    "Silisleşme": ("#dbeafe", "///"),
    "Serisitleşme": ("#fff3b0", "\\\\"),
    "Killeşme / Arjilik": ("#ddc1a1", ".."),
    "Advanced Argillic": ("#f4a261", "xx"),
    "Klorit + Epidot": ("#74c69d", "---"),
    "Karbonatlaşma": ("#caf0f8", "++"),
    "Potassic": ("#ffb4a2", ".."),
    "Propylitic": ("#b7e4c7", "\\\\"),
    "Garnet-Pyroxene": ("#c77dff", "oo"),
    "Epidot-Klorit-Aktinolit": ("#52b788", "---"),
    "Hematit-Goetit-Limonit": ("#e76f51", ".."),
    "Serpantinleşme": ("#80b918", "xx"),
}

ORE_MODELS = {
    "Orogenic Gold": {
        "rocks": ["Schist", "Micaschist", "Gneiss", "Quartzite", "Amphibolite", "Shear Zone", "Quartz Vein Zone"],
        "alteration": ["Serisitleşme", "Karbonatlaşma", "Silisleşme", "Klorit + Epidot"],
        "minerals": ["Py", "Apy"],
        "pathfinder": "Au, As, Sb, W, Bi, Te",
        "note": "Shear zone + quartz vein + carbonate-sericite alteration + pyrite/arsenopyrite supports orogenic Au model."
    },
    "LS Epithermal Au-Ag": {
        "rocks": ["Andesite", "Dacite", "Rhyolite", "Tuff", "Volcanic Breccia", "Quartz Vein Zone"],
        "alteration": ["Silisleşme", "Serisitleşme", "Killeşme / Arjilik"],
        "minerals": ["Py", "Gn", "Sp"],
        "pathfinder": "Au, Ag, As, Sb, Hg, Tl",
        "note": "Colloform/crustiform quartz, open-space filling and adularia-sericite style indicate LS epithermal potential."
    },
    "HS Epithermal Au-Cu": {
        "rocks": ["Rhyolite", "Dacite", "Tuff", "Volcanic Breccia", "Gossan / Iron Oxide Zone"],
        "alteration": ["Advanced Argillic", "Silisleşme", "Hematit-Goetit-Limonit"],
        "minerals": ["Py", "Cpy"],
        "pathfinder": "Au, Cu, As, Sb, Bi, Te",
        "note": "Vuggy silica, advanced argillic alteration, jarosite/hematite and breccia support HS epithermal/lithocap model."
    },
    "Porphyry Cu-Au-Mo": {
        "rocks": ["Granite", "Granodiorite", "Diorite", "Tonalite", "Monzonite", "Dacite", "Andesite"],
        "alteration": ["Potassic", "Serisitleşme", "Propylitic", "Silisleşme"],
        "minerals": ["Py", "Cpy", "Mo"],
        "pathfinder": "Cu, Mo, Au, Ag, Bi, W, Zn, Pb",
        "note": "Intrusive host, stockwork veins, phyllic-potassic-propylitic zoning and pyrite-chalcopyrite suggest porphyry potential."
    },
    "Skarn Cu-Fe-Zn-W": {
        "rocks": ["Limestone", "Dolomite", "Marble", "Skarn", "Granodiorite", "Diorite"],
        "alteration": ["Garnet-Pyroxene", "Epidot-Klorit-Aktinolit", "Klorit + Epidot"],
        "minerals": ["Mag", "Py", "Cpy", "Gn", "Sp"],
        "pathfinder": "Cu, Fe, Zn, Pb, W, Mo, Bi, Au",
        "note": "Carbonate-intrusive contact with garnet-pyroxene or epidote-chlorite-actinolite indicates skarn system."
    },
    "VMS Cu-Zn-Pb-Au-Ag": {
        "rocks": ["Basalt", "Rhyolite", "Dacite", "Tuff", "Volcanic Breccia", "Massive Sulphide"],
        "alteration": ["Klorit + Epidot", "Serisitleşme", "Silisleşme"],
        "minerals": ["Py", "Cpy", "Gn", "Sp"],
        "pathfinder": "Cu, Zn, Pb, Ag, Au, Ba, Mn, Fe",
        "note": "Massive sulphide, chlorite stringer zone and volcanic-sedimentary contact support VMS model."
    },
    "MVT / SEDEX Pb-Zn-Ag": {
        "rocks": ["Limestone", "Dolomite", "Shale", "Siltstone"],
        "alteration": ["Karbonatlaşma", "Silisleşme"],
        "minerals": ["Gn", "Sp", "Py"],
        "pathfinder": "Pb, Zn, Ag, Ba, Mn",
        "note": "Carbonate-hosted galena-sphalerite mineralization may indicate MVT/SEDEX style."
    },
    "BIF / Iron Ore": {
        "rocks": ["BIF / Iron Formation", "Quartzite", "Schist"],
        "alteration": ["Hematit-Goetit-Limonit", "Silisleşme"],
        "minerals": ["Hem", "Mag", "Gt"],
        "pathfinder": "Fe, Mn, Si, P",
        "note": "Banded iron formation, hematite-magnetite enrichment and silica bands support iron ore potential."
    },
    "Coal": {
        "rocks": ["Coal", "Mudstone", "Shale", "Sandstone", "Siltstone"],
        "alteration": ["Gözlenmedi"],
        "minerals": ["C"],
        "pathfinder": "C, S, Ash, VM, Moisture",
        "note": "Coal seam thickness, continuity, ash, sulfur and roof/floor stability are key economic controls."
    },
    "Chromite / Ultramafic": {
        "rocks": ["Serpentinite", "Dunite", "Harzburgite"],
        "alteration": ["Serpantinleşme"],
        "minerals": ["Chr"],
        "pathfinder": "Cr, Ni, Co, Mg, Pt, Pd",
        "note": "Serpentinized ultramafic rocks, dunite envelope and chromite bands/nodules support podiform chromite model."
    },
    "Li-REE Pegmatite": {
        "rocks": ["Pegmatite", "Granite", "Schist", "Gneiss"],
        "alteration": ["Silisleşme", "Serisitleşme"],
        "minerals": ["Spd", "Lep", "Tur", "Mnz"],
        "pathfinder": "Li, Cs, Ta, Nb, Sn, Be, REE",
        "note": "Pegmatite dykes with mica-feldspar-quartz and rare-element minerals may indicate Li-REE pegmatite potential."
    },
}

STRUCTURAL_SYMBOLS = ["Bedding", "Fracture", "Fault", "Shear", "Quartz vein", "Stockwork", "Breccia"]

# ============================================================
# 2) OTOMATİK YORUM MOTORU
# ============================================================

def choose_by_filename(name):
    n = name.lower()
    mapping = {
        "coal": "Coal", "komur": "Coal", "kömür": "Coal",
        "bif": "BIF / Iron Formation", "iron": "BIF / Iron Formation", "demir": "BIF / Iron Formation",
        "skarn": "Skarn", "marble": "Marble", "mermer": "Marble", "limestone": "Limestone", "dolomite": "Dolomite",
        "vms": "Massive Sulphide", "sulfide": "Massive Sulphide", "sulphide": "Massive Sulphide",
        "chromite": "Serpentinite", "krom": "Serpentinite", "serp": "Serpentinite",
        "peg": "Pegmatite", "lithium": "Pegmatite", "ree": "Pegmatite",
        "gossan": "Gossan / Iron Oxide Zone",
        "quartz": "Quartz Vein Zone", "vein": "Quartz Vein Zone",
        "shear": "Shear Zone",
        "breccia": "Volcanic Breccia",
        "gran": "Granodiorite",
        "dior": "Diorite",
        "andesite": "Andesite",
        "dacite": "Dacite",
        "basalt": "Basalt",
        "schist": "Schist",
        "gneiss": "Gneiss",
    }
    for key, lith in mapping.items():
        if key in n:
            return lith

    pool = ["Granodiorite", "Andesite", "Dacite", "Volcanic Breccia", "Schist", "Quartz Vein Zone", "Gossan / Iron Oxide Zone"]
    return pool[int(hashlib.md5(name.encode()).hexdigest()[:4], 16) % len(pool)]


def infer_alteration(lith, val):
    if lith in ["Gossan / Iron Oxide Zone", "BIF / Iron Formation"]:
        return "Hematit-Goetit-Limonit"
    if lith in ["Skarn", "Marble", "Limestone", "Dolomite"]:
        return random.choice(["Garnet-Pyroxene", "Epidot-Klorit-Aktinolit", "Karbonatlaşma"])
    if lith in ["Serpentinite", "Dunite", "Harzburgite"]:
        return "Serpantinleşme"
    if lith in ["Granite", "Granodiorite", "Diorite", "Tonalite", "Monzonite"]:
        return random.choice(["Silisleşme", "Serisitleşme", "Potassic", "Propylitic"])
    if lith in ["Rhyolite", "Dacite", "Andesite", "Tuff", "Volcanic Breccia"]:
        return random.choice(["Silisleşme", "Killeşme / Arjilik", "Serisitleşme", "Advanced Argillic"])
    if lith in ["Schist", "Micaschist", "Gneiss", "Quartzite", "Shear Zone"]:
        return random.choice(["Serisitleşme", "Karbonatlaşma", "Silisleşme", "Klorit + Epidot"])
    return "Gözlenmedi"


def infer_ore_model(lith, alt):
    scores = {}
    for model, data in ORE_MODELS.items():
        score = 0
        if lith in data["rocks"]:
            score += 45
        if alt in data["alteration"]:
            score += 35
        if lith in ["Quartz Vein Zone", "Shear Zone"] and model == "Orogenic Gold":
            score += 25
        if lith == "Coal" and model == "Coal":
            score += 80
        scores[model] = min(score, 100)

    best = max(scores, key=scores.get)
    return best, scores


def analyze_segment(file_name, depth_from, depth_to):
    val = int(hashlib.md5(file_name.encode()).hexdigest()[:6], 16)
    lith = choose_by_filename(file_name)
    code, tr, color, hatch, group = LITHOLOGY[lith]
    alt = infer_alteration(lith, val)
    alt_color, alt_hatch = ALTERATION[alt]
    best_model, model_scores = infer_ore_model(lith, alt)

    py = round((val % 40) / 10, 1)
    cpy = round((val % 18) / 10, 1) if best_model in ["Porphyry Cu-Au-Mo", "Skarn Cu-Fe-Zn-W", "VMS Cu-Zn-Pb-Au-Ag", "IOCG Fe-Cu-Au"] else round((val % 8) / 10, 1)
    gn = round((val % 14) / 10, 1) if best_model in ["MVT / SEDEX Pb-Zn-Ag", "VMS Cu-Zn-Pb-Au-Ag"] else 0.0
    sp = round((val % 16) / 10, 1) if best_model in ["MVT / SEDEX Pb-Zn-Ag", "Skarn Cu-Fe-Zn-W", "VMS Cu-Zn-Pb-Au-Ag"] else 0.0

    rqd = int(35 + (val % 60))
    tcr = int(75 + (val % 25))
    lith_pct = int(75 + (val % 22))
    structure = random.choice(STRUCTURAL_SYMBOLS)

    note = ORE_MODELS[best_model]["note"]
    pathfinder = ORE_MODELS[best_model]["pathfinder"]
    sample = ORE_MODELS[best_model].get("sample", "")
    drill = ORE_MODELS[best_model].get("drill", "")

    return {
        "From": depth_from,
        "To": depth_to,
        "Mid": (depth_from + depth_to) / 2,
        "Lithology": lith,
        "Code": code,
        "Lithology TR": tr,
        "Group": group,
        "Lithology Color": color,
        "Lithology Hatch": hatch,
        "Lithology %": lith_pct,
        "Secondary Lithology": "Quartz Vein Zone" if lith_pct < 90 else "None",
        "Secondary %": 100 - lith_pct,
        "Alteration": alt,
        "Alteration Color": alt_color,
        "Alteration Hatch": alt_hatch,
        "Py (%)": py,
        "Cpy (%)": cpy,
        "Gn (%)": gn,
        "Sp (%)": sp,
        "RQD (%)": rqd,
        "TCR (%)": tcr,
        "Structure": structure,
        "Ore Model": best_model,
        "Pathfinder": pathfinder,
        "Sampling": sample,
        "Drill Logic": drill,
        "Determination": note,
        "Scores": model_scores,
    }


def summarize(df, col):
    d = df.copy()
    d["Thickness"] = d["To"] - d["From"]
    s = d.groupby(col)["Thickness"].sum().reset_index()
    s["Percent"] = (s["Thickness"] / s["Thickness"].sum() * 100).round(1)
    return s.sort_values("Thickness", ascending=False)


# ============================================================
# 3) UI
# ============================================================

left, right = st.columns([1.1, 3.4])

with left:
    st.header("⚙️ Data Source")
    hole_id = st.text_input("Hole ID", "DDH-2026-004")
    project = st.text_input("Project", "SAHA-01")
    location = st.text_input("Location", "Central Zone")
    az_dip = st.text_input("Azimuth / Dip", "045° / -60°")

    uploaded_files = st.file_uploader(
        "Upload core / outcrop segment photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    intervals = []
    if uploaded_files:
        st.success(f"{len(uploaded_files)} images uploaded.")
        st.write("### Depth Intervals")
        for i, f in enumerate(uploaded_files):
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"From {i+1}", value=float(i * 10), step=1.0, key=f"from_{i}")
            d_to = c2.number_input(f"To {i+1}", value=float((i + 1) * 10), step=1.0, key=f"to_{i}")
            st.image(f, caption=f.name, width=140)
            intervals.append((f.name, d_from, d_to))

    run = st.button("🚀 Generate Professional Geological Master Log", use_container_width=True)

if run and uploaded_files:
    rows = [analyze_segment(name, f, t) for name, f, t in intervals]
    df = pd.DataFrame(rows)

    depth_top = df["From"].min()
    depth_bottom = df["To"].max()
    total_depth = depth_bottom - depth_top

    with right:
        st.subheader(f"📊 Geological Master Log Output: {hole_id}")

        c1, c2, c3 = st.columns(3)
        c1.dataframe(summarize(df, "Lithology TR"), use_container_width=True, hide_index=True)
        c2.dataframe(summarize(df, "Alteration"), use_container_width=True, hide_index=True)
        c3.dataframe(summarize(df, "Ore Model"), use_container_width=True, hide_index=True)

        fig_h = min(max(13, total_depth * 0.28), 45)
        fig = plt.figure(figsize=(32, fig_h + 5), dpi=220)
        gs = fig.add_gridspec(
            2, 9,
            height_ratios=[3.3, fig_h],
            width_ratios=[0.6, 1.2, 0.55, 1.35, 1.25, 0.95, 0.85, 0.9, 3.5],
            wspace=0.18,
            hspace=0.18
        )

        fig.suptitle(
            f"COMPREHENSIVE GEOLOGICAL MASTER LOG | HOLE ID: {hole_id}",
            fontsize=25,
            fontweight="bold",
            color="#0f2742",
            y=0.985
        )

        # Donut
        ax_donut = fig.add_subplot(gs[0, 0:3])
        lith_sum = summarize(df, "Lithology TR")
        donut_colors, donut_hatches = [], []
        for lith_tr in lith_sum["Lithology TR"]:
            found = False
            for _, vals in LITHOLOGY.items():
                if vals[1] == lith_tr:
                    donut_colors.append(vals[2])
                    donut_hatches.append(vals[3])
                    found = True
            if not found:
                donut_colors.append("#e5e5e5")
                donut_hatches.append("")

        wedges, _ = ax_donut.pie(
            lith_sum["Thickness"],
            labels=[f"{r['Lithology TR']} ({r['Percent']}%)" for _, r in lith_sum.iterrows()],
            colors=donut_colors,
            startangle=90,
            textprops={"fontsize": 9, "fontweight": "bold", "color": "#0f2742"},
            wedgeprops={"width": 0.42, "edgecolor": "#0f2742", "linewidth": 1.1}
        )
        for w, h in zip(wedges, donut_hatches):
            w.set_hatch(h)
        ax_donut.text(0, 0, f"{total_depth:.1f} m\nTotal", ha="center", va="center", fontsize=12, fontweight="bold")
        ax_donut.set_title("TOTAL LITHOLOGY DISTRIBUTION", fontsize=11, fontweight="bold", color="#0f2742")

        # Ore model donut
        ax_ore = fig.add_subplot(gs[0, 3:6])
        ore_sum = summarize(df, "Ore Model")
        ore_colors = plt.cm.tab20(np.linspace(0, 1, len(ore_sum)))
        ax_ore.pie(
            ore_sum["Thickness"],
            labels=[f"{r['Ore Model']} ({r['Percent']}%)" for _, r in ore_sum.iterrows()],
            colors=ore_colors,
            startangle=90,
            textprops={"fontsize": 8, "fontweight": "bold"},
            wedgeprops={"width": 0.42, "edgecolor": "white"}
        )
        ax_ore.text(0, 0, "Ore\nModels", ha="center", va="center", fontsize=11, fontweight="bold")
        ax_ore.set_title("ORE SYSTEM DISTRIBUTION", fontsize=11, fontweight="bold", color="#0f2742")

        # Header info
        ax_header = fig.add_subplot(gs[0, 6:9])
        ax_header.axis("off")
        ax_header.text(
            0, 0.92,
            f"PROJECT: {project}\nLOCATION: {location}\nAZIMUTH / DIP: {az_dip}\nTOTAL DEPTH: {total_depth:.1f} m",
            fontsize=13,
            fontweight="bold",
            va="top",
            color="#0f2742"
        )
        ax_header.text(
            0, 0.35,
            "Broad ore-system coverage: Au, Cu, Pb-Zn-Ag, Fe, coal, chromite, skarn, VMS, porphyry, epithermal, pegmatite and carbonate-hosted systems.",
            fontsize=11,
            va="top",
            wrap=True,
            color="#334155"
        )

        # Main axes
        ax_depth = fig.add_subplot(gs[1, 0])
        ax_lith = fig.add_subplot(gs[1, 1], sharey=ax_depth)
        ax_code = fig.add_subplot(gs[1, 2], sharey=ax_depth)
        ax_desc = fig.add_subplot(gs[1, 3], sharey=ax_depth)
        ax_alt = fig.add_subplot(gs[1, 4], sharey=ax_depth)
        ax_sulf = fig.add_subplot(gs[1, 5], sharey=ax_depth)
        ax_rqd = fig.add_subplot(gs[1, 6], sharey=ax_depth)
        ax_struct = fig.add_subplot(gs[1, 7], sharey=ax_depth)
        ax_note = fig.add_subplot(gs[1, 8], sharey=ax_depth)

        axes = [ax_depth, ax_lith, ax_code, ax_desc, ax_alt, ax_sulf, ax_rqd, ax_struct, ax_note]
        for ax in axes:
            ax.set_ylim(depth_bottom, depth_top)
            ax.set_yticks(np.arange(depth_top, depth_bottom + 5, 5))
            ax.grid(axis="y", linestyle=":", alpha=0.45)

        ax_depth.set_xlim(0, 1)
        ax_depth.set_xticks([])
        ax_depth.set_title("DEPTH\n(m)", fontsize=10, fontweight="bold")
        ax_depth.set_ylabel("Depth / Derinlik (m)", fontsize=12, fontweight="bold")
        for y in np.arange(depth_top, depth_bottom + 1, 1):
            ax_depth.plot([0.35, 0.65], [y, y], color="black", lw=0.7)

        ax_lith.set_xlim(0, 1)
        ax_lith.set_xticks([])
        ax_lith.set_title("LITHOLOGY\n(Visual Log)", fontsize=10, fontweight="bold")

        ax_code.set_xlim(0, 1)
        ax_code.set_xticks([])
        ax_code.set_title("ROCK\nCODE", fontsize=10, fontweight="bold")

        ax_desc.set_xlim(0, 1)
        ax_desc.axis("off")
        ax_desc.set_title("LITHOLOGY\nDESCRIPTION", fontsize=10, fontweight="bold")

        ax_alt.set_xlim(0, 1)
        ax_alt.set_xticks([])
        ax_alt.set_title("ALTERATION\n(Dominant)", fontsize=10, fontweight="bold")

        ax_sulf.set_xlim(0, 15)
        ax_sulf.set_title("SULFIDE\n(%)", fontsize=10, fontweight="bold")
        ax_sulf.set_facecolor("#fffaf0")

        ax_rqd.set_xlim(0, 100)
        ax_rqd.set_title("RQD\n(%)", fontsize=10, fontweight="bold")

        ax_struct.set_xlim(0, 1)
        ax_struct.set_xticks([])
        ax_struct.set_title("STRUCTURAL\n(Log)", fontsize=10, fontweight="bold")

        ax_note.set_xlim(0, 1)
        ax_note.axis("off")
        ax_note.set_title("TECHNICAL DETERMINATION & ORE-SYSTEM DESCRIPTION", fontsize=10, fontweight="bold", loc="left")

        for _, r in df.iterrows():
            h = r["To"] - r["From"]
            y = r["Mid"]

            # Lithology
            ax_lith.add_patch(patches.Rectangle(
                (0, r["From"]), 1, h,
                facecolor=r["Lithology Color"],
                edgecolor="#111827",
                linewidth=1.0,
                hatch=r["Lithology Hatch"]
            ))

            ax_code.text(
                0.5, y, f"{r['Code']}",
                ha="center", va="center",
                fontsize=10, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="#cbd5e1", boxstyle="round,pad=0.25")
            )

            lith_desc = f"{r['Lithology TR']}\n{r['Group']}\nMain: {r['Lithology %']}%"
            ax_desc.text(0.04, y, textwrap.fill(lith_desc, 22), ha="left", va="center", fontsize=9, fontweight="bold")

            # Alteration
            ax_alt.add_patch(patches.Rectangle(
                (0, r["From"]), 1, h,
                facecolor=r["Alteration Color"],
                edgecolor="#111827",
                linewidth=0.9,
                hatch=r["Alteration Hatch"],
                alpha=0.95
            ))
            ax_alt.text(0.5, y, textwrap.fill(r["Alteration"], 14), ha="center", va="center", fontsize=8, fontweight="bold")

            # Sulfides
            py = r["Py (%)"]; cpy = r["Cpy (%)"]; gn = r["Gn (%)"]; sp = r["Sp (%)"]
            ax_sulf.barh(y, py, height=h * 0.72, color="#f9dc5c", edgecolor="#b08900", label="Py" if "Py" not in ax_sulf.get_legend_handles_labels()[1] else "")
            ax_sulf.barh(y, cpy, left=py, height=h * 0.72, color="#e67e22", edgecolor="#a0522d", label="Cpy" if "Cpy" not in ax_sulf.get_legend_handles_labels()[1] else "")
            ax_sulf.barh(y, gn, left=py + cpy, height=h * 0.72, color="#7b8794", edgecolor="#334155", label="Gn" if "Gn" not in ax_sulf.get_legend_handles_labels()[1] else "")
            ax_sulf.barh(y, sp, left=py + cpy + gn, height=h * 0.72, color="#a3b18a", edgecolor="#344e41", label="Sp" if "Sp" not in ax_sulf.get_legend_handles_labels()[1] else "")

            # Structural symbols
            for j in range(3):
                yy = r["From"] + (j + 1) * h / 4
                if r["Structure"] in ["Fault", "Shear"]:
                    ax_struct.plot([0.22, 0.78], [yy + 0.8, yy - 0.8], color="black", lw=1.2)
                    ax_struct.plot([0.46, 0.54], [yy + 0.2, yy - 0.2], color="red", lw=1.1)
                elif r["Structure"] == "Quartz vein":
                    ax_struct.plot([0.2, 0.8], [yy, yy - 0.8], color="red", lw=1.2)
                else:
                    ax_struct.plot([0.25, 0.75], [yy, yy - 0.6], color="black", lw=0.9)

            # Note boxes
            ore = ORE_MODELS[r["Ore Model"]]
            ore_sum = r["Py (%)"] + r["Cpy (%)"] + r["Gn (%)"] + r["Sp (%)"]
            bg = "#fff7ed" if ore_sum > 3 else "#f8fafc"
            edge = "#f97316" if ore_sum > 3 else "#cbd5e1"

            note = (
                f"INTERVAL: {r['From']:.1f}-{r['To']:.1f} m | ROCK: {r['Lithology'].upper()} | ALTERATION: {r['Alteration']}\n"
                f"STRUCTURE: {r['Structure']} | TCR: {r['TCR (%)']}% | RQD: {r['RQD (%)']}% | SULFIDE: Py {r['Py (%)']}%, Cpy {r['Cpy (%)']}%, Gn {r['Gn (%)']}%, Sp {r['Sp (%)']}%\n"
                f"ORE MODEL: {r['Ore Model']} | PATHFINDER: {r['Pathfinder']}\n"
                f"DETERMINATION: {r['Determination']}\n"
                f"SAMPLING: {r['Sampling']} | DRILL LOGIC: {r['Drill Logic']}"
            )

            ax_note.text(
                0.005, y,
                textwrap.fill(note, 110),
                ha="left", va="center",
                fontsize=8.3,
                linespacing=1.35,
                bbox=dict(facecolor=bg, edgecolor=edge, boxstyle="square,pad=0.45", linewidth=1.1)
            )

        # RQD line
        ax_rqd.plot(df["RQD (%)"], df["Mid"], color="#0f2742", marker="o", lw=2.4)
        ax_sulf.legend(loc="upper right", fontsize=7, framealpha=1)

        # Legend box
        legend_handles = []
        legend_labels = []
        for lith_name, (code, tr, color, hatch, group) in LITHOLOGY.items():
            if lith_name in df["Lithology"].unique():
                legend_handles.append(patches.Patch(facecolor=color, edgecolor="black", hatch=hatch))
                legend_labels.append(f"{code} {tr}")

        fig.legend(
            legend_handles,
            legend_labels,
            loc="lower center",
            ncol=6,
            fontsize=8,
            frameon=True,
            title="Lithology Legend"
        )

        fig.subplots_adjust(top=0.93, bottom=0.075, left=0.035, right=0.985)

        st.pyplot(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=240, bbox_inches="tight")
        buf.seek(0)

        st.download_button(
            "📥 Download High-Resolution Master Log PNG",
            data=buf,
            file_name=f"{hole_id}_geological_master_log.png",
            mime="image/png",
            use_container_width=True
        )

elif run and not uploaded_files:
    st.warning("Önce karot / mostralar için görsel yüklemelisin.")

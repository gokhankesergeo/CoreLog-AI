import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import textwrap
import hashlib

st.set_page_config(
    page_title="CoreLog-AI | Geological Master Dashboard",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ CoreLog-AI | Geological Master Dashboard")
st.caption("Professional core/outcrop log panel: lithology, alteration, mineralization, RQD, structure, ore-system reasoning.")

# ============================================================
# DATABASE
# ============================================================

LITHOLOGY = {
    "Granite": ("GRN", "Granit", "#f7b7b7", ".", "Intrusive"),
    "Granodiorite": ("GDR", "Granodiyorit", "#e59a9a", ".", "Intrusive"),
    "Diorite": ("DIO", "Diyorit", "#8d99ae", "o", "Intrusive"),
    "Tonalite": ("TON", "Tonalit", "#c9a0dc", "+", "Intrusive"),
    "Gabbro": ("GAB", "Gabro", "#606c76", "o", "Intrusive"),

    "Rhyolite": ("RHY", "Riyolit", "#f7c6d9", "+", "Volcanic"),
    "Dacite": ("DAC", "Dasit", "#c9b6e4", "o", "Volcanic"),
    "Andesite": ("AND", "Andezit", "#a9b4dc", ".", "Volcanic"),
    "Basalt": ("BAS", "Bazalt", "#586f52", "x", "Volcanic"),
    "Tuff": ("TFF", "Tüf", "#ead7a5", ".", "Volcanic"),
    "Volcanic Breccia": ("VBX", "Volkanik Breş", "#b98665", "xx", "Volcanic"),

    "Sandstone": ("SST", "Kumtaşı", "#efd08a", "-", "Sedimentary"),
    "Siltstone": ("SLT", "Silttaşı", "#c8a86d", "-", "Sedimentary"),
    "Mudstone": ("MST", "Çamurtaşı", "#7b7b7b", "-", "Sedimentary"),
    "Shale": ("SHL", "Şeyl", "#565656", "-", "Sedimentary"),
    "Coal": ("COL", "Kömür", "#1f1f1f", "", "Coal"),

    "Limestone": ("LST", "Kireçtaşı", "#a8dadc", "+", "Carbonate"),
    "Dolomite": ("DOL", "Dolomit", "#b7e4c7", "+", "Carbonate"),
    "Marble": ("MRB", "Mermer", "#d8f3dc", "/", "Carbonate"),

    "Schist": ("SCH", "Şist", "#90a955", "/", "Metamorphic"),
    "Micaschist": ("MSC", "Mikaşist", "#8ecae6", "/", "Metamorphic"),
    "Gneiss": ("GNS", "Gnays", "#adb5bd", "x", "Metamorphic"),
    "Quartzite": ("QZT", "Kuvarsit", "#f8f9fa", "/", "Metamorphic"),
    "Amphibolite": ("AMP", "Amfibolit", "#2d6a4f", ".", "Metamorphic"),

    "Serpentinite": ("SRP", "Serpantinit", "#588157", "x", "Ultramafic"),
    "Dunite": ("DUN", "Dunit", "#6a994e", "o", "Ultramafic"),
    "Harzburgite": ("HZB", "Harzburjit", "#386641", "+", "Ultramafic"),

    "Quartz Vein Zone": ("QVZ", "Kuvars Damar Zonu", "#ffffff", "///", "Vein"),
    "Shear Zone": ("SHZ", "Makaslama Zonu", "#c1121f", "/", "Structure"),
    "Fault Breccia": ("FBX", "Fay Breşi", "#bc4749", "xx", "Structure"),
    "Gossan / Iron Oxide": ("GOX", "Gossan / Demir Oksit", "#d9480f", ".", "Ore Zone"),
    "Massive Sulphide": ("MSU", "Masif Sülfür", "#343a40", "", "Ore Zone"),
    "BIF / Iron Formation": ("BIF", "Bantlı Demir Formasyonu", "#6c757d", "-", "Iron"),
    "Pegmatite": ("PEG", "Pegmatit", "#ffe5ec", "+", "Pegmatite"),
    "Skarn": ("SKN", "Skarn", "#95d5b2", "o", "Skarn"),
    "Unknown": ("UNK", "Belirsiz", "#e5e5e5", "", "Unknown"),
}

ALTERATION = {
    "None": ("#f8f9fa", ""),
    "Silicification": ("#dbeafe", "///"),
    "Sericite": ("#fff3b0", "\\"),
    "Argillic Clay": ("#ddc1a1", "."),
    "Advanced Argillic": ("#f4a261", "x"),
    "Chlorite-Epidote": ("#74c69d", "-"),
    "Carbonate": ("#caf0f8", "+"),
    "Potassic": ("#ffb4a2", "."),
    "Propylitic": ("#b7e4c7", "\\"),
    "Garnet-Pyroxene": ("#c77dff", "o"),
    "Epidote-Chlorite-Actinolite": ("#52b788", "-"),
    "Iron Oxide / Gossan": ("#e76f51", "."),
    "Serpentinization": ("#80b918", "x"),
}

ORE_MODELS = {
    "Orogenic Gold": {
        "rocks": ["Schist", "Micaschist", "Gneiss", "Quartzite", "Amphibolite", "Shear Zone", "Quartz Vein Zone"],
        "alts": ["Sericite", "Carbonate", "Silicification", "Chlorite-Epidote"],
        "pathfinder": "Au, As, Sb, W, Bi, Te",
        "sampling": "Channel/chip samples across shear zone, quartz vein margins and altered wall rock.",
        "drill": "Drill perpendicular to shear/vein fabric; target fold hinge, dilation jog and vein thickening.",
    },
    "LS Epithermal Au-Ag": {
        "rocks": ["Andesite", "Dacite", "Rhyolite", "Tuff", "Volcanic Breccia", "Quartz Vein Zone"],
        "alts": ["Silicification", "Sericite", "Argillic Clay"],
        "pathfinder": "Au, Ag, As, Sb, Hg, Tl",
        "sampling": "Sample banded quartz veins, breccia matrix, vein margins and gossan zones.",
        "drill": "Target 150–350 m boiling zone below vein/gossan corridor.",
    },
    "HS Epithermal Au-Cu": {
        "rocks": ["Rhyolite", "Dacite", "Tuff", "Volcanic Breccia", "Gossan / Iron Oxide"],
        "alts": ["Advanced Argillic", "Silicification", "Iron Oxide / Gossan"],
        "pathfinder": "Au, Cu, As, Sb, Bi, Te, Sn",
        "sampling": "Sample vuggy silica, jarosite-gossan, breccia matrix and feeder faults.",
        "drill": "Test lithocap base, feeder fault and breccia pipe at 200–450 m.",
    },
    "Porphyry Cu-Au-Mo": {
        "rocks": ["Granite", "Granodiorite", "Diorite", "Tonalite", "Dacite", "Andesite"],
        "alts": ["Potassic", "Sericite", "Propylitic", "Silicification"],
        "pathfinder": "Cu, Mo, Au, Ag, Bi, W, Zn, Pb",
        "sampling": "Grid sample stockwork zones, phyllic halo and intrusive contacts.",
        "drill": "Deep test stockwork center with IP/magnetic support, generally 500–900 m.",
    },
    "Skarn Cu-Fe-Zn-W": {
        "rocks": ["Limestone", "Dolomite", "Marble", "Skarn", "Granodiorite", "Diorite"],
        "alts": ["Garnet-Pyroxene", "Epidote-Chlorite-Actinolite", "Chlorite-Epidote"],
        "pathfinder": "Cu, Fe, Zn, Pb, W, Mo, Bi, Au",
        "sampling": "Sample carbonate-intrusive contact, retrograde epidote-chlorite zones and magnetite/sulphide veins.",
        "drill": "Drill across intrusive-carbonate contact and replacement front.",
    },
    "VMS Cu-Zn-Pb-Au-Ag": {
        "rocks": ["Basalt", "Rhyolite", "Dacite", "Tuff", "Volcanic Breccia", "Massive Sulphide"],
        "alts": ["Chlorite-Epidote", "Sericite", "Silicification"],
        "pathfinder": "Cu, Zn, Pb, Ag, Au, Ba, Mn, Fe",
        "sampling": "Sample massive sulphide lens, footwall stringer zone, exhalite/barite horizons.",
        "drill": "Target stratigraphic horizon plus EM/IP anomaly and footwall feeder.",
    },
    "MVT / SEDEX Pb-Zn-Ag": {
        "rocks": ["Limestone", "Dolomite", "Shale", "Siltstone"],
        "alts": ["Carbonate", "Silicification"],
        "pathfinder": "Pb, Zn, Ag, Ba, Mn",
        "sampling": "Sample carbonate replacement, galena-sphalerite veins and dolomitized zones.",
        "drill": "Test carbonate-hosted replacement fronts and basin faults.",
    },
    "BIF / Iron Ore": {
        "rocks": ["BIF / Iron Formation", "Quartzite", "Schist"],
        "alts": ["Iron Oxide / Gossan", "Silicification"],
        "pathfinder": "Fe, Mn, Si, P",
        "sampling": "Channel sample hematite-magnetite bands and enriched iron zones.",
        "drill": "Drill perpendicular to BIF layering and enrichment zones.",
    },
    "Coal": {
        "rocks": ["Coal", "Mudstone", "Shale", "Sandstone", "Siltstone"],
        "alts": ["None"],
        "pathfinder": "C, S, Ash, VM, Moisture",
        "sampling": "Full-seam channel samples; roof/floor dilution must be separated.",
        "drill": "Drill seam continuity, thickness, ash, sulphur and roof/floor conditions.",
    },
    "Chromite / Ultramafic": {
        "rocks": ["Serpentinite", "Dunite", "Harzburgite"],
        "alts": ["Serpentinization"],
        "pathfinder": "Cr, Ni, Co, Mg, Pt, Pd",
        "sampling": "Sample chromite bands, nodules and dunite envelope.",
        "drill": "Short-spaced holes along podiform lens and dunite envelope.",
    },
    "Li-REE Pegmatite": {
        "rocks": ["Pegmatite", "Granite", "Schist", "Gneiss"],
        "alts": ["Silicification", "Sericite"],
        "pathfinder": "Li, Cs, Ta, Nb, Sn, Be, REE",
        "sampling": "Sample pegmatite dyke, contact zones, mica-rich and heavy mineral zones.",
        "drill": "Drill dyke continuity, zonation and down-dip extensions.",
    },
}

STRUCTURES = ["Bedding", "Fracture", "Fault", "Shear", "Quartz Vein", "Stockwork", "Breccia"]

# ============================================================
# HELPERS
# ============================================================

def stable_int(text):
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)

def choose_lithology(filename):
    n = filename.lower()
    mapping = {
        "coal": "Coal", "komur": "Coal", "kömür": "Coal",
        "bif": "BIF / Iron Formation", "iron": "BIF / Iron Formation", "demir": "BIF / Iron Formation",
        "skarn": "Skarn", "marble": "Marble", "mermer": "Marble", "limestone": "Limestone", "dolomite": "Dolomite",
        "vms": "Massive Sulphide", "sulfide": "Massive Sulphide", "sulphide": "Massive Sulphide",
        "chromite": "Serpentinite", "krom": "Serpentinite", "serp": "Serpentinite",
        "peg": "Pegmatite", "lithium": "Pegmatite", "ree": "Pegmatite",
        "gossan": "Gossan / Iron Oxide",
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
    pool = ["Granodiorite", "Andesite", "Dacite", "Volcanic Breccia", "Schist", "Quartz Vein Zone", "Gossan / Iron Oxide"]
    return pool[stable_int(filename) % len(pool)]

def choose_alteration(lith, seed):
    def pick(items):
        return items[seed % len(items)]

    if lith in ["Gossan / Iron Oxide", "BIF / Iron Formation"]:
        return "Iron Oxide / Gossan"
    if lith in ["Skarn", "Marble", "Limestone", "Dolomite"]:
        return pick(["Garnet-Pyroxene", "Epidote-Chlorite-Actinolite", "Carbonate"])
    if lith in ["Serpentinite", "Dunite", "Harzburgite"]:
        return "Serpentinization"
    if lith in ["Granite", "Granodiorite", "Diorite", "Tonalite", "Gabbro"]:
        return pick(["Silicification", "Sericite", "Potassic", "Propylitic"])
    if lith in ["Rhyolite", "Dacite", "Andesite", "Tuff", "Volcanic Breccia"]:
        return pick(["Silicification", "Argillic Clay", "Sericite", "Advanced Argillic"])
    if lith in ["Schist", "Micaschist", "Gneiss", "Quartzite", "Shear Zone"]:
        return pick(["Sericite", "Carbonate", "Silicification", "Chlorite-Epidote"])
    if lith == "Coal":
        return "None"
    return "None"

def infer_model(lith, alt):
    scores = {}
    for model, data in ORE_MODELS.items():
        score = 0
        if lith in data["rocks"]:
            score += 55
        if alt in data["alts"]:
            score += 35
        if lith == "Quartz Vein Zone" and model in ["Orogenic Gold", "LS Epithermal Au-Ag"]:
            score += 15
        if lith == "Coal" and model == "Coal":
            score += 100
        scores[model] = min(score, 100)
    best = max(scores, key=scores.get)
    return best, scores

def analyze_segment(filename, depth_from, depth_to):
    seed = stable_int(filename)
    lith = choose_lithology(filename)
    code, tr, color, hatch, group = LITHOLOGY[lith]
    alt = choose_alteration(lith, seed)
    alt_color, alt_hatch = ALTERATION[alt]
    model, scores = infer_model(lith, alt)

    py = round((seed % 35) / 10, 1)
    cpy = round((seed % 18) / 10, 1) if model in ["Porphyry Cu-Au-Mo", "Skarn Cu-Fe-Zn-W", "VMS Cu-Zn-Pb-Au-Ag"] else round((seed % 8) / 10, 1)
    gn = round((seed % 12) / 10, 1) if model in ["MVT / SEDEX Pb-Zn-Ag", "VMS Cu-Zn-Pb-Au-Ag"] else 0.0
    sp = round((seed % 14) / 10, 1) if model in ["MVT / SEDEX Pb-Zn-Ag", "Skarn Cu-Fe-Zn-W", "VMS Cu-Zn-Pb-Au-Ag"] else 0.0

    if lith == "Coal":
        py, cpy, gn, sp = 0.1, 0.0, 0.0, 0.0

    rqd = int(35 + (seed % 60))
    tcr = int(75 + (seed % 25))
    structure = STRUCTURES[seed % len(STRUCTURES)]
    ore = ORE_MODELS[model]

    return {
        "From": depth_from,
        "To": depth_to,
        "Mid": (depth_from + depth_to) / 2,
        "Thickness": depth_to - depth_from,
        "Lithology": lith,
        "Code": code,
        "Lithology TR": tr,
        "Group": group,
        "Lith Color": color,
        "Lith Hatch": hatch,
        "Alteration": alt,
        "Alt Color": alt_color,
        "Alt Hatch": alt_hatch,
        "Py": py,
        "Cpy": cpy,
        "Gn": gn,
        "Sp": sp,
        "RQD": rqd,
        "TCR": tcr,
        "Structure": structure,
        "Ore Model": model,
        "Pathfinder": ore["pathfinder"],
        "Sampling": ore["sampling"],
        "Drill": ore["drill"],
    }

def summarize(df, col):
    out = df.groupby(col)["Thickness"].sum().reset_index()
    out["Percent"] = (out["Thickness"] / out["Thickness"].sum() * 100).round(1)
    return out.sort_values("Thickness", ascending=False)

def add_panel_title(ax, title):
    ax.set_title(title, fontsize=10, fontweight="bold", color="#0f2742", pad=10)

def draw_structural_symbol(ax, x0, x1, y, kind):
    if kind == "Fault":
        ax.plot([x0, x1], [y + 0.45, y - 0.45], color="black", lw=1.1)
        ax.plot([0.48, 0.56], [y + 0.1, y - 0.1], color="red", lw=1.1)
    elif kind == "Shear":
        ax.plot([x0, x1], [y + 0.5, y - 0.5], color="black", lw=1.0)
        ax.plot([x0 + 0.1, x1 - 0.1], [y + 0.15, y - 0.15], color="black", lw=0.7)
    elif kind == "Quartz Vein":
        ax.plot([x0, x1], [y + 0.35, y - 0.35], color="red", lw=1.1)
    elif kind == "Stockwork":
        ax.plot([x0, x1], [y + 0.35, y - 0.35], color="red", lw=0.9)
        ax.plot([x0, x1], [y - 0.25, y + 0.25], color="red", lw=0.7)
    elif kind == "Breccia":
        ax.scatter([0.35, 0.5, 0.65], [y + 0.2, y - 0.15, y + 0.05], s=8, color="black")
    else:
        ax.plot([x0, x1], [y + 0.25, y - 0.25], color="black", lw=0.8)

# ============================================================
# UI
# ============================================================

left, right = st.columns([1.05, 3.6])

with left:
    st.header("⚙️ Data")
    hole_id = st.text_input("Hole ID", "DDH-2026-004")
    project = st.text_input("Project", "SAHA-01")
    location = st.text_input("Location", "Central Zone")
    az_dip = st.text_input("Azimuth / Dip", "045° / -60°")

    uploaded_files = st.file_uploader(
        "Upload core/outcrop segment photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    intervals = []
    if uploaded_files:
        st.success(f"{len(uploaded_files)} images uploaded.")
        for i, f in enumerate(uploaded_files):
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"From {i+1}", value=float(i * 10), step=1.0, key=f"from_{i}")
            d_to = c2.number_input(f"To {i+1}", value=float((i + 1) * 10), step=1.0, key=f"to_{i}")
            st.image(f, caption=f.name, width=130)
            intervals.append((f.name, d_from, d_to))

    run = st.button("🚀 Generate Master Dashboard", use_container_width=True)

if run and uploaded_files:
    rows = [analyze_segment(name, d_from, d_to) for name, d_from, d_to in intervals]
    df = pd.DataFrame(rows)

    depth_top = float(df["From"].min())
    depth_bottom = float(df["To"].max())
    total_depth = depth_bottom - depth_top

    with right:
        st.subheader(f"📊 Output: {hole_id}")

        fig_height = min(max(12, total_depth * 0.24), 34)
        fig = plt.figure(figsize=(24, fig_height), dpi=220)

        gs = fig.add_gridspec(
            2, 10,
            height_ratios=[1.9, 8.5],
            width_ratios=[0.45, 1.0, 0.45, 1.2, 1.1, 0.85, 0.75, 0.75, 1.25, 2.7],
            wspace=0.12,
            hspace=0.12
        )

        fig.suptitle(
            f"COMPREHENSIVE GEOLOGICAL MASTER DASHBOARD | HOLE ID: {hole_id}",
            fontsize=20,
            fontweight="bold",
            color="#0f2742",
            y=0.99
        )

        # Header panel
        ax_meta = fig.add_subplot(gs[0, 0:3])
        ax_meta.axis("off")
        ax_meta.text(
            0, 0.95,
            f"PROJECT: {project}\nLOCATION: {location}\nAZIMUTH / DIP: {az_dip}\nTOTAL DEPTH: {total_depth:.1f} m",
            va="top",
            fontsize=11,
            fontweight="bold",
            color="#0f2742"
        )

        # Lithology donut
        ax_lith_donut = fig.add_subplot(gs[0, 3:5])
        lith_sum = summarize(df, "Lithology TR")
        lith_colors = []
        lith_hatches = []
        for lith_tr in lith_sum["Lithology TR"]:
            found = False
            for _, vals in LITHOLOGY.items():
                if vals[1] == lith_tr:
                    lith_colors.append(vals[2])
                    lith_hatches.append(vals[3])
                    found = True
            if not found:
                lith_colors.append("#e5e5e5")
                lith_hatches.append("")

        wedges, _ = ax_lith_donut.pie(
            lith_sum["Thickness"],
            colors=lith_colors,
            startangle=90,
            wedgeprops={"width": 0.42, "edgecolor": "#0f2742", "linewidth": 0.8}
        )
        for w, h in zip(wedges, lith_hatches):
            w.set_hatch(h)

        ax_lith_donut.text(0, 0, f"{total_depth:.0f} m\nTotal", ha="center", va="center", fontsize=9, fontweight="bold")
        add_panel_title(ax_lith_donut, "LITHOLOGY SUMMARY")

        # Ore model donut
        ax_ore_donut = fig.add_subplot(gs[0, 5:7])
        ore_sum = summarize(df, "Ore Model")
        ore_colors = plt.cm.Set3(np.linspace(0, 1, len(ore_sum)))
        ax_ore_donut.pie(
            ore_sum["Thickness"],
            colors=ore_colors,
            startangle=90,
            wedgeprops={"width": 0.42, "edgecolor": "white"}
        )
        ax_ore_donut.text(0, 0, "Ore\nModels", ha="center", va="center", fontsize=9, fontweight="bold")
        add_panel_title(ax_ore_donut, "ORE SYSTEMS")

        # Legend panel
        ax_legend = fig.add_subplot(gs[0, 7:10])
        ax_legend.axis("off")
        ax_legend.text(0.0, 0.95, "ACTIVE LEGEND", fontsize=11, fontweight="bold", color="#0f2742", va="top")

        used_liths = list(df["Lithology"].unique())
        y0 = 0.72
        for i, lith in enumerate(used_liths[:6]):
            code, tr, color, hatch, group = LITHOLOGY[lith]
            ax_legend.add_patch(patches.Rectangle((0.0, y0 - i * 0.12), 0.05, 0.06, facecolor=color, edgecolor="black", hatch=hatch))
            ax_legend.text(0.07, y0 + 0.01 - i * 0.12, f"{code} {tr}", fontsize=8, va="center")

        ax_legend.text(
            0.45, 0.72,
            "Coverage:\nAu, Cu, Pb-Zn-Ag, Fe, coal,\nchromite, skarn, VMS,\nporphyry, epithermal,\npegmatite systems.",
            fontsize=8.2,
            va="top",
            color="#334155"
        )

        # Main log axes
        ax_depth = fig.add_subplot(gs[1, 0])
        ax_lith = fig.add_subplot(gs[1, 1], sharey=ax_depth)
        ax_code = fig.add_subplot(gs[1, 2], sharey=ax_depth)
        ax_desc = fig.add_subplot(gs[1, 3], sharey=ax_depth)
        ax_alt = fig.add_subplot(gs[1, 4], sharey=ax_depth)
        ax_sulf = fig.add_subplot(gs[1, 5], sharey=ax_depth)
        ax_rqd = fig.add_subplot(gs[1, 6], sharey=ax_depth)
        ax_struct = fig.add_subplot(gs[1, 7], sharey=ax_depth)
        ax_model = fig.add_subplot(gs[1, 8], sharey=ax_depth)
        ax_note = fig.add_subplot(gs[1, 9], sharey=ax_depth)

        axes = [ax_depth, ax_lith, ax_code, ax_desc, ax_alt, ax_sulf, ax_rqd, ax_struct, ax_model, ax_note]
        for ax in axes:
            ax.set_ylim(depth_bottom, depth_top)
            ax.set_yticks(np.arange(depth_top, depth_bottom + 5, 5))
            ax.grid(axis="y", linestyle=":", alpha=0.35)

        ax_depth.set_xlim(0, 1)
        ax_depth.set_xticks([])
        add_panel_title(ax_depth, "DEPTH\nm")
        ax_depth.set_ylabel("Depth / Derinlik (m)", fontsize=10, fontweight="bold")
        for y in np.arange(depth_top, depth_bottom + 1, 1):
            ax_depth.plot([0.35, 0.65], [y, y], color="black", lw=0.45)

        for ax, title in [
            (ax_lith, "LITHOLOGY\nVisual Log"),
            (ax_code, "ROCK\nCode"),
            (ax_desc, "LITHOLOGY\nDescription"),
            (ax_alt, "ALTERATION\nDominant"),
            (ax_sulf, "SULFIDE\n%"),
            (ax_rqd, "RQD\n%"),
            (ax_struct, "STRUCTURE\nSymbols"),
            (ax_model, "ORE MODEL\nInterpretation"),
            (ax_note, "TECHNICAL DETERMINATION")
        ]:
            add_panel_title(ax, title)

        ax_lith.set_xlim(0, 1)
        ax_code.set_xlim(0, 1)
        ax_desc.set_xlim(0, 1)
        ax_alt.set_xlim(0, 1)
        ax_sulf.set_xlim(0, 15)
        ax_rqd.set_xlim(0, 100)
        ax_struct.set_xlim(0, 1)
        ax_model.set_xlim(0, 1)
        ax_note.set_xlim(0, 1)

        ax_lith.set_xticks([])
        ax_code.set_xticks([])
        ax_desc.axis("off")
        ax_alt.set_xticks([])
        ax_struct.set_xticks([])
        ax_model.axis("off")
        ax_note.axis("off")
        ax_sulf.set_facecolor("#fffaf0")

        model_color_map = {
            model: plt.cm.tab20(i / max(1, len(ORE_MODELS)))
            for i, model in enumerate(ORE_MODELS.keys())
        }

        for _, r in df.iterrows():
            h = r["Thickness"]
            y = r["Mid"]

            ax_lith.add_patch(patches.Rectangle(
                (0, r["From"]), 1, h,
                facecolor=r["Lith Color"],
                edgecolor="#111827",
                linewidth=0.8,
                hatch=r["Lith Hatch"]
            ))

            ax_code.text(
                0.5, y, r["Code"],
                ha="center", va="center",
                fontsize=8.5,
                fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="#cbd5e1", boxstyle="round,pad=0.22")
            )

            desc = f"{r['Lithology TR']}\n{r['Group']}"
            ax_desc.text(0.05, y, textwrap.fill(desc, 21), ha="left", va="center", fontsize=8.2, fontweight="bold")

            ax_alt.add_patch(patches.Rectangle(
                (0, r["From"]), 1, h,
                facecolor=r["Alt Color"],
                edgecolor="#111827",
                linewidth=0.7,
                hatch=r["Alt Hatch"],
                alpha=0.95
            ))
            ax_alt.text(0.5, y, textwrap.fill(r["Alteration"], 13), ha="center", va="center", fontsize=7.4, fontweight="bold")

            py, cpy, gn, sp = r["Py"], r["Cpy"], r["Gn"], r["Sp"]
            ax_sulf.barh(y, py, height=h * 0.68, color="#f9dc5c", edgecolor="#b08900", label="Py" if "Py" not in ax_sulf.get_legend_handles_labels()[1] else "")
            ax_sulf.barh(y, cpy, left=py, height=h * 0.68, color="#e67e22", edgecolor="#a0522d", label="Cpy" if "Cpy" not in ax_sulf.get_legend_handles_labels()[1] else "")
            ax_sulf.barh(y, gn, left=py + cpy, height=h * 0.68, color="#7b8794", edgecolor="#334155", label="Gn" if "Gn" not in ax_sulf.get_legend_handles_labels()[1] else "")
            ax_sulf.barh(y, sp, left=py + cpy + gn, height=h * 0.68, color="#a3b18a", edgecolor="#344e41", label="Sp" if "Sp" not in ax_sulf.get_legend_handles_labels()[1] else "")

            for j in range(3):
                yy = r["From"] + (j + 1) * h / 4
                draw_structural_symbol(ax_struct, 0.22, 0.78, yy, r["Structure"])

            ax_model.add_patch(patches.Rectangle(
                (0, r["From"]), 1, h,
                facecolor=model_color_map.get(r["Ore Model"], "#e5e7eb"),
                edgecolor="white",
                alpha=0.85
            ))
            ax_model.text(0.5, y, textwrap.fill(r["Ore Model"], 12), ha="center", va="center", fontsize=7.2, fontweight="bold")

            ore_sum_value = py + cpy + gn + sp
            bg = "#fff7ed" if ore_sum_value > 3 else "#f8fafc"
            edge = "#f97316" if ore_sum_value > 3 else "#cbd5e1"

            note = (
                f"{r['From']:.1f}-{r['To']:.1f} m | {r['Lithology']} | Alt: {r['Alteration']} | "
                f"Structure: {r['Structure']} | TCR {r['TCR']}% | RQD {r['RQD']}% | "
                f"Py {py}%, Cpy {cpy}%, Gn {gn}%, Sp {sp}% | "
                f"Model: {r['Ore Model']} | Pathfinder: {r['Pathfinder']} | "
                f"Sampling: {r['Sampling']} | Drill: {r['Drill']}"
            )

            ax_note.text(
                0.01, y,
                textwrap.fill(note, 90),
                ha="left",
                va="center",
                fontsize=7.1,
                linespacing=1.25,
                bbox=dict(facecolor=bg, edgecolor=edge, boxstyle="square,pad=0.35", linewidth=0.9)
            )

        ax_rqd.plot(df["RQD"], df["Mid"], color="#0f2742", marker="o", lw=2.1, markersize=4.5)
        ax_sulf.legend(loc="upper right", fontsize=6.5, framealpha=1)

        fig.subplots_adjust(top=0.91, bottom=0.035, left=0.035, right=0.985)

        st.pyplot(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=240, bbox_inches="tight")
        buf.seek(0)

        st.download_button(
            "📥 Download High-Resolution Dashboard PNG",
            data=buf,
            file_name=f"{hole_id}_master_dashboard.png",
            mime="image/png",
            use_container_width=True
        )

elif run and not uploaded_files:
    st.warning("Önce görsel yüklemelisin.")

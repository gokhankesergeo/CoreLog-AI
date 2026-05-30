import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from openai import OpenAI
import base64
import json
import io
import textwrap
import re

# ==========================================================
# CORELOG-AI REAL VISION VERSION
# Developed for AI-assisted geological core/chip logging
# ==========================================================

st.set_page_config(page_title="CoreLog-AI Vision Logger", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

LITHOLOGY_STYLE = {
    "GDR": ("Granodiorite", "#f4b6bd", ".."),
    "GRN": ("Granite", "#f5c1c1", ".."),
    "DIO": ("Diorite", "#9aa6b2", "o"),
    "AND": ("Andesite", "#b9c7e6", "vv"),
    "BAS": ("Basalt", "#6b7280", "xx"),
    "DAC": ("Dacite", "#cbb7e8", "oo"),
    "RHY": ("Rhyolite", "#e6c8e6", "++"),
    "TFF": ("Tuff / Lapilli Tuff", "#d9c095", "^"),
    "VBX": ("Volcanic Breccia", "#b98b63", "xx"),
    "QZV": ("Quartz Vein / Stockwork", "#f7f7f7", "//"),
    "LST": ("Limestone / Marble", "#b9ddd6", "+"),
    "DOL": ("Dolomite", "#cfd6c4", "++"),
    "SKN": ("Skarn", "#8faa73", "xx"),
    "BIF": ("Banded Iron Formation", "#8d7a90", "=="),
    "SST": ("Sandstone", "#e5c48f", ".."),
    "SHL": ("Shale / Mudstone", "#9aa0a6", "--"),
    "CLN": ("Coal / Carbonaceous Unit", "#2d2d2d", "//"),
    "MYL": ("Mylonite / Shear Zone", "#7c6f64", "\\\\"),
    "FLT": ("Fault Gouge / Broken Zone", "#c2b280", "**"),
    "UNK": ("Unknown / Mixed", "#e5e7eb", ""),
}

ALTERATION_STYLE = {
    "none": "#f8f9fa",
    "silicification": "#dfeaf2",
    "argillic": "#f5e7ad",
    "chlorite": "#cddfbd",
    "epidote": "#a7d8a4",
    "sericite": "#efe3bf",
    "carbonate": "#d7e7df",
    "iron oxide": "#f0a0a0",
    "hematite": "#e79a8a",
    "magnetite": "#8d99ae",
    "potassic": "#f6c5cf",
    "propylitic": "#b6d9b6",
    "skarn": "#9bbf8f",
    "garnet": "#c56b6b",
    "graphitic": "#555555",
    "coal": "#1f2937",
    "uranium redox": "#e0c46c",
    "clay": "#d8c3a5",
}

ORE_SYSTEMS = [
    "Unknown / general exploration",
    "Orogenic gold",
    "Epithermal Au-Ag",
    "Porphyry Cu-Au",
    "VMS base metals",
    "Skarn Fe-Cu-Au",
    "Iron ore / BIF / magnetite-hematite",
    "Uranium / redox system",
    "Coal / carbonaceous basin",
    "MVT / SEDEX Pb-Zn-Ag",
    "Lithium pegmatite / REE",
    "Industrial minerals"
]

def safe_json_loads(text):
    text = text.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)

def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

def normalize_code(code):
    if not code:
        return "UNK"
    code = str(code).upper().strip()
    return code if code in LITHOLOGY_STYLE else "UNK"

def alteration_color(alterations):
    if not alterations:
        return ALTERATION_STYLE["none"]
    joined = " ".join([str(a).lower() for a in alterations])
    for key, color in ALTERATION_STYLE.items():
        if key in joined:
            return color
    return "#f8f9fa"

def analyze_core_image_with_ai(image_bytes, from_m, to_m, ore_context):
    image_b64 = image_to_base64(image_bytes)

    prompt = f"""
You are a senior exploration geologist, core logging specialist and economic geology consultant.

Analyze the uploaded drill core / chip tray image visually.

Depth interval:
FROM = {from_m} m
TO = {to_m} m

Exploration context:
{ore_context}

Return ONLY valid JSON. Do not use markdown.

Critical rules:
1. Do NOT invent assay grades.
2. Do NOT claim certainty for minerals that cannot be visually confirmed.
3. RQD from a photo is only a visual estimate unless exact piece lengths and scale are visible.
4. If the image has broken core/chips, estimate fracture intensity and give low/medium confidence.
5. Identify possible lithology, texture, colour, alteration, oxidation, veining, brecciation, shear, fault gouge, mylonite, clay, chlorite, epidote, garnet, pyrite, chalcopyrite, galena, sphalerite, magnetite, hematite, graphite/carbonaceous material, coal, uranium redox indicators if visually relevant.
6. Give guidance for possible deposit systems: gold, copper, iron, uranium, coal, base metals, skarn, VMS, porphyry, epithermal, orogenic gold.
7. If uncertain, say uncertain.

Use this exact JSON schema:
{{
  "from_m": {from_m},
  "to_m": {to_m},
  "primary_lithology": "string",
  "lithology_code": "one of GDR, GRN, DIO, AND, BAS, DAC, RHY, TFF, VBX, QZV, LST, DOL, SKN, BIF, SST, SHL, CLN, MYL, FLT, UNK",
  "secondary_lithology": "string or none",
  "texture": "string",
  "colour": "string",
  "grain_size": "string",
  "alteration": ["string"],
  "alteration_intensity": "none/weak/moderate/strong/intense/uncertain",
  "visible_structures": ["string"],
  "fracture_intensity": "low/moderate/high/very high",
  "possible_fault_or_shear": "yes/no/uncertain",
  "visual_rqd_estimate_percent": number,
  "rqd_confidence": "low/medium/high",
  "tcr_visual_estimate_percent": number,
  "sulfide_visual_estimate_percent": number,
  "sulfide_confidence": "low/medium/high",
  "visible_sulfides": ["string"],
  "visible_oxides": ["string"],
  "indicator_minerals": ["string"],
  "ore_system_indicators": ["string"],
  "possible_deposit_models": ["string"],
  "economic_potential": "low/moderate/high/unknown",
  "recommended_follow_up": ["string"],
  "geological_note": "string",
  "confidence": "low/medium/high"
}}
"""

    response = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                    },
                ],
            }
        ],
    )

    return safe_json_loads(response.output_text)

def build_rows_from_ai_results(ai_results):
    rows = []
    for r in ai_results:
        code = normalize_code(r.get("lithology_code", "UNK"))
        lith_name, color, hatch = LITHOLOGY_STYLE[code]
        alt_list = r.get("alteration", [])
        if not isinstance(alt_list, list):
            alt_list = [str(alt_list)]

        visible_sulfides = r.get("visible_sulfides", [])
        visible_oxides = r.get("visible_oxides", [])
        indicator_minerals = r.get("indicator_minerals", [])
        structures = r.get("visible_structures", [])
        deposit_models = r.get("possible_deposit_models", [])
        follow_up = r.get("recommended_follow_up", [])

        rows.append({
            "From": float(r.get("from_m", 0)),
            "To": float(r.get("to_m", 0)),
            "LithCode": code,
            "Lithology": r.get("primary_lithology", lith_name),
            "SecondaryLithology": r.get("secondary_lithology", "none"),
            "Texture": r.get("texture", "uncertain"),
            "Colour": r.get("colour", "uncertain"),
            "GrainSize": r.get("grain_size", "uncertain"),
            "Alteration": ", ".join(alt_list),
            "AlterationIntensity": r.get("alteration_intensity", "uncertain"),
            "Structures": ", ".join(structures),
            "FaultShear": r.get("possible_fault_or_shear", "uncertain"),
            "FractureIntensity": r.get("fracture_intensity", "uncertain"),
            "RQD_%": float(r.get("visual_rqd_estimate_percent", 0)),
            "RQD_Confidence": r.get("rqd_confidence", "low"),
            "TCR_%": float(r.get("tcr_visual_estimate_percent", 0)),
            "Sulfide_%": float(r.get("sulfide_visual_estimate_percent", 0)),
            "SulfideConfidence": r.get("sulfide_confidence", "low"),
            "VisibleSulfides": ", ".join(visible_sulfides),
            "VisibleOxides": ", ".join(visible_oxides),
            "IndicatorMinerals": ", ".join(indicator_minerals),
            "OreIndicators": ", ".join(r.get("ore_system_indicators", [])),
            "DepositModels": ", ".join(deposit_models),
            "EconomicPotential": r.get("economic_potential", "unknown"),
            "FollowUp": ", ".join(follow_up),
            "GeologicalNote": r.get("geological_note", "No note."),
            "Confidence": r.get("confidence", "low"),
            "Color": color,
            "Hatch": hatch,
            "AltColor": alteration_color(alt_list),
        })

    df = pd.DataFrame(rows)
    df["Thickness"] = df["To"] - df["From"]
    df["Mid"] = (df["From"] + df["To"]) / 2
    return df.sort_values("From").reset_index(drop=True)

def summarize_lithology(df):
    s = df.groupby(["LithCode", "Lithology", "Color", "Hatch"], as_index=False)["Thickness"].sum()
    total = s["Thickness"].sum()
    s["Percent"] = np.where(total > 0, s["Thickness"] / total * 100, 0)
    return s.sort_values("Thickness", ascending=False)

def draw_structure_symbol(ax, x, y, name, color="#111111"):
    name = str(name).lower()
    if "fault" in name:
        ax.plot([x - 0.08, x + 0.08], [y + 0.08, y - 0.08], color=color, lw=1.0)
        ax.plot([x - 0.03, x + 0.02], [y + 0.01, y + 0.05], color=color, lw=1.0)
    elif "shear" in name or "mylonite" in name:
        ax.plot([x - 0.09, x + 0.09], [y + 0.06, y - 0.06], color=color, lw=1.0)
        ax.plot([x - 0.07, x + 0.07], [y + 0.00, y - 0.12], color=color, lw=1.0)
    elif "vein" in name or "quartz" in name:
        ax.plot([x - 0.09, x + 0.09], [y + 0.05, y - 0.05], color="#c62828", lw=1.1)
        ax.plot([x - 0.08, x + 0.08], [y + 0.09, y - 0.01], color="#c62828", lw=0.8)
    elif "breccia" in name:
        tri = patches.RegularPolygon((x, y), 3, radius=0.055, orientation=0.3, facecolor="none", edgecolor=color, lw=1.0)
        ax.add_patch(tri)
    else:
        ax.plot([x - 0.08, x + 0.06], [y - 0.08, y + 0.08], color=color, lw=0.9)

def make_master_log(df, project, location, hole_id, azdip, date_txt):
    depth_top = float(df["From"].min())
    depth_bottom = float(df["To"].max())
    total_depth = depth_bottom - depth_top

    fig = plt.figure(figsize=(18, 11), dpi=170)

    gs = GridSpec(
        1, 10,
        figure=fig,
        width_ratios=[0.55, 1.35, 0.58, 1.75, 1.55, 1.25, 1.3, 1.15, 2.6, 2.4],
        wspace=0.09,
    )

    ax_depth = fig.add_subplot(gs[0, 0])
    ax_lith = fig.add_subplot(gs[0, 1], sharey=ax_depth)
    ax_code = fig.add_subplot(gs[0, 2], sharey=ax_depth)
    ax_desc = fig.add_subplot(gs[0, 3], sharey=ax_depth)
    ax_alt = fig.add_subplot(gs[0, 4], sharey=ax_depth)
    ax_sulf = fig.add_subplot(gs[0, 5], sharey=ax_depth)
    ax_rqd = fig.add_subplot(gs[0, 6], sharey=ax_depth)
    ax_struct = fig.add_subplot(gs[0, 7], sharey=ax_depth)
    ax_marks = fig.add_subplot(gs[0, 8], sharey=ax_depth)
    ax_side = fig.add_subplot(gs[0, 9])

    axes_depth = [ax_depth, ax_lith, ax_code, ax_desc, ax_alt, ax_sulf, ax_rqd, ax_struct, ax_marks]

    for ax in axes_depth:
        ax.set_ylim(depth_bottom, depth_top)
        ax.set_facecolor("white")
        ax.grid(axis="y", color="#d0d0d0", lw=0.45, ls="--", alpha=0.8)
        for spine in ax.spines.values():
            spine.set_color("#9ca3af")
            spine.set_linewidth(0.7)

    fig.suptitle(
        f"COMPREHENSIVE GEOLOGICAL MASTER LOG | HOLE ID: {hole_id}",
        y=0.985,
        fontsize=15,
        fontweight="bold",
        color="#0b1d3a",
    )

    fig.text(0.07, 0.953, f"PROJECT: {project}", fontsize=8, fontweight="bold")
    fig.text(0.20, 0.953, f"LOCATION: {location}", fontsize=8)
    fig.text(0.36, 0.953, f"AZIMUTH / DIP: {azdip}", fontsize=8, fontweight="bold")
    fig.text(0.52, 0.953, f"TOTAL DEPTH: {total_depth:.1f} m", fontsize=8, fontweight="bold")
    fig.text(0.66, 0.953, f"DATE: {date_txt}", fontsize=8, fontweight="bold")

    major = np.arange(np.floor(depth_top / 5) * 5, depth_bottom + 5, 5)
    minor = np.arange(np.floor(depth_top), depth_bottom + 1, 1)

    ax_depth.set_xlim(0, 1)
    ax_depth.set_title("DEPTH\n(m)", fontsize=8, fontweight="bold", pad=10)
    ax_depth.set_yticks(major)
    ax_depth.set_yticks(minor, minor=True)
    ax_depth.set_xticks([])
    ax_depth.tick_params(axis="y", which="major", length=7, width=1, labelsize=8)
    ax_depth.tick_params(axis="y", which="minor", length=3, width=0.6)

    titles = [
        (ax_lith, "LITHOLOGY\n(Visual Log)"),
        (ax_code, "ROCK\nCODE"),
        (ax_desc, "LITHOLOGY\nDESCRIPTION"),
        (ax_alt, "ALTERATION\n(Dominant)"),
        (ax_sulf, "SULFIDE\n(%)"),
        (ax_rqd, "RQD\n(%)"),
        (ax_struct, "STRUCTURAL\n(Log)"),
        (ax_marks, "AI GEOLOGICAL INTERPRETATION"),
    ]

    for ax, title in titles:
        ax.set_title(title, fontsize=8, fontweight="bold", pad=10)
        ax.set_yticklabels([])

    for ax in [ax_lith, ax_code, ax_desc, ax_alt, ax_struct, ax_marks]:
        ax.set_xlim(0, 1)
        ax.set_xticks([])

    ax_sulf.set_xlim(0, max(5, float(df["Sulfide_%"].max()) * 1.35))
    ax_sulf.grid(axis="x", color="#dddddd", ls="--", lw=0.5)

    ax_rqd.set_xlim(0, 100)
    ax_rqd.set_xticks([0, 50, 100])
    ax_rqd.grid(axis="x", color="#dddddd", ls="--", lw=0.5)

    for _, r in df.iterrows():
        y0 = float(r["From"])
        y1 = float(r["To"])
        thick = float(r["Thickness"])
        mid = float(r["Mid"])

        ax_lith.add_patch(
            patches.Rectangle(
                (0, y0), 1, thick,
                facecolor=r["Color"],
                edgecolor="#333",
                lw=0.65,
                hatch=r["Hatch"],
                alpha=0.95,
            )
        )
        ax_lith.text(
            0.5, mid,
            f"[{r['LithCode']}]\n{r['Lithology']}",
            ha="center",
            va="center",
            fontsize=6.5,
            fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="#777", alpha=0.9, boxstyle="round,pad=0.25"),
        )

        ax_code.text(0.5, mid, r["LithCode"], ha="center", va="center", fontsize=8, fontweight="bold")

        desc = (
            f"{r['Lithology']}\n"
            f"Colour: {r['Colour']}\n"
            f"Texture: {r['Texture']}\n"
            f"Grain size: {r['GrainSize']}\n"
            f"Secondary: {r['SecondaryLithology']}"
        )
        ax_desc.text(0.04, mid, textwrap.fill(desc, 26), ha="left", va="center", fontsize=6.5)

        ax_alt.add_patch(
            patches.Rectangle(
                (0, y0), 1, thick,
                facecolor=r["AltColor"],
                edgecolor="#333",
                lw=0.55,
                alpha=0.82,
            )
        )
        ax_alt.text(
            0.5, mid,
            textwrap.fill(f"{r['Alteration']}\n{r['AlterationIntensity']}", 16),
            ha="center",
            va="center",
            fontsize=6.3,
            fontweight="bold",
        )

        ax_sulf.barh(
            mid,
            float(r["Sulfide_%"]),
            height=thick * 0.75,
            left=0,
            color="#e8773d",
            edgecolor="#b45309",
            alpha=0.9,
        )

        structures = str(r["Structures"]).split(",")
        if len(structures) == 0 or structures == [""]:
            structures = ["fracture"]

        rng = np.random.default_rng(int((mid + 1) * 1000) % 999999)
        n_symbols = max(2, min(8, int(thick / 2) + 1))
        for i in range(n_symbols):
            yy = float(rng.uniform(y0 + thick * 0.15, y1 - thick * 0.15)) if thick > 1 else mid
            xx = float(rng.uniform(0.2, 0.8))
            symbol_name = structures[i % len(structures)]
            draw_structure_symbol(ax_struct, xx, yy, symbol_name)

        note = (
            f"{r['From']:.1f}–{r['To']:.1f} m | {r['Lithology']} ({r['LithCode']})\n"
            f"Fracturing: {r['FractureIntensity']} | RQD visual est.: {r['RQD_%']:.0f}% ({r['RQD_Confidence']} confidence)\n"
            f"Sulfide visual est.: {r['Sulfide_%']:.1f}% ({r['SulfideConfidence']} confidence)\n"
            f"Visible sulfides: {r['VisibleSulfides']}\n"
            f"Oxides / indicators: {r['VisibleOxides']} | {r['IndicatorMinerals']}\n"
            f"Possible models: {r['DepositModels']}\n"
            f"Potential: {r['EconomicPotential']}\n"
            f"Follow-up: {r['FollowUp']}\n"
            f"Note: {r['GeologicalNote']}"
        )

        border = "#f59e0b" if str(r["EconomicPotential"]).lower() in ["moderate", "high"] else "#cbd5e1"
        bg = "#fffbeb" if str(r["EconomicPotential"]).lower() in ["moderate", "high"] else "#f8fafc"

        ax_marks.text(
            0.01, mid,
            textwrap.fill(note, 75),
            ha="left",
            va="center",
            fontsize=5.9,
            linespacing=1.25,
            bbox=dict(facecolor=bg, edgecolor=border, boxstyle="square,pad=0.45", lw=0.9),
        )

    ax_rqd.plot(df["RQD_%"], df["Mid"], color="#0b2545", lw=1.4, marker="o", markersize=3)

    ax_side.axis("off")
    ax_side.set_title("SUMMARY & LEGEND", fontsize=9, fontweight="bold", pad=10)

    lith_sum = summarize_lithology(df)

    inset = ax_side.inset_axes([0.05, 0.72, 0.48, 0.23])
    wedges, _ = inset.pie(
        lith_sum["Thickness"],
        colors=lith_sum["Color"],
        startangle=90,
        wedgeprops=dict(width=0.38, edgecolor="white"),
    )
    for w, h in zip(wedges, lith_sum["Hatch"]):
        w.set_hatch(h)
    inset.text(0, 0, f"{total_depth:.1f} m\nTotal", ha="center", va="center", fontsize=7, fontweight="bold")
    inset.set_aspect("equal")

    y = 0.92
    ax_side.text(0.56, y, "TOTAL LITHOLOGY", fontsize=7, fontweight="bold", transform=ax_side.transAxes)
    y -= 0.035

    for _, rr in lith_sum.iterrows():
        ax_side.add_patch(
            patches.Rectangle(
                (0.56, y - 0.012), 0.035, 0.018,
                facecolor=rr["Color"],
                hatch=rr["Hatch"],
                edgecolor="#333",
                transform=ax_side.transAxes,
            )
        )
        ax_side.text(0.60, y, f"{rr['Lithology']} ({rr['LithCode']})", fontsize=6, transform=ax_side.transAxes, va="center")
        ax_side.text(0.98, y, f"{rr['Percent']:.1f}%", fontsize=6, transform=ax_side.transAxes, ha="right", va="center")
        y -= 0.031

    y = 0.61
    ax_side.text(0.05, y, "USED LITHOLOGY CODES", fontsize=7, fontweight="bold", transform=ax_side.transAxes)
    y -= 0.034

    for code in df["LithCode"].unique():
        name, color, hatch = LITHOLOGY_STYLE.get(code, LITHOLOGY_STYLE["UNK"])
        ax_side.add_patch(
            patches.Rectangle(
                (0.06, y - 0.012), 0.035, 0.018,
                facecolor=color,
                hatch=hatch,
                edgecolor="#333",
                transform=ax_side.transAxes,
            )
        )
        ax_side.text(0.105, y, f"{code}  {name}", fontsize=6, transform=ax_side.transAxes, va="center")
        y -= 0.028

    y -= 0.02
    ax_side.text(0.05, y, "IMPORTANT WARNING", fontsize=7, fontweight="bold", transform=ax_side.transAxes)
    y -= 0.035
    warning = (
        "AI interpretation is visual and preliminary. "
        "Final logging requires geologist review, scale-controlled RQD, assays, petrography, QA/QC and field context."
    )
    ax_side.text(0.05, y, textwrap.fill(warning, 42), fontsize=6.2, transform=ax_side.transAxes, va="top")

    fig.text(
        0.06,
        0.025,
        "Note: RQD shown here is a visual estimate from image analysis. True RQD must be calculated from measured core pieces >10 cm over the run length.",
        fontsize=7,
        style="italic",
        color="#555",
    )

    return fig

# ===================== UI =====================

st.markdown(
    """
    <div style="background:linear-gradient(135deg,#0b1d3a,#1d4ed8);padding:22px;border-radius:16px;color:white;">
    <h1 style="margin:0;">⛏️ CoreLog-AI Vision Logger</h1>
    <p style="margin:6px 0 0 0;">AI-assisted geological core/chip image interpretation + master log figure.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1, 2.8])

with left:
    st.subheader("Project")
    project = st.text_input("Project", "SAHA-01")
    location = st.text_input("Location", "Central Zone")
    hole_id = st.text_input("Hole ID", "DDH-2026-004")
    azdip = st.text_input("Azimuth / Dip", "045° / -60°")
    date_txt = st.text_input("Date", "16 May 2025")

    st.subheader("Geological context")
    ore_context = st.selectbox("Exploration / deposit context", ORE_SYSTEMS)

    uploaded_files = st.file_uploader(
        "Upload drill core / chip tray images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

intervals = []

if uploaded_files:
    with left:
        st.subheader("Depth intervals")
        for i, f in enumerate(uploaded_files):
            st.image(f, caption=f.name, width=180)
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"From #{i+1}", value=float(i * 10), step=1.0, key=f"from_{i}")
            d_to = c2.number_input(f"To #{i+1}", value=float((i + 1) * 10), step=1.0, key=f"to_{i}")

            intervals.append({
                "file_name": f.name,
                "file_bytes": f.getvalue(),
                "from": d_from,
                "to": d_to,
            })

    with right:
        st.subheader("Run AI visual geological logging")

        if st.button("🚀 Analyze images with AI and build log table", type="primary", use_container_width=True):
            ai_results = []

            progress = st.progress(0)
            for idx, item in enumerate(intervals):
                with st.spinner(f"Analyzing {item['file_name']}..."):
                    result = analyze_core_image_with_ai(
                        item["file_bytes"],
                        item["from"],
                        item["to"],
                        ore_context,
                    )
                    ai_results.append(result)
                progress.progress((idx + 1) / len(intervals))

            df = build_rows_from_ai_results(ai_results)
            st.session_state["corelog_df"] = df

        if "corelog_df" in st.session_state:
            st.subheader("Editable AI logging table")
            df = st.session_state["corelog_df"]

            editable_cols = [
                "From", "To", "LithCode", "Lithology", "SecondaryLithology",
                "Texture", "Colour", "Alteration", "AlterationIntensity",
                "Structures", "FaultShear", "FractureIntensity",
                "RQD_%", "RQD_Confidence", "TCR_%",
                "Sulfide_%", "VisibleSulfides", "VisibleOxides",
                "IndicatorMinerals", "DepositModels", "EconomicPotential",
                "FollowUp", "GeologicalNote", "Confidence"
            ]

            edited = st.data_editor(
                df[editable_cols],
                use_container_width=True,
                num_rows="dynamic",
                height=420,
            )

            for i in edited.index:
                code = normalize_code(edited.at[i, "LithCode"])
                edited.at[i, "LithCode"] = code
                name, color, hatch = LITHOLOGY_STYLE[code]
                edited.at[i, "Color"] = color
                edited.at[i, "Hatch"] = hatch
                edited.at[i, "AltColor"] = alteration_color(str(edited.at[i, "Alteration"]).split(","))
                edited.at[i, "Thickness"] = float(edited.at[i, "To"]) - float(edited.at[i, "From"])
                edited.at[i, "Mid"] = (float(edited.at[i, "To"]) + float(edited.at[i, "From"])) / 2
                edited.at[i, "SulfideConfidence"] = "visual estimate"

            if st.button("📊 Generate master log figure", use_container_width=True):
                fig = make_master_log(edited, project, location, hole_id, azdip, date_txt)
                st.pyplot(fig)

                png = io.BytesIO()
                fig.savefig(png, format="png", dpi=300, bbox_inches="tight")

                st.download_button(
                    "Download PNG",
                    data=png.getvalue(),
                    file_name=f"{hole_id}_ai_master_log.png",
                    mime="image/png",
                    use_container_width=True,
                )

                csv = edited.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download CSV",
                    data=csv,
                    file_name=f"{hole_id}_ai_logging_table.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

else:
    with right:
        st.info("Karot fotoğraflarını yükle, her fotoğraf için From-To metraj gir, sonra AI analizini çalıştır.")

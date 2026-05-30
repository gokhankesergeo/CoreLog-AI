import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import io, json, re, textwrap

try:
    from google import genai
except Exception:
    genai = None

st.set_page_config(
    page_title="CoreLog-AI | Professional Suite",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ CoreLog-AI | Geological Master Log Engine")
st.caption("Raporlama Standartlarında, Yüksek Çözünürlüklü ve Sürekli Eksenli Profesyonel Loglama Modülü")

# ============================================================
# GEOLOGY DATABASE & STYLING
# ============================================================
LITHOLOGY_STYLE = {
    "Granite": ("GRN", "Granit", "#f7b7b7", "."),
    "Granodiorite": ("GDR", "Granodiyorit", "#e59a9a", "."),
    "Diorite": ("DIO", "Diyorit", "#8d99ae", "o"),
    "Andesite": ("AND", "Andezit", "#a9b4dc", "."),
    "Dacite": ("DAC", "Dasit", "#c9b6e4", "o"),
    "Rhyolite": ("RHY", "Riyolit", "#f7c6d9", "+"),
    "Basalt": ("BAS", "Bazalt", "#586f52", "x"),
    "Tuff": ("TFF", "Tüf", "#ead7a5", "."),
    "Volcanic Breccia": ("VBX", "Volkanik Breş", "#b98665", "xx"),
    "Sandstone": ("SST", "Kumtaşı", "#efd08a", "-"),
    "Siltstone": ("SLT", "Silttaşı", "#c8a86d", "-"),
    "Mudstone": ("MST", "Çamurtaşı", "#7b7b7b", "-"),
    "Shale": ("SHL", "Şeyl", "#565656", "-"),
    "Coal": ("COL", "Kömür", "#1f1f1f", ""),
    "Limestone": ("LST", "Kireçtaşı", "#a8dadc", "+"),
    "Dolomite": ("DOL", "Dolomit", "#b7e4c7", "+"),
    "Marble": ("MRB", "Mermer", "#d8f3dc", "/"),
    "Schist": ("SCH", "Şist", "#90a955", "/"),
    "Gneiss": ("GNS", "Gnays", "#adb5bd", "x"),
    "Quartzite": ("QZT", "Kuvarsit", "#f8f9fa", "/"),
    "Serpentinite": ("SRP", "Serpantinit", "#588157", "x"),
    "Quartz Vein Zone": ("QVZ", "Kuvars Damar Zonu", "#ffffff", "///"),
    "Shear Zone": ("SHZ", "Makaslama Zonu", "#c1121f", "/"),
    "Fault Breccia": ("FBX", "Fay Breşi", "#bc4749", "xx"),
    "Unknown": ("UNK", "Belirsiz", "#e5e5e5", ""),
}

ALTERATION_STYLE = {
    "None": ("#f8f9fa", ""),
    "Silicification": ("#dbeafe", "///"),
    "Sericite": ("#fff3b0", "\\"),
    "Argillic Clay": ("#ddc1a1", "."),
    "Advanced Argillic": ("#f4a261", "x"),
    "Chlorite-Epidote": ("#74c69d", "-"),
    "Carbonate": ("#caf0f8", "+"),
    "Potassic": ("#ffb4a2", "."),
    "Propylitic": ("#b7e4c7", "\\"),
    "Unknown": ("#e5e5e5", ""),
}

ORE_MODELS = ["Orogenic Gold", "LS Epithermal Au-Ag", "HS Epithermal Au-Cu", "Porphyry Cu-Au-Mo", "Skarn Cu-Fe-Zn-W", "VMS Cu-Zn-Pb-Au-Ag", "Unknown"]

# ============================================================
# PARSING & DATA HELPERS
# ============================================================
def safe_float(v, default=0.0):
    try:
        if isinstance(v, (int, float)): return float(v)
        nums = re.findall(r"-?\d+\.?\d*", str(v))
        return float(nums[0]) if nums else float(default)
    except: return float(default)

def extract_json(text):
    try:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(m.group(0)) if m else None
    except: return None

def resize_image(file, max_size=800):
    file.seek(0)
    img = Image.open(file).convert("RGB")
    img.thumbnail((max_size, max_size))
    return img

def summarize_data(df, col):
    s = df.groupby(col)["Thickness"].sum().reset_index()
    return s.sort_values("Thickness", ascending=False)

def normalize_ai_row(row, from_m, to_m, filename):
    lith = row.get("lithology", "Unknown")
    if lith not in LITHOLOGY_STYLE: lith = "Unknown"
    alt = row.get("alteration", "Unknown")
    if alt not in ALTERATION_STYLE: alt = "Unknown"
    
    code, tr, color, hatch = LITHOLOGY_STYLE.get(lith, LITHOLOGY_STYLE["Unknown"])
    alt_color, alt_hatch = ALTERATION_STYLE.get(alt, ALTERATION_STYLE["Unknown"])

    return {
        "File": filename, "From": from_m, "To": to_m, "Mid": (from_m + to_m) / 2, "Thickness": to_m - from_m,
        "Lithology": lith, "Code": code, "Lithology TR": tr, "Lith Color": color, "Lith Hatch": hatch,
        "Alteration": alt, "Alt Color": alt_color, "Alt Hatch": alt_hatch,
        "Py": safe_float(row.get("pyrite_pct"), 0), "Cpy": safe_float(row.get("chalcopyrite_pct"), 0),
        "Apy": safe_float(row.get("arsenopyrite_pct"), 0), "Gn": safe_float(row.get("galena_pct"), 0),
        "Sp": safe_float(row.get("sphalerite_pct"), 0), "Mag": safe_float(row.get("magnetite_pct"), 0),
        "RQD": max(0, min(100, safe_float(row.get("rqd_pct"), 50))), "TCR": max(0, min(100, safe_float(row.get("tcr_pct"), 80))),
        "Structure": row.get("structure", "Fracture"), "Ore Model": row.get("ore_model", "Unknown"),
        "Confidence": row.get("confidence", "Medium"), "Jeolog_Notu": "Gözlem notlarınızı buraya ekleyebilirsiniz.",
        "Determination": row.get("determination", "AI geological core log interpretation.")
    }

def ai_analyze_image(api_key, file, from_m, to_m):
    if genai is None: raise Exception("google-genai eksik!")
    client = genai.Client(api_key=api_key)
    img = resize_image(file, 800)

    prompt = f"""
    You are a senior exploration geologist. Analyze this core interval {from_m}-{to_m} m.
    Return ONLY valid JSON.
    Allowed Lithology: {list(LITHOLOGY_STYLE.keys())}
    Allowed Alteration: {list(ALTERATION_STYLE.keys())}
    Allowed Ore Model: {ORE_MODELS}

    JSON Schema:
    {{
      "lithology": "Andesite",
      "alteration": "Silicification",
      "pyrite_pct": 1.5,
      "chalcopyrite_pct": 0.3,
      "arsenopyrite_pct": 0.0,
      "galena_pct": 0.0,
      "sphalerite_pct": 0.0,
      "magnetite_pct": 0.5,
      "rqd_pct": 70,
      "tcr_pct": 95,
      "structure": "Intense fracturing with quartz-carbonate veining",
      "ore_model": "Porphyry Cu-Au-Mo",
      "confidence": "Medium",
      "determination": "Hydrothermally altered porphyritic rock with disseminated sulfides."
    }}
    """
    response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=[prompt, img])
    data = extract_json(response.text)
    if not data: raise Exception("JSON Okunamadı.")
    return normalize_ai_row(data, from_m, to_m, file.name)

def draw_structural_symbol(ax, y, kind):
    x0, x1 = 0.15, 0.85
    k = str(kind).lower()
    if "fault" in k or "fay" in k:
        ax.plot([x0, x1], [y + 0.2, y - 0.2], color="#dc2626", lw=1.8, label="Fault" if "Fault" not in ax.get_legend_handles_labels()[1] else "")
    elif "vein" in k or "damar" in k:
        ax.plot([x0, x1], [y + 0.15, y - 0.15], color="#ea580c", lw=1.5, label="Vein" if "Vein" not in ax.get_legend_handles_labels()[1] else "")
    else:
        ax.plot([x0, x1], [y + 0.1, y - 0.1], color="#475569", lw=0.9)

# ============================================================
# MASTER ENGINE (JEOLOJİK STANDARTLARA UYGUN YENİ NESİL PAFTA)
# ============================================================
def create_master_page_log(df_page, page_idx, start_m, end_m, hole_id, project, location, az_dip):
    # Geniş ve okunaklı endüstriyel pafta boyutu
    fig = plt.figure(figsize=(26, 14), dpi=220)
    
    gs = fig.add_gridspec(
        2, 10,
        height_ratios=[1.6, 8.4],
        width_ratios=[0.4, 0.8, 0.4, 1.2, 1.0, 0.9, 0.8, 0.7, 1.1, 2.7],
        wspace=0.10, hspace=0.12
    )

    fig.suptitle(f"AI-ASSISTED GEOLOGICAL MASTER LOG | HOLE ID: {hole_id} (PAGE: {page_idx+1})", fontsize=20, fontweight="bold", color="#0f2742", y=0.98)

    # Upper Panel - Metadata
    ax_meta = fig.add_subplot(gs[0, 0:3])
    ax_meta.axis("off")
    ax_meta.text(0, 0.95, f"PROJECT: {project}\nLOCATION: {location}\nAZIMUTH / DIP: {az_dip}\nINTERVAL: {start_m:.1f} - {end_m:.1f} m", va="top", fontsize=11, fontweight="bold", color="#1e293b", linespacing=1.4)

    # Upper Panel - Donut Summary 1
    ax_lith_donut = fig.add_subplot(gs[0, 3:5])
    lith_sum = summarize_data(df_page, "Lithology")
    colors, hatches = [], []
    for lith in lith_sum["Lithology"]:
        _, _, c, h = LITHOLOGY_STYLE.get(lith, LITHOLOGY_STYLE["Unknown"])
        colors.append(c)
        hatches.append(h)
    wedges, _ = ax_lith_donut.pie(lith_sum["Thickness"], colors=colors, startangle=90, wedgeprops={"width": 0.4, "edgecolor": "#0f2742", "linewidth": 0.7})
    for w, h in zip(wedges, hatches): w.set_hatch(h)
    ax_lith_donut.set_title("LITHOLOGY COMPOSITION", fontsize=10, fontweight="bold", color="#0f2742")

    # Upper Panel - Donut Summary 2
    ax_ore_donut = fig.add_subplot(gs[0, 5:7])
    ore_sum = summarize_data(df_page, "Ore Model")
    ore_colors = plt.cm.Pastel1(np.linspace(0, 1, len(ore_sum)))
    ax_ore_donut.pie(ore_sum["Thickness"], colors=ore_colors, startangle=90, wedgeprops={"width": 0.4, "edgecolor": "white"})
    ax_ore_donut.set_title("PROPOSED ORE SYSTEMS", fontsize=10, fontweight="bold", color="#0f2742")

    # Upper Panel - Active Legend
    ax_legend = fig.add_subplot(gs[0, 7:10])
    ax_legend.axis("off")
    ax_legend.text(0.0, 0.95, "ACTIVE PAGE LEGEND", fontsize=11, fontweight="bold", color="#0f2742", va="top")
    used_liths = list(df_page["Lithology"].unique())
    for i, lith in enumerate(used_liths[:5]):
        code, tr, color, hatch = LITHOLOGY_STYLE.get(lith, LITHOLOGY_STYLE["Unknown"])
        ax_legend.add_patch(patches.Rectangle((0.0, 0.65 - i * 0.16), 0.04, 0.10, facecolor=color, edgecolor="black", hatch=hatch))
        ax_legend.text(0.05, 0.70 - i * 0.16, f"[{code}] {tr} ({lith})", fontsize=9, va="center")

    # Core Axes Setup
    ax_depth  = fig.add_subplot(gs[1, 0])
    ax_lith   = fig.add_subplot(gs[1, 1], sharey=ax_depth)
    ax_code   = fig.add_subplot(gs[1, 2], sharey=ax_depth)
    ax_desc   = fig.add_subplot(gs[1, 3], sharey=ax_depth)
    ax_alt    = fig.add_subplot(gs[1, 4], sharey=ax_depth)
    ax_sulf   = fig.add_subplot(gs[1, 5], sharey=ax_depth)
    ax_rqd    = fig.add_subplot(gs[1, 6], sharey=ax_depth)
    ax_struct = fig.add_subplot(gs[1, 7], sharey=ax_depth)
    ax_model  = fig.add_subplot(gs[1, 8], sharey=ax_depth)
    ax_note   = fig.add_subplot(gs[1, 9], sharey=ax_depth)

    axes = [ax_depth, ax_lith, ax_code, ax_desc, ax_alt, ax_sulf, ax_rqd, ax_struct, ax_model, ax_note]
    for ax in axes:
        ax.set_ylim(end_m, start_m) # Jeolojik yönelim: Yukarısı sıfır metre, aşağısı derinlik
        ax.set_yticks(np.arange(start_m, end_m + 5, 5))
        ax.tick_params(axis='y', labelsize=9)
        ax.grid(axis="y", linestyle="-", color="#cbd5e1", alpha=0.5)

    # Column Titles
    titles = [
        (ax_depth, "DEPTH\n(m)"), (ax_lith, "STRATIGRAPHY\nGraphic Log"), (ax_code, "ROCK\nCode"),
        (ax_desc, "GEOLOGICAL\nDescription"), (ax_alt, "ALTERATION\nDominant"), (ax_sulf, "SULFIDES\nVisual %"),
        (ax_rqd, "GEOTECHNICAL\nRQD / TCR %"), (ax_struct, "STRUCTURAL\nFeatures"), (ax_model, "GENETIC MODEL\nInterpretation"),
        (ax_note, "FIELD DETERMINATION & REMARKS FOR REPORT")
    ]
    for ax, title in titles:
        ax.set_title(title, fontsize=10, fontweight="bold", color="#0f2742", pad=12)

    # Set Axes Limits and Behaviors
    ax_depth.set_xlim(0, 1); ax_depth.set_xticks([])
    for y in np.arange(start_m, end_m + 1, 1):
        ax_depth.plot([0.3, 0.7], [y, y], color="#475569", lw=0.6)

    ax_lith.set_xlim(0, 1); ax_lith.set_xticks([])
    ax_code.set_xlim(0, 1); ax_code.set_xticks([])
    ax_desc.set_xlim(0, 1); ax_desc.axis("off")
    ax_alt.set_xlim(0, 1); ax_alt.set_xticks([])
    ax_sulf.set_xlim(0, 10); ax_sulf.set_facecolor("#f8fafc")
    ax_rqd.set_xlim(0, 100); ax_rqd.set_facecolor("#f1f5f9")
    ax_struct.set_xlim(0, 1); ax_struct.set_xticks([])
    ax_model.set_xlim(0, 1); ax_model.axis("off")
    ax_note.set_xlim(0, 1); ax_note.axis("off")

    model_colors = plt.cm.tab20(np.linspace(0, 1, len(ORE_MODELS)))
    model_map = {m: model_colors[i] for i, m in enumerate(ORE_MODELS)}

    # Plot Geotechnical Trends (Sürekli Çizgi Grafiği - Gerçek Jeolojik Akış!)
    # Derinliğin başlangıç ve bitiş sınırlarını trende ekleyerek havada asılı kalmasını engelliyoruz
    rqd_points_x, rqd_points_y = [], []
    tcr_points_x, tcr_points_y = [], []
    
    for _, r in df_page.iterrows():
        rqd_points_x.extend([r["RQD"], r["RQD"]])
        rqd_points_y.extend([r["From"], r["To"]])
        tcr_points_x.extend([r["TCR"], r["TCR"]])
        tcr_points_y.extend([r["From"], r["To"]])

    ax_rqd.plot(rqd_points_x, rqd_points_y, color="#1e3a8a", lw=2.2, label="RQD", zorder=3)
    ax_rqd.plot(tcr_points_x, tcr_points_y, color="#b91c1c", lw=1.5, ls="--", label="TCR", zorder=3)

    # Plot Core Interval Data
    for _, r in df_page.iterrows():
        y_top, y_bot = max(start_m, r["From"]), min(end_m, r["To"])
        h = y_bot - y_top
        y_mid = (y_top + y_bot) / 2
        if h <= 0: continue

        # Lithology & Rock Code
        ax_lith.add_patch(patches.Rectangle((0, y_top), 1, h, facecolor=r["Lith Color"], edgecolor="#0f2742", linewidth=0.9, hatch=r["Lith Hatch"]))
        ax_code.text(0.5, y_mid, r["Code"], ha="center", va="center", fontsize=9, fontweight="bold", bbox=dict(facecolor="white", edgecolor="#94a3b8", boxstyle="round,pad=0.25"))

        # Description Column
        desc_text = f"• {r['Lithology TR']}\n({r['Lithology']})\nConfidence: {r['Confidence']}"
        ax_desc.text(0.05, y_mid, textwrap.fill(desc_text, 24), ha="left", va="center", fontsize=8.5, fontweight="500")

        # Alteration Column
        ax_alt.add_patch(patches.Rectangle((0, y_top), 1, h, facecolor=r["Alt Color"], edgecolor="#0f2742", linewidth=0.8, hatch=r["Alt Hatch"]))
        ax_alt.text(0.5, y_mid, textwrap.fill(r["Alteration"], 14), ha="center", va="center", fontsize=8, fontweight="bold", color="#0f2742")

        # Sulfide Area/Bars
        py, cpy, apy, mag = r["Py"], r["Cpy"], r.get("Apy", 0), r["Mag"]
        ax_sulf.barh(y_mid, py, height=h*0.4, color="#f59e0b", edgecolor="#b45309", alpha=0.9)
        ax_sulf.barh(y_mid, cpy, left=py, height=h*0.4, color="#ea580c", edgecolor="#9a3412", alpha=0.9)
        ax_sulf.barh(y_mid, apy, left=py+cpy, height=h*0.4, color="#64748b", edgecolor="#334155", alpha=0.9)
        ax_sulf.barh(y_mid, mag, left=py+cpy+apy, height=h*0.4, color="#1e293b", edgecolor="black", alpha=0.9)

        # Structure Symbols
        draw_structural_symbol(ax_struct, y_mid, r["Structure"])

        # Genetic Ore Model
        ax_model.add_patch(patches.Rectangle((0, y_top), 1, h, facecolor=model_map.get(r["Ore Model"], "#f1f5f9"), edgecolor="#cbd5e1", alpha=0.9))
        ax_model.text(0.5, y_mid, textwrap.fill(r["Ore Model"], 14), ha="center", va="center", fontsize=8, fontweight="bold")

        # Clean, Formal Reporting Remarks Column (No ugly bounding boxes!)
        report_note = (
            f"▶ INTERVAL: {r['From']:.1f} - {r['To']:.1f} m\n"
            f"  [STRUCTURE]: {r['Structure']}\n"
            f"  [SAHA JEOLOGU NOTU]: {r['Jeolog_Notu']}\n"
            f"  [TECHNICAL DETERMINATION]: {r['Determination']}"
        )
        ax_note.text(0.02, y_mid, textwrap.fill(report_note, 88), ha="left", va="center", fontsize=8.2, linespacing=1.3, color="#1e293b")
        ax_note.plot([0, 1], [y_bot, y_bot], color="#e2e8f0", lw=0.8)

    # Finalize Legends
    ax_rqd.legend(loc="upper right", fontsize=8, framealpha=0.9)
    
    # Custom handles for sulfide legend
    sulf_patches = [
        patches.Patch(color="#f59e0b", label="Py"),
        patches.Patch(color="#ea580c", label="Cpy"),
        patches.Patch(color="#64748b", label="Apy"),
        patches.Patch(color="#1e293b", label="Mag")
    ]
    ax_sulf.legend(handles=sulf_patches, loc="upper right", fontsize=8)

    fig.subplots_adjust(top=0.90, bottom=0.04, left=0.03, right=0.97, wspace=0.08)
    return fig

# ============================================================
# STREAMLIT INTERFACE
# ============================================================
left, right = st.columns([1.1, 3.5])

with left:
    st.header("⚙️ Proje Ayarları")
    hole_id = st.text_input("Hole ID", "DDH-2026-004")
    project = st.text_input("Project", "SAHA-01")
    location = st.text_input("Location", "Central Zone")
    az_dip = st.text_input("Azimuth / Dip", "045° / -60°")
    page_step = st.selectbox("Sayfa Başına Metraj Limiti", [25, 50, 100], index=0)

    api_key = st.text_input("Gemini API Key", type="password")
    uploaded_files = st.file_uploader("Karot Segment Fotoğrafları", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    intervals = []
    if uploaded_files:
        st.info(f"{len(uploaded_files)} görsel sisteme yüklendi.")
        for i, f in enumerate(uploaded_files):
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"Başlangıç #{i+1}", value=float(i * 10), step=1.0, key=f"from_{i}")
            d_to = c2.number_input(f"Bitiş #{i+1}", value=float((i + 1) * 10), step=1.0, key=f"to_{i}")
            intervals.append((f, d_from, d_to))

    run = st.button("🚀 Loglama Motorunu Çalıştır", use_container_width=True)

if run:
    if not uploaded_files or not api_key:
        st.error("Lütfen karot fotoğraflarını ve geçerli bir API anahtarını girin.")
        st.stop()

    rows = []
    with st.spinner("AI Karot Örneklerini Jeolojik Olarak Sınıflandırıyor..."):
        for f, d_from, d_to in intervals:
            try:
                row = ai_analyze_image(api_key, f, d_from, d_to)
                rows.append(row)
            except Exception as e:
                st.error(f"{f.name} işlem hatası: {e}")

    if rows:
        st.session_state["reporting_df"] = pd.DataFrame(rows).sort_values("From").reset_index(drop=True)

if "reporting_df" in st.session_state:
    df = st.session_state["reporting_df"]
    
    with right:
        st.subheader("📝 Jeolog Revizyon ve Veri Giriş Ekranı")
        df_edited = st.data_editor(
            df[["From", "To", "Lithology", "Alteration", "Py", "Cpy", "Apy", "Mag", "RQD", "TCR", "Structure", "Ore Model", "Jeolog_Notu"]],
            use_container_width=True
        )

        # Sync manual changes
        for col in df_edited.columns: df[col] = df_edited[col]
        for idx, row in df.iterrows():
            _, _, col, h = LITHOLOGY_STYLE.get(row["Lithology"], LITHOLOGY_STYLE["Unknown"])
            df.at[idx, "Lith Color"] = col
            df.at[idx, "Lith Hatch"] = h

        total_min_m = float(df["From"].min())
        total_max_m = float(df["To"].max())
        
        page_bounds = []
        curr_m = total_min_m
        while curr_m < total_max_m:
            next_m = min(curr_m + page_step, total_max_m)
            page_bounds.append((curr_m, next_m))
            curr_m = next_m

        st.subheader("📊 Profesyonel Çıktı Paftaları")
        for idx, (p_start, p_end) in enumerate(page_bounds):
            df_page = df[(df["To"] > p_start) & (df["From"] < p_end)]
            if not df_page.empty:
                with st.expander(f"📄 PAFTA SAYFA {idx+1} ({p_start:.1f}m - {p_end:.1f}m)", expanded=True):
                    fig = create_master_page_log(df_page, idx, p_start, p_end, hole_id, project, location, az_dip)
                    st.pyplot(fig)

                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", dpi=240, bbox_inches="tight")
                    buf.seek(0)
                    st.download_button(f"📥 Sayfa {idx+1} Profesyonel Paftayı İndir (PNG)", data=buf, file_name=f"{hole_id}_MasterLog_Page_{idx+1}.png", mime="image/png", use_container_width=True)

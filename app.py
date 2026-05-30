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
    page_title="CoreLog-AI Master Suite",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ CoreLog-AI | Geological Master Log Engine")
st.caption("İlk Pafta Estetiğinde, Genişletilmiş Mineraloji ve Sayfalanabilir Büyük Sondaj Modülü")

# ============================================================
# GEOLOGY DATABASE (Orijinal Renkler ve Gelişmiş Tarama)
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

MINERAL_COLORS = {
    "Py": "#f9dc5c", "Cpy": "#e67e22", "Apy": "#94a3b8", 
    "Gn": "#7b8794", "Sp": "#a3b18a", "Mag": "#111827"
}

ORE_MODELS = ["Orogenic Gold", "LS Epithermal Au-Ag", "HS Epithermal Au-Cu", "Porphyry Cu-Au-Mo", "Skarn Cu-Fe-Zn-W", "VMS Cu-Zn-Pb-Au-Ag", "Unknown"]

# ============================================================
# HELPERS
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

def resize_image(file, max_size=1000):
    file.seek(0)
    img = Image.open(file).convert("RGB")
    img.thumbnail((max_size, max_size))
    return img

def summarize_page(df, col):
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
        "Confidence": row.get("confidence", "Medium"),
        "Jeolog_Notu": "Gözlemlerinizi buraya yazabilirsiniz.",
        "Determination": row.get("determination", "AI geological interpretation.")
    }

def ai_analyze_image(api_key, file, from_m, to_m):
    if genai is None: raise Exception("google-genai eksik!")
    client = genai.Client(api_key=api_key)
    img = resize_image(file, 1000)

    prompt = f"""
    You are a senior exploration geologist. Analyze this core/outcrop photo for interval {from_m}-{to_m} m.
    Return ONLY valid JSON.
    Allowed Lithology: {list(LITHOLOGY_STYLE.keys())}
    Allowed Alteration: {list(ALTERATION_STYLE.keys())}
    Allowed Ore Model: {ORE_MODELS}

    JSON Schema:
    {{
      "lithology": "Andesite",
      "alteration": "Silicification",
      "pyrite_pct": 1.0,
      "chalcopyrite_pct": 0.2,
      "arsenopyrite_pct": 0.0,
      "galena_pct": 0.0,
      "sphalerite_pct": 0.0,
      "magnetite_pct": 0.0,
      "rqd_pct": 65,
      "tcr_pct": 90,
      "structure": "Fractured",
      "ore_model": "Porphyry Cu-Au-Mo",
      "confidence": "Medium",
      "determination": "Technical description."
    }}
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt, img])
    data = extract_json(response.text)
    if not data: raise Exception("JSON Çözümlenemedi.")
    return normalize_ai_row(data, from_m, to_m, file.name)

def draw_structural_symbol(ax, y, kind):
    x0, x1 = 0.2, 0.8
    k = str(kind).lower()
    if "fault" in k or "fay" in k:
        ax.plot([x0, x1], [y + 0.3, y - 0.3], color="black", lw=1.2)
        ax.plot([0.48, 0.56], [y + 0.1, y - 0.1], color="red", lw=1.2)
    elif "vein" in k or "damar" in k:
        ax.plot([x0, x1], [y + 0.25, y - 0.25], color="red", lw=1.2)
    else:
        ax.plot([x0, x1], [y + 0.2, y - 0.2], color="black", lw=0.8)

# ============================================================
# ORIGINAL PAFTA DESIGN ENGINE (İlk Beğenilen Estetik Düzen)
# ============================================================
def create_master_page_log(df_page, page_idx, start_m, end_m, hole_id, project, location, az_dip):
    total_depth_page = end_m - start_m
    
    # Orijinal ilk görselin geniş inç oranları ve yüksek DPI kalitesi
    fig = plt.figure(figsize=(25, 14), dpi=220)
    
    gs = fig.add_gridspec(
        2, 10,
        height_ratios=[1.8, 8.2],
        width_ratios=[0.42, 0.95, 0.42, 1.15, 1.05, 0.85, 0.72, 0.75, 1.2, 2.8],
        wspace=0.12, hspace=0.14
    )

    fig.suptitle(f"AI-ASSISTED GEOLOGICAL MASTER LOG | HOLE ID: {hole_id} (PAFTA SAYFA: {page_idx+1})", fontsize=20, fontweight="bold", color="#0f2742", y=0.99)

    # 1. METADATA ALANI (Orijinal Sol Üst)
    ax_meta = fig.add_subplot(gs[0, 0:3])
    ax_meta.axis("off")
    ax_meta.text(0, 0.95, f"PROJECT: {project}\nLOCATION: {location}\nAZIMUTH / DIP: {az_dip}\nINTERVAL: {start_m:.1f} - {end_m:.1f} m", va="top", fontsize=11, fontweight="bold", color="#0f2742")

    # 2. LITHOLOGY DONUT (Orijinal Üst Orta)
    ax_lith_donut = fig.add_subplot(gs[0, 3:5])
    lith_sum = summarize_page(df_page, "Lithology")
    colors, hatches = [], []
    for lith in lith_sum["Lithology"]:
        _, _, c, h = LITHOLOGY_STYLE.get(lith, LITHOLOGY_STYLE["Unknown"])
        colors.append(c)
        hatches.append(h)
    wedges, _ = ax_lith_donut.pie(lith_sum["Thickness"], colors=colors, startangle=90, wedgeprops={"width": 0.42, "edgecolor": "#0f2742", "linewidth": 0.8})
    for w, h in zip(wedges, hatches): w.set_hatch(h)
    ax_lith_donut.text(0, 0, f"{total_depth_page:.0f} m\nPage", ha="center", va="center", fontsize=9, fontweight="bold")
    ax_lith_donut.set_title("LITHOLOGY SUMMARY", fontsize=10, fontweight="bold", color="#0f2742", pad=8)

    # 3. ORE SYSTEMS DONUT (Orijinal Üst Sağ)
    ax_ore_donut = fig.add_subplot(gs[0, 5:7])
    ore_sum = summarize_page(df_page, "Ore Model")
    ore_colors = plt.cm.Set3(np.linspace(0, 1, len(ore_sum)))
    ax_ore_donut.pie(ore_sum["Thickness"], colors=ore_colors, startangle=90, wedgeprops={"width": 0.42, "edgecolor": "white"})
    ax_ore_donut.text(0, 0, "Ore\nModels", ha="center", va="center", fontsize=9, fontweight="bold")
    ax_ore_donut.set_title("ORE SYSTEMS", fontsize=10, fontweight="bold", color="#0f2742", pad=8)

    # 4. ACTIVE LEGEND (Orijinal Üst En Sağ)
    ax_legend = fig.add_subplot(gs[0, 7:10])
    ax_legend.axis("off")
    ax_legend.text(0.0, 0.95, "ACTIVE LEGEND", fontsize=11, fontweight="bold", color="#0f2742", va="top")
    used_liths = list(df_page["Lithology"].unique())
    for i, lith in enumerate(used_liths[:5]):
        code, tr, color, hatch = LITHOLOGY_STYLE.get(lith, LITHOLOGY_STYLE["Unknown"])
        ax_legend.add_patch(patches.Rectangle((0.0, 0.7 - i * 0.15), 0.05, 0.08, facecolor=color, edgecolor="black", hatch=hatch))
        ax_legend.text(0.07, 0.74 - i * 0.15, f"{code} {tr}", fontsize=8.5, va="center")

    # ANA SÜTUNLARIN KURULUMU (Orijinal Tasarım Düzeni)
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
        ax.set_ylim(end_m, start_m)
        ax.set_yticks(np.arange(start_m, end_m + 5, 5))
        ax.grid(axis="y", linestyle=":", alpha=0.4)

    ax_depth.set_xlim(0, 1); ax_depth.set_xticks([])
    ax_depth.set_ylabel("Depth / Derinlik (m)", fontsize=10, fontweight="bold")
    for y in np.arange(start_m, end_m + 1, 1):
        ax_depth.plot([0.35, 0.65], [y, y], color="black", lw=0.5)

    columns_setup = [
        (ax_depth, "DEPTH\nm"), (ax_lith, "LITHOLOGY\nAI Visual Log"), (ax_code, "ROCK\nCode"),
        (ax_desc, "LITHOLOGY\nDescription"), (ax_alt, "ALTERATION\nAI Dominant"), (ax_sulf, "SULFIDE\nVisual %"),
        (ax_rqd, "RQD / TCR\nEstimate"), (ax_struct, "STRUCTURE\nSymbols"), (ax_model, "ORE MODEL\nAI Reasoning"),
        (ax_note, "TECHNICAL DETERMINATION & GEOLOGIST REMARKS")
    ]
    for ax, title in columns_setup:
        ax.set_title(title, fontsize=10, fontweight="bold", color="#0f2742", pad=10)

    ax_lith.set_xlim(0, 1); ax_lith.set_xticks([])
    ax_code.set_xlim(0, 1); ax_code.set_xticks([])
    ax_desc.set_xlim(0, 1); ax_desc.axis("off")
    ax_alt.set_xlim(0, 1); ax_alt.set_xticks([])
    ax_sulf.set_xlim(0, 15); ax_sulf.set_facecolor("#fffaf0")
    ax_rqd.set_xlim(0, 100)
    ax_struct.set_xlim(0, 1); ax_struct.set_xticks([])
    ax_model.set_xlim(0, 1); ax_model.axis("off")
    ax_note.set_xlim(0, 1); ax_note.axis("off")

    model_colors = plt.cm.tab20(np.linspace(0, 1, len(ORE_MODELS)))
    model_color_map = {m: model_colors[i] for i, m in enumerate(ORE_MODELS)}

    # VERİ ÇİZİM DÖNGÜSÜ
    for _, r in df_page.iterrows():
        y_top = max(start_m, r["From"])
        y_bot = min(end_m, r["To"])
        h = y_bot - y_top
        y_mid = (y_top + y_bot) / 2
        if h <= 0: continue

        # Orijinal Log Çizimi
        ax_lith.add_patch(patches.Rectangle((0, y_top), 1, h, facecolor=r["Lith Color"], edgecolor="#111827", linewidth=0.8, hatch=r["Lith Hatch"]))
        
        ax_code.text(0.5, y_mid, r["Code"], ha="center", va="center", fontsize=8.5, fontweight="bold",
                     bbox=dict(facecolor="white", edgecolor="#cbd5e1", boxstyle="round,pad=0.22"))

        desc_str = f"{r['Lithology TR']}\nAI: {r['Lithology']}\nConf: {r['Confidence']}"
        ax_desc.text(0.05, y_mid, textwrap.fill(desc_str, 22), ha="left", va="center", fontsize=8, fontweight="bold")

        ax_alt.add_patch(patches.Rectangle((0, y_top), 1, h, facecolor=r["Alt Color"], edgecolor="#111827", linewidth=0.7, hatch=r["Alt Hatch"]))
        ax_alt.text(0.5, y_mid, textwrap.fill(r["Alteration"], 13), ha="center", va="center", fontsize=7.5, fontweight="bold")

        # Sülfid Dağılımları (Hatalı Olmayan Çizim)
        py, cpy, apy, gn, sp, mag = r["Py"], r["Cpy"], r.get("Apy", 0), r["Gn"], r["Sp"], r["Mag"]
        ax_sulf.barh(y_mid, py, height=h*0.6, color="#f9dc5c", edgecolor="#b08900", label="Py" if "Py" not in ax_sulf.get_legend_handles_labels()[1] else "")
        ax_sulf.barh(y_mid, cpy, left=py, height=h*0.6, color="#e67e22", edgecolor="#a0522d", label="Cpy" if "Cpy" not in ax_sulf.get_legend_handles_labels()[1] else "")
        ax_sulf.barh(y_mid, apy, left=py+cpy, height=h*0.6, color="#94a3b8", edgecolor="#475569", label="Apy" if "Apy" not in ax_sulf.get_legend_handles_labels()[1] else "")
        ax_sulf.barh(y_mid, mag, left=py+cpy+apy, height=h*0.6, color="#111827", edgecolor="black", label="Mag" if "Mag" not in ax_sulf.get_legend_handles_labels()[1] else "")

        # Yapı sembolü
        draw_structural_symbol(ax_struct, y_mid, r["Structure"])

        # Ore Model
        ax_model.add_patch(patches.Rectangle((0, y_top), 1, h, facecolor=model_color_map.get(r["Ore Model"], "#e5e7eb"), edgecolor="white", alpha=0.85))
        ax_model.text(0.5, y_mid, textwrap.fill(r["Ore Model"], 12), ha="center", va="center", fontsize=7.5, fontweight="bold")

        # Teknik Not Alanı
        total_sulf = py + cpy + apy + gn + sp + mag
        bg_box = "#fff7ed" if total_sulf > 2.0 else "#f8fafc"
        edge_box = "#f97316" if total_sulf > 2.0 else "#cbd5e1"
        
        note_str = (
            f"{r['From']:.1f}-{r['To']:.1f} m | STRUCTURE: {r['Structure']}\n"
            f"JEOLOG SAHA NOTU: {r['Jeolog_Notu']}\n"
            f"AI TECHNICAL NOTE: {r['Determination']}"
        )
        ax_note.text(0.01, y_mid, textwrap.fill(note_str, 90), ha="left", va="center", fontsize=7.2, linespacing=1.2,
                     bbox=dict(facecolor=bg_box, edgecolor=edge_box, boxstyle="square,pad=0.35", linewidth=0.85))

    # RQD & TCR Eğrileri (Hata Veren labelsize Parametresi Kaldırıldı!)
    ax_rqd.plot(df_page["RQD"], df_page["Mid"], color="#0f2742", marker="o", lw=2.0, label="RQD")
    ax_rqd.plot(df_page["TCR"], df_page["Mid"], color="#dc2626", marker="s", lw=1.2, ls="--", label="TCR")
    ax_rqd.legend(loc="upper right", fontsize=7)
    if ax_sulf.get_legend_handles_labels()[1]: ax_sulf.legend(loc="upper right", fontsize=7)

    fig.subplots_adjust(top=0.91, bottom=0.035, left=0.035, right=0.985)
    return fig

# ============================================================
# STREAMLIT UI
# ============================================================
left, right = st.columns([1.05, 3.6])

with left:
    st.header("⚙️ Proje Verileri")
    hole_id = st.text_input("Hole ID", "DDH-2026-004")
    project = st.text_input("Project", "SAHA-01")
    location = st.text_input("Location", "Central Zone")
    az_dip = st.text_input("Azimuth / Dip", "045° / -60°")
    page_step = st.selectbox("Sayfa Başına Metraj Limit Ayarı", [25, 50, 100], index=0)

    api_key = st.text_input("Gemini API Key", type="password")
    uploaded_files = st.file_uploader("Karot Fotoğrafları", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    intervals = []
    if uploaded_files:
        st.success(f"{len(uploaded_files)} görsel algılandı.")
        for i, f in enumerate(uploaded_files):
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"Başlangıç #{i+1}", value=float(i * 10), step=1.0, key=f"from_{i}")
            d_to = c2.number_input(f"Bitiş #{i+1}", value=float((i + 1) * 10), step=1.0, key=f"to_{i}")
            intervals.append((f, d_from, d_to))

    run = st.button("🚀 Loglama Motorunu Çalıştır", use_container_width=True)

if run:
    if not uploaded_files or not api_key:
        st.error("Görsel ve API anahtarı zorunludur.")
        st.stop()

    rows = []
    with st.spinner("Yapay Zeka Karot Piksellerini Analiz Ediyor..."):
        for f, d_from, d_to in intervals:
            try:
                row = ai_analyze_image(api_key, f, d_from, d_to)
                rows.append(row)
            except Exception as e:
                st.error(f"{f.name} hatası: {e}")

    if rows:
        st.session_state["reporting_df"] = pd.DataFrame(rows).sort_values("From").reset_index(drop=True)

if "reporting_df" in st.session_state:
    df = st.session_state["reporting_df"]
    
    with right:
        st.subheader("📝 Jeolog Revizyon Paneli (Notlarınızı Buradan Ekleyin)")
        df_edited = st.data_editor(df[["From", "To", "Lithology", "Alteration", "Py", "Cpy", "Apy", "Mag", "RQD", "TCR", "Structure", "Ore Model", "Jeolog_Notu"]], use_container_width=True)

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

        st.subheader("📊 Rapor Kalitesinde Çıktı Paftaları")
        for idx, (p_start, p_end) in enumerate(page_bounds):
            df_page = df[(df["To"] > p_start) & (df["From"] < p_end)]
            if not df_page.empty:
                with st.expander(f"📄 PAFTA SAYFA {idx+1} ({p_start:.1f}m - {p_end:.1f}m)", expanded=True):
                    fig = create_master_page_log(df_page, idx, p_start, p_end, hole_id, project, location, az_dip)
                    st.pyplot(fig)

                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", dpi=240, bbox_inches="tight")
                    buf.seek(0)
                    st.download_button(f"📥 Sayfa {idx+1} Master Log Görselini İndir", data=buf, file_name=f"{hole_id}_MasterLog_Page_{idx+1}.png", mime="image/png", use_container_width=True)

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
    page_title="CORELOG-AI | AI GEOLOGICAL MASTER LOG",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ CORELOG-AI | AI GEOLOGICAL MASTER LOG")
st.caption("AI-ASSISTED CORE/OUTCROP LOGGING: LITHOLOGY, ALTERATION, MINERALIZATION, RQD, STRUCTURE, ORE-SYSTEM REASONING.")

# ============================================================
# GENİŞLETİLMİŞ JEOLOJİ VE YATAK TİPLERİ KÜTÜPHANESİ
# ============================================================

LITHOLOGY_STYLE = {
    # Mağmatik / İntruzif (Porfiri & Skarn Yatakları İçin)
    "Granite": ("GRN", "GRANİT", "#f7b7b7", "."),
    "Granodiorite": ("GDR", "GRANODİYORİT", "#e59a9a", "."),
    "Diorite": ("DIO", "DİYORİT", "#8d99ae", "o"),
    "Syenite": ("SYE", "SİYENİT", "#fbc4b6", "."),
    "Monzonite": ("MON", "MONZONİT", "#f0a6ca", "+"),
    "Quartz Porphyry": ("QPO", "KUVARS PORFİRİ", "#ffccd5", "o"),

    # Volkanik (Epitemal & VMS Yatakları İçin)
    "Andesite": ("AND", "ANDEZİT", "#a9b4dc", "."),
    "Dacite": ("DAC", "DASİT", "#c9b6e4", "o"),
    "Rhyolite": ("RHY", "RİYOLİT", "#f7c6d9", "+"),
    "Basalt": ("BAS", "BAZALT", "#586f52", "x"),
    "Tuff": ("TFF", "TÜF", "#ead7a5", "-"),
    "Volcanic Breccia": ("VBX", "VOLKANİK BREŞ", "#b98665", "xx"),
    "Agglomerate": ("AGL", "AGLOMERA", "#9c6644", "xx"),

    # Sedanter / Karbonat (MVT, SEDEX & Skarn İçin)
    "Sandstone": ("SST", "KUMTAŞI", "#efd08a", "-"),
    "Siltstone": ("SLT", "SİLTTAŞI", "#c8a86d", "-"),
    "Mudstone": ("MST", "ÇAMURTAŞI", "#7b7b7b", "-"),
    "Shale": ("SHL", "ŞEYL", "#565656", "-"),
    "Limestone": ("LST", "KİREÇTAŞI", "#a8dadc", "+"),
    "Dolomite": ("DOL", "DOLOMİT", "#b7e4c7", "+"),
    "Chert": ("CHT", "ÇERT", "#ffb5a7", "/"),
    "Coal": ("COL", "KÖMÜR", "#1f1f1f", ""),

    # Metamorfik (Orojenik Altın & Endüstriyel Mineraller İçin)
    "Schist": ("SCH", "ŞİST", "#90a955", "/"),
    "Micaschist": ("MSC", "MİKAŞİST", "#8ecae6", "/"),
    "Gneiss": ("GNS", "GNAYS", "#adb5bd", "x"),
    "Quartzite": ("QZT", "KUVARSİT", "#f8f9fa", "/"),
    "Marble": ("MRB", "MERMER", "#d8f3dc", "/"),
    "Amphibolite": ("AMP", "AMFİBOLİT", "#2d6a4f", "."),

    # Ultramafik / Ofiyolitik (Kromit & Nikel İçin)
    "Serpentinite": ("SRP", "SERPANTİNİT", "#588157", "x"),
    "Dunite": ("DUN", "DUNİT", "#6a994e", "o"),
    "Harzburgite": ("HZB", "HARZBURJİT", "#386641", "+"),
    "Pyroxenite": ("PRX", "PİROKSENİT", "#132a13", "x"),

    # Damar / Yapısal / Cevher Zonları
    "Quartz Vein Zone": ("QVZ", "KUVARS DAMAR ZONU", "#ffffff", "///"),
    "Carbonate Vein": ("CBV", "KARBONAT DAMARI", "#e0f2fe", "///"),
    "Shear Zone": ("SHZ", "MAKASLAMA ZONU", "#c1121f", "/"),
    "Fault Breccia": ("FBX", "FAY BREŞİ", "#bc4749", "xx"),
    "Gossan / Iron Oxide": ("GOX", "GOSSAN / DEMİR OKSİT", "#d9480f", "."),
    "Massive Sulphide": ("MSU", "MASİF SÜLFÜR", "#343a40", ""),
    "BIF / Iron Formation": ("BIF", "BANTLI DEMİR FOR.", "#6c757d", "-"),
    "Pegmatite": ("PEG", "PEGMASİT", "#ffe5ec", "+"),
    "Skarn": ("SKN", "SKARN", "#95d5b2", "o"),
    "Unknown": ("UNK", "BELİRSİZ", "#e5e5e5", ""),
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
    "Phyllic": ("#e9d5ff", "///"),
    "Skarn Garnet-Pyroxene": ("#c77dff", "o"),
    "Epidote-Chlorite-Actinolite": ("#52b788", "-"),
    "Iron Oxide / Gossan": ("#e76f51", "."),
    "Serpentinization": ("#80b918", "x"),
    "Unknown": ("#e5e5e5", ""),
}

ORE_MODELS = [
    "Orogenic Gold",
    "LS Epithermal Au-Ag",
    "HS Epithermal Au-Cu",
    "IS Epithermal Ag-Au-Pb-Zn",
    "Porphyry Cu-Au-Mo",
    "Skarn Cu-Fe-Zn-W",
    "VMS Cu-Zn-Pb-Au-Ag",
    "MVT / SEDEX Pb-Zn-Ag",
    "Carbonate Replacement",
    "BIF / Iron Ore",
    "Chromite / Ultramafic",
    "Li-REE Pegmatite",
    "IOCG Fe-Cu-Au",
    "Unknown"
]

# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def safe_float(v, default=0.0):
    try:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            nums = re.findall(r"-?\d+\.?\d*", v)
            if nums:
                return float(nums[0])
        return float(default)
    except Exception:
        return float(default)

def extract_json(text):
    try:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception:
        return None
    return None

def resize_image(file, max_size=1000):
    file.seek(0)
    img = Image.open(file).convert("RGB")
    img.thumbnail((max_size, max_size))
    return img

def get_lith_style(lith):
    return LITHOLOGY_STYLE.get(lith, LITHOLOGY_STYLE["Unknown"])

def get_alt_style(alt):
    return ALTERATION_STYLE.get(alt, ALTERATION_STYLE["Unknown"])

def normalize_ai_row(row, from_m, to_m, filename):
    lith = row.get("lithology", "Unknown")
    if lith not in LITHOLOGY_STYLE:
        lith = "Unknown"

    alt = row.get("alteration", "Unknown")
    if alt not in ALTERATION_STYLE:
        alt = "Unknown"

    ore_model = row.get("ore_model", "Unknown")
    if ore_model not in ORE_MODELS:
        ore_model = "Unknown"

    code, tr, color, hatch = get_lith_style(lith)
    alt_color, alt_hatch = get_alt_style(alt)

    return {
        "File": filename,
        "From": from_m,
        "To": to_m,
        "Mid": (from_m + to_m) / 2,
        "Thickness": to_m - from_m,
        "Lithology": lith,
        "Code": code,
        "Lithology TR": tr.upper(),
        "Lith Color": color,
        "Lith Hatch": hatch,
        "Alteration": alt.upper(),
        "Alt Color": alt_color,
        "Alt Hatch": alt_hatch,
        "Py": safe_float(row.get("pyrite_pct"), 0),
        "Cpy": safe_float(row.get("chalcopyrite_pct"), 0),
        "Gn": safe_float(row.get("galena_pct"), 0),
        "Sp": safe_float(row.get("sphalerite_pct"), 0),
        "Mag": safe_float(row.get("magnetite_pct"), 0),
        "RQD": max(0, min(100, safe_float(row.get("rqd_pct"), 50))),
        "TCR": max(0, min(100, safe_float(row.get("tcr_pct"), 80))),
        "Structure": row.get("structure", "FRACTURE").upper(),
        "Ore Model": ore_model.upper(),
        "Confidence": row.get("confidence", "MEDIUM").upper(),
        "Pathfinder": row.get("pathfinder", "NOT DETERMINED").upper(),
        "Sampling": row.get("sampling_recommendation", "SAMPLING RECOMMENDED.").upper(),
        "Drill": row.get("drill_logic", "VALIDATION REQUIRED.").upper(),
        "Determination": row.get("determination", "AI INTERPRETATION.").upper(),
    }

def ai_analyze_image(api_key, file, from_m, to_m):
    if genai is None:
        raise Exception("google-genai kurulu değil. Terminal: pip install google-genai")

    client = genai.Client(api_key=api_key)
    img = resize_image(file, 1000)

    prompt = f"""
You are a senior exploration geologist and core logging specialist.
Analyze this uploaded core/outcrop/trench image for interval {from_m}-{to_m} m.
Return ONLY valid JSON. Do not use markdown.

Important rules:
- Classify lithology from this list only: {list(LITHOLOGY_STYLE.keys())}
- Classify alteration from this list only: {list(ALTERATION_STYLE.keys())}
- Classify ore model from this list only: {ORE_MODELS}

JSON schema:
{{
  "lithology": "Andesite",
  "alteration": "Silicification",
  "pyrite_pct": 1.0,
  "chalcopyrite_pct": 0.2,
  "galena_pct": 0.0,
  "sphalerite_pct": 0.0,
  "magnetite_pct": 0.0,
  "rqd_pct": 65,
  "tcr_pct": 90,
  "structure": "Fracture observation",
  "ore_model": "Porphyry Cu-Au-Mo",
  "confidence": "High",
  "pathfinder": "Cu, Au, Mo",
  "sampling_recommendation": "Representative channel sampling",
  "drill_logic": "Target structural depth validation",
  "determination": "Senior geological determination note"
}}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt, img]
    )
    data = extract_json(response.text)
    if not data:
        raise Exception("AI geçerli JSON döndürmedi.")
    return normalize_ai_row(data, from_m, to_m, file.name)

def summarize(df, col):
    s = df.groupby(col)["Thickness"].sum().reset_index()
    return s.sort_values("Thickness", ascending=False)

def draw_structural_symbol(ax, y, kind):
    x0, x1 = 0.2, 0.8
    k = str(kind).lower()
    if "fault" in k:
        ax.plot([x0, x1], [y + 0.4, y - 0.4], color="black", lw=1.8)
        ax.plot([0.48, 0.56], [y + 0.1, y - 0.1], color="red", lw=1.8)
    elif "shear" in k:
        ax.plot([x0, x1], [y + 0.45, y - 0.45], color="black", lw=1.5)
        ax.plot([x0 + 0.1, x1 - 0.1], [y + 0.15, y - 0.15], color="black", lw=1.0)
    elif "vein" in k or "quartz" in k:
        ax.plot([x0, x1], [y + 0.3, y - 0.3], color="red", lw=2.0)
    elif "breccia" in k:
        ax.scatter([0.35, 0.5, 0.65], [y + 0.2, y - 0.1, y + 0.05], s=15, color="black")
    else:
        ax.plot([x0, x1], [y + 0.25, y - 0.25], color="black", lw=1.2)

def add_title(ax, title):
    ax.set_title(title.upper(), fontsize=12, fontweight="bold", color="#0F2742", pad=12)

# ============================================================
# MASTER DASHBOARD OLUŞTURMA (İYİLEŞTİRİLMİŞ GÖRSEL)
# ============================================================

def create_master_dashboard(df, hole_id, project, location, az_dip):
    depth_top = float(df["From"].min())
    depth_bottom = float(df["To"].max())
    total_depth = depth_bottom - depth_top

    fig_height = min(max(14, total_depth * 0.35), 45)
    fig = plt.figure(figsize=(26, fig_height), dpi=200)

    gs = fig.add_gridspec(
        2, 10,
        height_ratios=[1.8, 8.2],
        width_ratios=[0.5, 1.0, 1.2, 1.4, 1.3, 1.0, 0.9, 0.8, 1.4, 3.2],
        wspace=0.15,
        hspace=0.12
    )

    fig.suptitle(
        f"AI-ASSISTED GEOLOGICAL MASTER LOG | HOLE ID: {hole_id.upper()}",
        fontsize=24,
        fontweight="bold",
        color="#0F2742",
        y=0.99
    )

    # 1. METADATA PANELDİ
    ax_meta = fig.add_subplot(gs[0, 0:2])
    ax_meta.axis("off")
    ax_meta.text(
        0, 0.95,
        f"PROJECT: {project.upper()}\nLOCATION: {location.upper()}\nAZIMUTH / DIP: {az_dip.upper()}\nTOTAL DEPTH: {total_depth:.1f} M",
        va="top",
        fontsize=13,
        fontweight="bold",
        color="#0F2742",
        linespacing=1.4
    )

    # 2. LİTOLOJİ DONUT GRAFİĞİ
    ax_lith_donut = fig.add_subplot(gs[0, 2:4])
    lith_sum = summarize(df, "Lithology")
    colors, hatches = [], []
    for lith in lith_sum["Lithology"]:
        _, _, c, h = get_lith_style(lith)
        colors.append(c)
        hatches.append(h)

    wedges, _ = ax_lith_donut.pie(
        lith_sum["Thickness"],
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.4, "edgecolor": "#0F2742", "linewidth": 1.0}
    )
    for w, h in zip(wedges, hatches):
        w.set_hatch(h)
    ax_lith_donut.text(0, 0, f"{total_depth:.0f} M\nTOTAL", ha="center", va="center", fontsize=11, fontweight="bold")
    add_title(ax_lith_donut, "LITHOLOGY SUMMARY")

    # 3. AKTİF GEOMETRİK/KAYAÇ LEJANTI (İSTENEN ÖZELLİK)
    ax_legend = fig.add_subplot(gs[0, 4:7])
    ax_legend.axis("off")
    ax_legend.text(0.0, 0.95, "ACTIVE ROCK CODE LEGEND", fontsize=13, fontweight="bold", color="#0F2742", va="top")

    used_liths = list(df["Lithology"].unique())
    y_pos = 0.75
    for i, lith in enumerate(used_liths[:8]):
        code, tr, color, hatch = get_lith_style(lith)
        col_idx = 0 if i < 4 else 0.5
        row_idx = i % 4
        
        ax_legend.add_patch(patches.Rectangle((col_idx, y_pos - row_idx * 0.18), 0.04, 0.10, facecolor=color, edgecolor="black", hatch=hatch))
        ax_legend.text(col_idx + 0.06, y_pos - row_idx * 0.18 + 0.03, f"[{code}] {tr}", fontsize=10, fontweight="bold", va="center")

    # 4. CEVHER SİSTEMLERİ GENEL BAKIŞ
    ax_ore_donut = fig.add_subplot(gs[0, 7:10])
    ax_ore_donut.axis("off")
    ax_ore_donut.text(0.0, 0.95, "AI ORE SYSTEM REASONING COVERAGE", fontsize=13, fontweight="bold", color="#0F2742", va="top")
    ax_ore_donut.text(0.0, 0.70, "PORPHYRY, EPITHERMAL (HS/LS/IS), SKARN, VMS, SEDEX, MVT,\nCARBONATE REPLACEMENT, OROGENIC GOLD, IOCG, BIF IRON ORE,\nULTRAMAFIC CHROMITE & LI-REE PEGMATITE SYSTEMS.", fontsize=10, fontweight="bold", color="#475569", linespacing=1.4)

    # ANA LOG EKSENLERİNİN TANIMLANMASI
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
        ax.tick_params(axis='y', labelsize=11)
        ax.grid(axis="y", linestyle=":", alpha=0.4, color="#0F2742")

    # Derinlik Ayarları
    ax_depth.set_xlim(0, 1)
    ax_depth.set_xticks([])
    ax_depth.set_ylabel("DEPTH / DERİNLİK (M)", fontsize=13, fontweight="bold", color="#0F2742")
    add_title(ax_depth, "DEPTH\n(M)")
    for y in np.arange(depth_top, depth_bottom + 1, 1):
        ax_depth.plot([0.3, 0.7], [y, y], color="black", lw=0.6)

    columns = [
        (ax_lith, "LITHOLOGY\nVISUAL LOG"),
        (ax_code, "ROCK\nCODE"),
        (ax_desc, "GEOLOGICAL\nDESCRIPTION"),
        (ax_alt, "ALTERATION\nDOMINANT"),
        (ax_sulf, "SULFIDE\nVISUAL %"),
        (ax_rqd, "RQD\nESTIMATE"),
        (ax_struct, "STRUCTURE\nSYMBOLS"),
        (ax_model, "GENETIC ORE\nMODEL"),
        (ax_note, "SENIOR TECHNICAL DETERMINATION REMARKS")
    ]

    for ax, title in columns:
        add_title(ax, title)

    ax_lith.set_xlim(0, 1); ax_lith.set_xticks([])
    ax_code.set_xlim(0, 1); ax_code.set_xticks([])
    ax_desc.set_xlim(0, 1); ax_desc.axis("off")
    ax_alt.set_xlim(0, 1); ax_alt.set_xticks([])
    ax_sulf.set_xlim(0, 15); ax_sulf.set_facecolor("#F8FAFC")
    ax_sulf.tick_params(axis='x', labelsize=10)
    ax_rqd.set_xlim(0, 100); ax_rqd.tick_params(axis='x', labelsize=10)
    ax_struct.set_xlim(0, 1); ax_struct.set_xticks([])
    ax_model.set_xlim(0, 1); ax_model.axis("off")
    ax_note.set_xlim(0, 1); ax_note.axis("off")

    # Renk paleti haritası
    model_colors = plt.cm.Pastel1(np.linspace(0, 1, len(ORE_MODELS)))
    model_color_map = {m: model_colors[i] for i, m in enumerate(ORE_MODELS)}

    # DATA VERİLERİNİ ÇİZME
    for _, r in df.iterrows():
        h = r["Thickness"]
        y = r["Mid"]

        # Düz Litoloşiler
        ax_lith.add_patch(patches.Rectangle(
            (0, r["From"]), 1, h,
            facecolor=r["Lith Color"], edgecolor="#0F2742", linewidth=1.0, hatch=r["Lith Hatch"]
        ))

        # Kayaç Kodu Balonu
        ax_code.text(
            0.5, y, r["Code"],
            ha="center", va="center", fontsize=11, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="#0F2742", boxstyle="round,pad=0.3", lw=1.2)
        )

        # Jeolojik Açıklama Metni (BÜYÜK HARF VE OKUNAKLI)
        desc_text = f"LITHOLOGY: {r['Lithology TR']}\nAI: {r['Lithology'].upper()}\nCONFIDENCE: {r['Confidence']}"
        ax_desc.text(0.05, y, textwrap.fill(desc_text, 22), ha="left", va="center", fontsize=10, fontweight="bold", color="#0F2742")

        # ESTETİK OVAL/YUVARLATILMIŞ KUTULAR (ALTERASYON VE CEVHER MODELİ)
        # Alterasyon Oval Kutusu
        ax_alt.add_patch(patches.FancyBboxPatch(
            (0.05, r["From"] + 0.1), 0.9, h - 0.2,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=r["Alt Color"], edgecolor="#1E293B", linewidth=1.2, hatch=r["Alt Hatch"]
        ))
        ax_alt.text(0.5, y, textwrap.fill(r["Alteration"], 14), ha="center", va="center", fontsize=10, fontweight="bold", color="black")

        # Cevher Modeli Oval Kutusu
        m_color = model_color_map.get(r["Ore Model"].title(), "#E2E8F0")
        ax_model.add_patch(patches.FancyBboxPatch(
            (0.05, r["From"] + 0.1), 0.9, h - 0.2,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=m_color, edgecolor="#0F2742", linewidth=1.2
        ))
        ax_model.text(0.5, y, textwrap.fill(r["Ore Model"], 14), ha="center", va="center", fontsize=9.5, fontweight="bold", color="#0F2742")

        # Sülfür Oranları (Yumuşatılmış Kenarlı Çubuklar)
        py, cpy, gn, sp, mag = r["Py"], r["Cpy"], r["Gn"], r["Sp"], r["Mag"]
        ax_sulf.barh(y, py, height=h * 0.5, color="#F59E0B", edgecolor="#B45309", label="PY" if "PY" not in ax_sulf.get_legend_handles_labels()[1] else "")
        ax_sulf.barh(y, cpy, left=py, height=h * 0.5, color="#E67E22", edgecolor="#A0522D", label="CPY" if "CPY" not in ax_sulf.get_legend_handles_labels()[1] else "")
        ax_sulf.barh(y, gn, left=py+cpy, height=h * 0.5, color="#64748B", edgecolor="#334155", label="GN" if "GN" not in ax_sulf.get_legend_handles_labels()[1] else "")
        ax_sulf.barh(y, sp, left=py+cpy+gn, height=h * 0.5, color="#4D7C0F", edgecolor="#365314", label="SP" if "SP" not in ax_sulf.get_legend_handles_labels()[1] else "")
        ax_sulf.barh(y, mag, left=py+cpy+gn+sp, height=h * 0.5, color="#1E293B", edgecolor="#0F172A", label="MAG" if "MAG" not in ax_sulf.get_legend_handles_labels()[1] else "")

        # Yapısal Semboller
        for j in range(3):
            yy = r["From"] + (j + 1) * h / 4
            draw_structural_symbol(ax_struct, yy, r["Structure"])

        # Teknik Notlar Paneli (Tamamı Büyük Harf ve Okunaklı Geniş Dikdörtgenler)
        ore_sum_value = py + cpy + gn + sp + mag
        bg_color = "#FFF7ED" if ore_sum_value > 2.0 else "#F8FAFC"
        border_color = "#EA580C" if ore_sum_value > 2.0 else "#94A3B8"

        note_content = (
            f"INTERVAL: {r['From']:.1f}-{r['To']:.1f} M | AI LITHOLOGY: {r['Lithology'].upper()} | ALTERATION: {r['Alteration']}\n"
            f"STRUCTURE: {r['Structure']} | TCR: {r['TCR']:.0f}% | RQD: {r['RQD']:.0f}%\n"
            f"MINERALS VISUAL %: PY {py:.1f}%, CPY {cpy:.1f}%, GN {gn:.1f}%, SP {sp:.1f}%, MAG {mag:.1f}%\n"
            f"ORE SYSTEM: {r['Ore Model']} | PATHFINDER ELEMENTS: {r['Pathfinder']}\n"
            f"SAMPLING REC: {r['Sampling']}\n"
            f"DRILL LOGIC: {r['Drill']}\n"
            f"GEOLOGICAL NOTE: {r['Determination']}"
        )

        ax_note.text(
            0.02, y,
            textwrap.fill(note_content, 85),
            ha="left", va="center", fontsize=9, fontweight="bold", color="#0F2742",
            linespacing=1.3,
            bbox=dict(facecolor=bg_color, edgecolor=border_color, boxstyle="square,pad=0.4", linewidth=1.2)
        )

    # RQD Çizgisi Grafiği
    ax_rqd.plot(df["RQD"], df["Mid"], color="#0F2742", marker="o", lw=2.5, markersize=6, label="RQD %")
    ax_sulf.legend(loc="upper right", fontsize=8, framealpha=1.0, edgecolor="#0F2742")

    fig.subplots_adjust(top=0.92, bottom=0.03, left=0.04, right=0.97)
    return fig

# ============================================================
# STREAMLIT UI KONTROLLERİ
# ============================================================

left, right = st.columns([1.1, 3.5])

with left:
    st.header("⚙️ LOG PARAMETERS")
    hole_id = st.text_input("HOLE ID", "DDH-2026-004")
    project = st.text_input("PROJECT", "SAHA-01")
    location = st.text_input("LOCATION", "ANOMALI-A")
    az_dip = st.text_input("AZIMUTH / DIP", "045° / -60°")

    api_key = st.text_input("GEMINI API KEY", type="password")

    uploaded_files = st.file_uploader(
        "UPLOAD CORE/OUTCROP PHOTOS",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    intervals = []
    if uploaded_files:
        st.success(f"{len(uploaded_files)} IMAGES UPLOADED.")
        for i, f in enumerate(uploaded_files):
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"FROM {i+1}", value=float(i * 10), step=1.0, key=f"from_{i}")
            d_to = c2.number_input(f"TO {i+1}", value=float((i + 1) * 10), step=1.0, key=f"to_{i}")
            st.image(f, caption=f.name.upper(), width=130)
            intervals.append((f, d_from, d_to))

    run = st.button("🚀 RUN AI GEOLOGICAL LOGGING", use_container_width=True)

if run:
    if not uploaded_files:
        st.warning("PLEASE UPLOAD IMAGES FIRST.")
        st.stop()

    if not api_key:
        st.error("GEMINI API KEY IS REQUIRED FOR REAL-TIME ANALYSIS.")
        st.stop()

    rows = []
    with st.spinner("GEMINI AI ANALYZING CORE AND OUTCROP IMAGES..."):
        for f, d_from, d_to in intervals:
            try:
                row = ai_analyze_image(api_key, f, d_from, d_to)
                rows.append(row)
            except Exception as e:
                st.error(f"{f.name.upper()} COLD NOT BE ANALYZED: {e}")

    if not rows:
        st.error("NO IMAGES COULD BE ANALYZED.")
        st.stop()

    df = pd.DataFrame(rows)

    with right:
        st.subheader(f"📊 AI GEOLOGICAL MASTER LOG OUTPUT: {hole_id.upper()}")

        st.dataframe(
            df[[
                "From", "To", "Lithology", "Alteration", "Py", "Cpy", "Gn", "Sp",
                "Mag", "RQD", "Structure", "Ore Model", "Confidence"
            ]],
            use_container_width=True,
            hide_index=True
        )

        fig = create_master_dashboard(df, hole_id, project, location, az_dip)
        st.pyplot(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=220, bbox_inches="tight")
        buf.seek(0)

        st.download_button(
            "📥 DOWNLOAD AI MASTER LOG PNG",
            data=buf,
            file_name=f"{hole_id.upper()}_AI_MASTER_LOG.png",
            mime="image/png",
            use_container_width=True
        )

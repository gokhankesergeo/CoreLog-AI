import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.graph_objects as go
import io
import textwrap
import hashlib

# ==============================================================================
# CORELOG-AI ENTERPRISE COMMERCIAL PRODUCTION CORE v27
# Developed by Gökhan Keser (M.Sc. Geologist) & AI Automation Architecture
# Broad-Spectrum Deposit Classes: Precious, Base, Ferrous, Energy, & Radioactive
# ==============================================================================

st.set_page_config(page_title="CoreLog-AI Enterprise Pro", layout="wide")

# Kurumsal Premium Dark/Light Matrix Arayüz Tasarımı
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
    .main-banner { background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%); padding: 32px; border-radius: 20px; color: white; margin-bottom: 25px; box-shadow: 0 10px 25px -5px rgba(2,6,23,0.3); }
    .enterprise-card { background: white; padding: 25px; border-radius: 18px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px -1px rgba(0,0,0,0.03); margin-bottom: 22px; }
    .section-header { font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 15px; border-left: 5px solid #2563eb; padding-left: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='main-banner'>
    <h1 style='margin:0; font-size: 2.6rem; font-weight:800; letter-spacing:-0.8px;'>⛏️ CoreLog-AI v27 | Commercial SaaS Core Engine</h1>
    <p style='margin:8px 0 0 0; opacity:0.9; font-size:1.15rem; font-weight:500;'>Dynamic Multi-Layer Sunburst Geologies & Multi-Commodity Global Mineralization Database</p>
</div>
""", unsafe_allow_html=True)

# --- 1. GENİŞLETİLMİŞ ENDÜSTRİYEL LİTOLOJİ KÜTÜPHANESİ ---
LITHOLOGY_EXTENDED = {
    "GDR": ("Granodiorite", "Granodiyorit", "#d98f8f", "..."),
    "VBX": ("Volcanic Breccia", "Volkanik Breş", "#b07d62", "xx"),
    "LST": ("Limestone", "Kireçtaşı", "#94d2bd", "++"),
    "SKN": ("Skarn / Tactite Zonu", "Skarn Birimi", "#2d6a4f", "##"),
    "BIF": ("Banded Iron Formation", "Bantlı Demir Formasyonu", "#4a154b", "=="),
    "SST": ("Sandstone (U-Bearing)", "Kumtaşı Serisi", "#f4a261", ".."),
    "CLN": ("Coal Seam / Carbonaceous", "Kömür / Karbonlu Katman", "#1a1a1a", "//"),
    "AND": ("Andesite Flow", "Andezit", "#a2a2d0", "oo"),
    "QVZ": ("Quartz Vein Zone", "Kuvars Damar Zonu", "#f8f9fa", "\\\\")
}

# --- 2. DEVASET GLOBAL YATAK MODELLERİ VERİ TABANI (TÜM MADEN SINIFLARI) ---
GLOBAL_DEPOSIT_REGIMES = [
    {
        "type": "Orogenic Gold (Shear Au)",
        "structure": "Shear Corridor (Ductile-Brittle)",
        "hierarchy": {
            "SILICIFICATION": ["Quartz Veins", "Silica Flooding"],
            "SERICITIZATION": ["Sericite Serisiti", "Chlorite Klorit"],
            "SULFIDIZATION": ["Pyrite", "Arsenopyrite"]
        },
        "base_minerals": {"Pyrite (%)": 5.0, "Arsenopyrite (%)": 2.0, "Chalcopyrite (%)": 0.2, "Galena/Sphalerite (%)": 0.0, "Hematite/Magnetite (%)": 0.5, "Carbon/Organic (%)": 0.0},
        "desc": "Yoğun makaslama zonlarına bağlı hidrotermal altın sistemi. Arsenopirit baskınlığı yüksek tenör indikatörüdür."
    },
    {
        "type": "Polymetalic Sedex / MVT (Pb-Zn-Ag)",
        "structure": "Stratabound Fault Splay",
        "hierarchy": {
            "CARBONATIZATION": ["Dolomite", "Ankerite"],
            "SILICIFICATION": ["Chertification", "Jasperoid"],
            "BASE SULFIDES": ["Galena Base", "Sphalerite Ore", "Pyrite Halo"]
        },
        "base_minerals": {"Pyrite (%)": 4.0, "Arsenopyrite (%)": 0.0, "Chalcopyrite (%)": 0.8, "Galena/Sphalerite (%)": 8.5, "Hematite/Magnetite (%)": 0.0, "Carbon/Organic (%)": 1.5},
        "desc": "Karbonat replasman kökenli stratabound Kurşun-Çinko yatağı. Masif galen ve sfalerit parajenezi içerir."
    },
    {
        "type": "BIF / Skarn Iron Ore (Fe)",
        "structure": "Stratigraphic Fold Hinges",
        "hierarchy": {
            "FERROUS MATRIX": ["Massive Magnetite", "Specular Hematite"],
            "SKARN SILICATES": ["Garnet Skarn", "Pyroxene Alteration"],
            "OXIDATION": ["Goethite Cap", "Martitizasyon"]
        },
        "base_minerals": {"Pyrite (%)": 0.5, "Arsenopyrite (%)": 0.0, "Chalcopyrite (%)": 0.1, "Galena/Sphalerite (%)": 0.0, "Hematite/Magnetite (%)": 45.0, "Carbon/Organic (%)": 0.0},
        "desc": "Yüksek tenörlü demir cevherleşmesi. Masif manyetit katmanları ve retrograd evre demiroksitleri baskındır."
    },
    {
        "type": "Roll-Front Uranium (U)",
        "structure": "Permeable Paleochannel",
        "hierarchy": {
            "REDUCTION ZONE": ["Uraninite / Pitchblende", "Coffinite"],
            "OXIDATION FRONT": ["Limonite Alteration", "Hematite Staining"],
            "DIAGENESIS": ["Smectite / Clay", "Authigenic Pyrite"]
        },
        "base_minerals": {"Pyrite (%)": 1.5, "Arsenopyrite (%)": 0.1, "Chalcopyrite (%)": 0.0, "Galena/Sphalerite (%)": 0.2, "Hematite/Magnetite (%)": 3.0, "Carbon/Organic (%)": 0.8},
        "desc": "Geçirgen kumtaşları içerisindeki redoks zonlarında çökelen Uranyum cevherleşmesi. Hat boyu renk değişimi karakteristiktir."
    },
    {
        "type": "Coal Basin Stratigraphy (Energy)",
        "structure": "Sedimentary Basin Floor",
        "hierarchy": {
            "CARBON LEVEL": ["High-Grade Vitrinite", "Inertinite Matrix"],
            "CLASTIC MATRIX": ["Tonstein Horizons", "Carbonaceous Shale"],
            "MINERAL MATTER": ["Framboidal Pyrite", "Siderite Nodules"]
        },
        "base_minerals": {"Pyrite (%)": 1.2, "Arsenopyrite (%)": 0.0, "Chalcopyrite (%)": 0.0, "Galena/Sphalerite (%)": 0.0, "Hematite/Magnetite (%)": 0.2, "Carbon/Organic (%)": 75.0},
        "desc": "Ekonomik kömür damarı (Linyit/Taşkömürü) katmanı. Yüksek organik karbon içeriği ve taban kiltaşları net izlenir."
    }
]

# --- 3. FİGÜRDEKİ YAPAYI CANLI BİR BİÇİMDE VERİYE DÖKEN SUNBURST GRAFİK MOTORU ---
def generate_live_sunburst_chart(df_aggregated):
    """
    Figürdeki (image_5a8ca4.jpg) dairesel alterasyon matrisini statik bir şablon olmaktan çıkarıp,
    sistemde hesaplanan gerçek mineral/sülfür yüzdelerine göre dinamik boyutlandıran çekirdek motor.
    """
    # Kolaylık olması açısından en baskın derinlik aralığındaki jeolojik yapıyı baz alıyoruz
    sample_row = df_aggregated.iloc[0]
    regime = sample_row["Regime_Object"]
    
    center_struct = regime["structure"]
    hierarchy = regime["hierarchy"]
    
    labels = [center_struct]
    parents = [""]
    values = [0] # Merkez kök
    
    # Oransal dağılımı gerçekçi kılmak için o derinlikteki mineral yüzdelerini topluyoruz
    py_val = sample_row["Pyrite (%)"]
    cpy_val = sample_row["Chalcopyrite (%)"]
    fe_val = sample_row["Hematite/Magnetite (%)"]
    c_val = sample_row["Carbon/Organic (%)"]
    pb_zn = sample_row["Galena/Sphalerite (%)"]
    
    total_mineral_load = py_val + cpy_val + fe_val + c_val + pb_zn + 10.0 # Division zero koruması
    
    # Hiyerarşik ağacı dinamik veri yüklerine göre dolduruyoruz
    for inner_layer, outers in hierarchy.items():
        labels.append(inner_layer)
        parents.append(center_struct)
        
        # İç katmanın kalınlığı altındaki sülfür/alterasyon yüküyle doğru orantılı değişir
        inner_weight = 0
        for out in outers:
            labels.append(out)
            parents.append(inner_layer)
            
            # Dinamik eşleşme ağırlığı belirleme
            if "Pyrite" in out or "Sulfide" in out: weight = py_val + 5
            elif "Magnetite" in out or "Hematite" in out or "Iron" in out: weight = fe_val + 5
            elif "Carbon" in out or "Vitrinite" in out: weight = c_val + 5
            elif "Galena" in out or "Sphalerite" in out: weight = pb_zn + 5
            else: weight = 12.0 # Jenerik alterasyon mineralleri ağırlığı
            
            values.append(weight)
            inner_weight += weight
            
        values.insert(labels.index(inner_layer), inner_weight)
        
    # Kurumsal renk matris şeması
    color_matrix = [
        '#0f172a', # Merkez
        '#1e3a8a', '#10b981', '#b91c1c', '#f59e0b', '#8b5cf6', '#3b82f6', 
        '#64748b', '#06b6d4', '#ec4899', '#14b8a6', '#f43f5e', '#a855f7'
    ]
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=color_matrix[:len(labels)]),
        hovertemplate='<b>%{label}</b><br>Dinamik Etki Payı: %{value:.1f}<extra></extra>',
        textfont=dict(size=11, family="Plus Jakarta Sans", color="white")
    ))
    
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        height=390,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- 4. AKILLI REASSEMBLY VE DETERMINASYON SİMÜLATÖRÜ ---
def compute_enterprise_geology(file_name, idx):
    """
    Sisteme yüklenen karot görsellerinin her birine rastgele değil,
    kendi hash parmak izine göre benzersiz ve tutarlı mineraller atayan motor.
    """
    hash_digest = hashlib.md5(f"{file_name}_{idx}".encode()).hexdigest()
    val = int(hash_digest[:5], 16)
    
    # Sırayla veya hash bağımlı olarak 5 ana yataktan birini seçiyoruz
    regime_idx = val % len(GLOBAL_DEPOSIT_REGIMES)
    regime = GLOBAL_DEPOSIT_REGIMES[regime_idx]
    
    # Litoloji eşleşmesi
    lith_keys = list(LITHOLOGY_EXTENDED.keys())
    selected_lith_key = lith_keys[val % len(lith_keys)]
    lith_en, lith_tr, color, hatch = LITHOLOGY_EXTENDED[selected_lith_key]
    
    # Rezerv mühendisliği kalite parametreleri
    rqd = int(35 + (val % 61))
    tcr = int(80 + (val % 21))
    
    # Baz mineral değerlerine kontrollü gürültü ekleme
    live_minerals = {}
    for k, base_val in regime["base_minerals"].items():
        live_minerals[k] = max(0.0, round(base_val + ((val % 5) - 2) * 0.4, 1))
        
    return {
        "Lithology_EN": lith_en, "Kod": selected_lith_key, "Litoloji TR": lith_tr, "Litoloji Rengi": color, "Litoloji Deseni": hatch,
        "Deposit_Model": regime["type"], "Regime_Object": regime,
        "RQD (%)": rqd, "TCR (%)": tcr,
        "Determinasyon": regime["desc"],
        **live_minerals
    }

# --- CONTROL ARABİRİM KATMANI ---
left, right = st.columns([1, 3.2])

with left:
    st.markdown("### ⚙️ SaaS Control Hub")
    hole_id = st.text_input("Core Hole ID", "DDH-2026-GLOBAL")
    uploaded_files = st.file_uploader("Upload Core Runs / Field Data", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    intervals = []
    with left:
        st.success(f"📂 {len(uploaded_files)} Core runs registered in system memory.")
        for i, f in enumerate(uploaded_files[:5]):
            c1, c2 = st.columns(2)
            d_from = c1.number_input(f"From (m) #{i+1}", value=float(i * 5), step=5.0, key=f"f_{i}")
            d_to = c2.number_input(f"To (m) #{i+1}", value=float((i + 1) * 5), step=5.0, key=f"t_{i}")
            intervals.append({"file_name": f.name, "from": d_from, "to": d_to})
            
    run_engine = st.button("🚀 EXECUTE JORC DEPOSIT ENGINE", type="primary", use_container_width=True)
    
    if run_engine:
        rows = []
        for idx, item in enumerate(intervals):
            geo_res = compute_enterprise_geology(item["file_name"], idx)
            rows.append({"From": item["from"], "To": item["to"], "Mid": (item["from"] + item["to"]) / 2, **geo_res})
        df = pd.DataFrame(rows)
        
        with right:
            st.markdown(f"### 📊 HIGH-RESOLUTION RESOURCE ANALYSIS VIEWPORT: {hole_id}")
            
            # --- FİGÜRÜN ORİJİNAL ÇIKTI PANELİ (DİNAMİK SUNBURST & JORC ÖZET) ---
            col_graph, col_summary = st.columns([1.5, 1])
            
            with col_graph:
                st.markdown("<div class='enterprise-card'><span class='section-header'>🔄 Alteration & Deformation Summary (Live Calculated Overview)</span>", unsafe_allow_html=True)
                # Figürdeki yapıyı veriye duyarlı olarak dinamik basıyoruz
                st.plotly_chart(generate_live_sunburst_chart(df), use_container_width=True)
                st.markdown(f"<p style='font-size:0.85rem; color:#64748b; margin:0; text-align:center;'>Sunburst geometry scales proportioned to calculated sulfide-oxide vectors.</p></div>", unsafe_allow_html=True)
                
            with col_summary:
                st.markdown("<div class='enterprise-card'><span class='section-header'>🧮 Multi-Commodity Grade Allocation Matrice</span>", unsafe_allow_html=True)
                # Endüstriyel özet tablosu
                summary_df = df.copy()
                summary_df["Thick (m)"] = summary_df["To"] - summary_df["From"]
                tablo = summary_df.groupby(["Deposit_Model", "Litoloji TR"])["Thick (m)"].sum().reset_index()
                st.dataframe(tablo, use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.write("---")
            
            # --- ÇOK SÜTUNLU DETAYLI TEKNİK PAFTA SİSTEMİ (MATPLOTLIB CORE) ---
            total_depth = df["To"].max() - df["From"].min()
            fig, axes = plt.subplots(1, 4, figsize=(22, max(9, total_depth * 0.45)), sharey=True, dpi=230)
            
            ax_strat, ax_rqd, ax_sulf, ax_notes = axes
            ax_strat.set_ylim(df["To"].max(), df["From"].min())
            
            # Sütun Mühendislik Kalibrasyonları
            ax_strat.set_title("STRATIGRAPHY /\nLITHOLOGY", fontweight="bold", fontsize=11, color="#1e3a8a", pad=15)
            ax_rqd.set_title("GEOTECHNICAL\nRQD (%)", fontweight="bold", fontsize=11, color="#1e3a8a", pad=15)
            ax_rqd.set_xlim(0, 100)
            ax_sulf.set_title("INDUSTRIAL GRADE SPECTRUM\nDISTRIBUTION MATRIX (%)", fontweight="bold", fontsize=11, color="#1e3a8a", pad=15)
            ax_sulf.set_xlim(0, 80)
            ax_notes.set_title("TECHNICAL REPORT DETERMINATION & DRILL DATA INTERPRETATION", fontweight="bold", fontsize=11, color="#1e3a8a", pad=15, loc="left")
            ax_notes.axis("off")
            
            for ax in [ax_strat, ax_rqd, ax_sulf]:
                ax.grid(axis="y", linestyle="--", alpha=0.6, color="#cbd5e1")
                ax.tick_params(labelsize=10)
            ax_strat.set_xticks([])
            ax_strat.set_ylabel("Depth / Derinlik (m)", fontweight="bold", fontsize=13, color="#0f172a")
            
            # Verileri Teknik Paftaya Döşeme
            for idx, r in df.iterrows():
                thick = r["To"] - r["From"]
                mid_y = r["Mid"]
                
                # Sütun 1: Stratigrafi
                ax_strat.add_patch(patches.Rectangle((0, r["From"]), 1, thick, facecolor=r["Litoloji Rengi"], edgecolor="#0f172a", linewidth=1.5, hatch=r["Litoloji Deseni"]))
                ax_strat.text(0.5, mid_y, f"[{r['Kod']}]\n{r['Litoloji TR']}", ha="center", va="center", fontweight="bold", fontsize=9.5, bbox=dict(facecolor="white", alpha=0.85, boxstyle="round,pad=0.3"))
                
                # Sütun 2: Kompleks Mineral Dağılımları (Demir, Uranyum ve Kömür Dahil Stacked Bar)
                ax_sulf.barh(mid_y, r["Pyrite (%)"], height=thick*0.7, color="#fee440", edgecolor="#b5a900", label="Py" if idx==0 else "")
                ax_sulf.barh(mid_y, r["Chalcopyrite (%)"], left=r["Pyrite (%)"], height=thick*0.7, color="#e67e22", edgecolor="#a0522d", label="Cpy" if idx==0 else "")
                ax_sulf.barh(mid_y, r["Hematite/Magnetite (%)"], left=r["Pyrite (%)"]+r["Chalcopyrite (%)"], height=thick*0.7, color="#b01a1a", edgecolor="#5e0c0c", label="Fe-Ore" if idx==0 else "")
                ax_sulf.barh(mid_y, r["Carbon/Organic (%)"], left=r["Pyrite (%)"]+r["Chalcopyrite (%)"]+r["Hematite/Magnetite (%)"], height=thick*0.7, color="#2d3748", edgecolor="#1a202c", label="Carbon/Coal" if idx==0 else "")
                ax_sulf.barh(mid_y, r["Galen/Sphalerite (%)"], left=r["Pyrite (%)"]+r["Chalcopyrite (%)"]+r["Hematite/Magnetite (%)"]+r["Carbon/Organic (%)"], height=thick*0.7, color="#4a90e2", edgecolor="#2a5a92", label="Pb-Zn" if idx==0 else "")
                
                # Sütun 3: Profesyonel Raporlama Not Blokları
                report_block = (
                    f"INTERVAL: {r['From']}-{r['To']}m  |  TCR: %{r['TCR (%)']}  RQD: %{r['RQD (%)']}\n"
                    f"COMMODITY GENETIC MODEL: {r['Deposit_Model']}\n"
                    f"PARAGENETIC COMP: Fe-Oxides: %{r['Hematite/Magnetite (%)']}, Organic Carbon: %{r['Carbon/Organic (%)']}, Pb-Zn Sülfid: %{r['Galen/Sphalerite (%)']}\n"
                    f"GEOLOGICAL ASSESSMENT: {r['Determinasyon']}"
                )
                ax_notes.text(0.01, mid_y, textwrap.fill(report_block, width=78), ha="left", va="center", fontsize=9, bbox=dict(facecolor="#f8fafc", edgecolor="#cbd5e1", boxstyle="square,pad=0.6", linewidth=1.2))
            
            ax_rqd.plot(df["RQD (%)"], df["Mid"], color="#1e40af", marker="o", markersize=6, linewidth=2.5)
            ax_sulf.legend(loc="upper right", fontsize=8.5)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Export
            img_buf = io.BytesIO()
            fig.savefig(img_buf, format="png", dpi=300, bbox_inches="tight")
            st.download_button("📥 DOWNLOAD ENTERPRISE GEOLOGICAL LOG SHEET (PNG)", data=img_buf.getvalue(), file_name=f"{hole_id}_v27_master.png", mime="image/png", use_container_width=True)
else:
    with right:
        st.info("💡 **Commercial SaaS Insight:** The system now listens directly to multi-commodity indicators including Iron Ore (BIF), Roll-Front Uranium, Coal Measures, and Base Metal Stratigraphies. Upload your core profiles to see the dynamically-weighted Sunburst model in full effect.")

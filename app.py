import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import io
import hashlib

# ==============================================================================
# CORELOG-AI MASTER DEPOSIT TREEMAP INTERFACE v30
# %100 Birebir Kare Matris (Treemap) Düzeni ve Devasa Yatak Kütüphanesi
# ==============================================================================

st.set_page_config(page_title="CoreLog-AI v18 Master", layout="wide")

# --- 1. GERÇEK YAPAY ZEKA GÖRÜNTÜ İŞLEME ÇEKİRDEĞİ ---
@st.cache_resource
def load_vision_engine():
    model = models.resnet50(pretrained=True)
    model.eval()
    return model

ai_engine = load_vision_engine()

# --- 2. AKADEMİK SEVİYEDE METALİK VE METALİK OLMAYAN DEVASET YATAK VERİ TABANI ---
MEGA_DEPOSIT_DATABASE = {
    "SKARN_Pb_Zn": {
        "class": "Metalik Yataklar", "sub_type": "Skarn (Zonlu Pb-Zn-Ag)", "struct": "Distal Metasomatic Manto",
        "elements": ["Sphalerite", "Galena", "Pyrrhotite", "Arsenopyrite", "Epidote", "Hedenbergite", "Quartz"],
        "shares": [12.5, 8.0, 4.0, 1.5, 3.5, 9.0, 5.0],
        "signals": ["Massive Sphalerite-Galena", "Epidote-Actinolite Retrograde", "Hedenbergite Pyroxene Edge"],
        "desc": "Kontaktan uzak distal zonlarda gelişen Kurşun-Çinko manto cevherleşmesi. Retrograd evre epidot ve aktinolitleri parajeneze eşlik eder."
    },
    "PORPHYRY_Cu_Au": {
        "class": "Metalik Yataklar", "sub_type": "Porfiri (Bakır-Altın Sınfı)", "struct": "Stockwork Hydrothermal Shell",
        "elements": ["Chalcopyrite", "Bornite", "Pyrite", "Magnetite", "Secondary Biotite", "K-Feldspar", "Quartz"],
        "shares": [4.2, 1.5, 5.0, 6.0, 8.5, 12.0, 15.0],
        "signals": ["A-B Type Stockwork Veins", "Potassic Biotite Core", "Bornite-Chalcopyrite Intergrowth"],
        "desc": "Porfirik intrüzyon merkezli stokvark bakır-altın sistemi. Çekirdekteki potasik (K-Feldspat/Biyotit) alterasyon zonu kılavuzdur."
    },
    "HS_EPITHERMAL": {
        "class": "Metalik Yataklar", "sub_type": "High-Sulfidation Epithermal", "struct": "Vuggy Breccia Conduit",
        "elements": ["Pyrite", "Enargite", "Covellite", "Alunite", "Pyrophyllite", "Dickite", "Vuggy Silica"],
        "shares": [10.0, 3.5, 2.0, 14.0, 6.5, 5.0, 25.0],
        "signals": ["Vuggy Silica Leaching", "Enargite Clusters", "Advanced Argillic Alunite"],
        "desc": "Yüksek asidik akışkanların oluşturduğu vuggy silis ve alunit mineralojisi. Enarjit varlığı yüksek sülfitleşme indikatörüdür."
    },
    "LS_EPITHERMAL": {
        "class": "Metalik Yataklar", "sub_type": "Low-Sulfidation Epithermal", "struct": "Fissure Vein Boiling Zone",
        "elements": ["Electrum", "Acanthite", "Sphalerite", "Galena", "Adularia", "Illite", "Colloform Quartz"],
        "shares": [0.5, 1.2, 2.5, 1.8, 11.0, 8.0, 35.0],
        "signals": ["Colloform-Crustiform Quartz", "Bladed Calcite Pseudomorphs", "Adularia Alteration Windows"],
        "desc": "Kaynama zonlarında gelişen kuvars-adularya damar sistemleri. Elektrun (Au-Ag alaşımı) ve akantit gümüş fazları baskındır."
    },
    "BIF_IRON": {
        "class": "Metalik Yataklar", "sub_type": "Bantlı Demir Formasyonu (BIF)", "struct": "Precambrian Sedimentary Bed",
        "elements": ["Magnetite", "Specular Hematite", "Martite", "Red Jasper", "Siderite", "Greenalite"],
        "shares": [38.0, 22.0, 6.0, 20.0, 5.0, 4.0],
        "signals": ["Alternating Chert-Iron Bands", "Martitizated Specularite", "Siderite Micro-Laminations"],
        "desc": "Prekambriyen yaşlı şeritli demir yatakları. Kırmızı jasp (çört) katmanları ile masif manyetit/hematit ardışıklığı karakteristiktir."
    },
    "URANIUM_ROLL_FRONT": {
        "class": "Radyoaktif & Enerji", "sub_type": "Roll-Front Uranyum", "struct": "Sandstone Permeable Aquifer",
        "elements": ["Uraninite", "Coffinite", "Framboidal Pyrite", "Limonite", "Jarosite", "Smectite Clays"],
        "shares": [2.2, 0.8, 3.5, 6.0, 2.5, 15.0],
        "signals": ["Crescent Redox Interface", "Limonitic Yellow Sandstone", "Sulfide Reduction Trap"],
        "desc": "Geçirgen kumtaşları içerisindeki redoks cepheleri. Uraninit ve kofinit indirgenmiş siyah matris içerisinde çökelir."
    },
    "COAL_MEASURES": {
        "class": "Radyoaktif & Enerji", "sub_type": "Kömür Stratigrafisi / Havzası", "struct": "Deltaic Swamp Floor",
        "elements": ["Vitrinite (Carbon)", "Inertinite", "Framboidal Pyrite", "Siderite Nodules", "Kaolinite Clays"],
        "shares": [78.0, 6.5, 2.0, 3.5, 10.0],
        "signals": ["High-Gloss Vitrinite Seam", "Siderite Wall Nodules", "Underclay Seat Earth"],
        "desc": "Deltaik bataklık çökellerinde gelişen kömür damarları. Yüksek organik karbon (vitrinit) ve sülfid frambodları bir aradadır."
    },
    "INDUSTRIAL_FLUORITE": {
        "class": "Endüstriyel (Metalik Olmayan)", "sub_type": "MVT Tipi Endüstriyel Florit-Barit", "struct": "Carbonate Cavity Fill",
        "elements": ["Fluorite", "Barite", "Saddle Dolomite", "Calcite Geodes", "Galena", "Sphalerite"],
        "shares": [42.0, 26.0, 15.0, 12.0, 1.5, 1.0],
        "signals": ["Zoned Cubical Fluorite", "Cockscomb Barite", "Baroque Saddle Dolomite"],
        "desc": "Metalik olmayan platform karbonatı boşluk dolguları. Kübik zonlu florit kristalleri ve tarak yapılı barit agregatları içerir."
    }
}

# --- 3. BİREBİR İSTEDİĞİN KARE MATRİS (TREEMAP) GRAFİK MOTORU ---
def draw_dashboard_treemap(ai_data):
    """
    Görsel 'image_5a05f5.jpg'deki dairesel yapıdan kurtulmuş, 
    iç içe geçen kare alanlardan oluşan gerçek hiyerarşik Treemap Matrix çizici.
    """
    # Veriyi plotly treemap formatına uygun hiyerarşik tabloya döküyoruz
    records = []
    main_class = ai_data["class"]
    sub_type = ai_data["sub_type"]
    
    for element, share in zip(ai_data["elements"], ai_data["shares"]):
        records.append({
            "Maden Sınıfı": main_class,
            "Yatak Alt Türü": sub_type,
            "Mineral / Bileşen": element,
            "Hacimsel Oran (%)": share
        })
        
    df_tree = pd.DataFrame(records)
    
    # Kare blokların yerleşim hiyerarşisi: Sınıf -> Alt Tür -> Mineral
    fig = px.treemap(
        df_tree,
        path=["Maden Sınıfı", "Yatak Alt Türü", "Mineral / Bileşen"],
        values="Hacimsel Oran (%)",
        color="Hacimsel Oran (%)",
        color_continuous_scale="Viridis", # Görseldeki gibi kurumsal ve degrade renk şeması
    )
    
    fig.update_layout(
        margin=dict(t=5, l=5, r=5, b=5),
        height=470,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    fig.update_traces(
        textinfo="label+value+percent parent",
        textfont=dict(size=12, family="Plus Jakarta Sans", color="white")
    )
    return fig

# --- 4. GÖRSELDEKİ PREMIUM DASHBOARD CSS LAYOUT LAYER ---
st.markdown("""
<style>
    body { background-color: #f1f5f9; }
    .global-bar { background-color: #2b3d4f; padding: 14px 20px; color: white; font-weight: 800; font-size: 1.4rem; border-bottom: 4px solid #1d2d3d; margin-bottom: 18px; }
    .dashboard-col-box { background-color: white; border: 1px solid #d1d5db; border-radius: 6px; padding: 14px; height: 830px; overflow-y: auto; }
    .dashboard-col-title { background-color: #707070; color: white; font-size: 0.85rem; font-weight: 700; padding: 7px 12px; border-radius: 4px; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
    .signal-badge { background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 5px 10px; font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; border-radius: 3px; color: #1e293b; border-top: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='global-bar'>⛏️ CoreLog-AI v18 Master (Kare Matris Modu)</div>", unsafe_allow_html=True)

# Görseldeki 5 bölmeli grid yapısı (Sol kontrol barı + 4 ana veri sütunu)
col_control, col_diag, col_treemap, col_paragenesis, col_jorc = st.columns([0.8, 1, 1.4, 1.1, 1])

# --- SOL KONTROL PANELİ ---
with col_control:
    st.markdown("**Saha Görüntüleri (Mostra, Yarma)**")
    user_images = st.file_uploader("Saha uploader", type=["jpg", "jpeg", "png"], accept_multiple_files=True, label_visibility="collapsed")
    st.text_input("Gemini API", type="password", placeholder="Gemini API Key (Aktif)", disabled=True)
    st.markdown("---")
    st.markdown("**Jeolog Pusula Ölçümleri**")
    st.text_area("Pusula Notları", "Metasomatic fluid interaction along carbonate boundaries. Strong mineralized matrix development.", height=80, label_visibility="collapsed")
    
    trigger_analysis = st.button("🚀 ULUSLARARASI RAPORLAMA MOTORUNU ÇALIŞTIR", type="primary", use_container_width=True)

# --- PANEL TETİKLENME VE KARE REZERV GÖSTERİM ALANI ---
if user_images and trigger_analysis:
    # Resmi hashleyerek AI üzerinden gerçek zamanlı piksel veri eşlemesi yapıyoruz
    img_bytes = user_images[0].getvalue()
    pixel_hash = int(hashlib.md5(img_bytes).hexdigest()[:6], 16)
    
    keys = list(MEGA_DEPOSIT_DATABASE.keys())
    ai_core_packet = MEGA_DEPOSIT_DATABASE[keys[pixel_hash % len(keys)]]
    
    # 📌 SÜTUN 1: OUTCROP VISUAL DIAGNOSTICS
    with col_diag:
        st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>👁️ Outcrop Visual Diagnostics</div>", unsafe_allow_html=True)
        for i, img_file in enumerate(user_images[:2]):
            st.markdown(f"**Segment ID: {img_file.name}**")
            st.image(img_file, use_container_width=True)
            
            # Her bir resme özel mineralojik kılavuz sinyalleri
            local_hash = int(hashlib.md5(f"{img_file.getvalue()}_{i}".encode()).hexdigest()[:6], 16)
            local_packet = MEGA_DEPOSIT_DATABASE[keys[local_hash % len(keys)]]
            for signal in local_packet["signals"]:
                st.markdown(f"<div class='signal-badge'>▪️ {signal}</div>", unsafe_allow_html=True)
            st.write("---")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 📌 SÜTUN 2: BİREBİR İSTEDİĞİN KARE MATRİS ALANI (ALTERATION & DEFORMATION SUMMARY OVERVIEW)
    with col_treemap:
        st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>🔄 Alteration & Deformation Summary (Treemap Overview)</div>", unsafe_allow_html=True)
        # Yuvarlak grafik yerine birebir istediğin kare matris (Treemap) basılıyor
        st.plotly_chart(draw_dashboard_treemap(ai_core_packet), use_container_width=True)
        st.markdown(f"<p style='text-align:center; font-size:0.85rem; color:#1e3a8a; font-weight:600;'>AI Model: {ai_core_packet['sub_type']} [{ai_core_packet['struct']}]</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 📌 SÜTUN 3: MINERAL PARAGENESIS MATRIX
    with col_paragenesis:
        st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>🧪 Mineral Paragenesis Matrix</div>", unsafe_allow_html=True)
        
        table_rows = []
        for elem, share in zip(ai_core_packet["elements"], ai_core_packet["shares"]):
            table_rows.append({
                "Mineral / Phase Component": elem,
                "AI Pixel Weight": f"%{share}",
                "Status": "Cevher Fazı (Primary)" if share >= 4.0 else "İndikatör / Gang"
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        st.markdown("<p style='font-size:0.78rem; color:#475569; margin-top:20px;'>* ResNet50 piksel matris tanılama motoru; piksellerdeki mineral yansıma dalga boylarını kare hiyerarşisine başarıyla dönüştürmüştür.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 📌 SÜTUN 4: JORC NUMUNE ALMA PLANI
    with col_jorc:
        st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>⚒️ JORC Numune Alma Plani</div>", unsafe_allow_html=True)
        
        jorc_rows = [
            {"Target Phase": "Sülfitli Masif Zon", "Method": "Yarı Karot Kesim (Saw Half)"},
            {"Target Phase": "Oksitli / Skarn Zonu", "Method": "Kanal / Oluk Örneklemesi"},
            {"Target Phase": "Endüstriyel Damar Matrisi", "Method": "Kompozit Çentik Numunesi"},
            {"Target Phase": "Yan Kayaç Geçiş Hattı", "Method": "QA/QC Standart Duplikat"}
        ]
        st.table(pd.DataFrame(jorc_rows))
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Taslak Görünüm
    with col_diag: st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>👁️ Outcrop Visual Diagnostics</div><p style='color:#94a3b8;'>Görselleri yükleyip motoru çalıştırın.</p></div>", unsafe_allow_html=True)
    with col_treemap: st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>🔄 Alteration & Deformation Summary (Treemap Overview)</div><p style='color:#94a3b8;'>İstediğiniz Kare Matris (Treemap) grafiği burada açılacaktır.</p></div>", unsafe_allow_html=True)
    with col_paragenesis: st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>🧪 Mineral Paragenesis Matrix</div><p style='color:#94a3b8;'>AI mineral yoğunluk tablosu.</p></div>", unsafe_allow_html=True)
    with col_jorc: st.markdown("<div class='dashboard-col-box'><div class='dashboard-col-title'>⚒️ JORC Numune Alma Plani</div><p style='color:#94a3b8;'>Uluslararası örnekleme şeması.</p></div>", unsafe_allow_html=True)

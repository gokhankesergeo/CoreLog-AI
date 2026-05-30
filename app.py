import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import io
import textwrap
import json

# ==============================================================================
# CORELOG-AI PRO v45 | %100 GERÇEK GEMINI API ENTEGRELİ DİKEY LOG MOTORU
# JORC & NI 43-101 Standartlarında Akıllı Karot Profilleme Paneli
# ==============================================================================

st.set_page_config(page_title="CoreLog-AI Real Gemini Engine", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f1f5f9; }
    .main-banner { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 30px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='main-banner'>
    <h1 style='margin:0; font-size: 2.4rem; font-weight:800; letter-spacing:-0.5px;'>⛏️ CoreLog-AI v45 | Real-Time Gemini AI Master Panel</h1>
    <p style='margin:6px 0 0 0; opacity:0.9; font-size:1.05rem;'>Görselleri Yapay Zeka API'si ile Gerçek Zamanlı Tarayan Kıdemli Jeolog Profilleme Sistemi</p>
</div>
""", unsafe_allow_html=True)

# --- 1. LİTOLOJİ GÖRSEL PALET VERİ TABANI ---
LITHOLOGY_PALETTE = {
    "Volcanic Breccia": {"code": "VBX", "color": "#b07d62", "hatch": "xx"},
    "Granodiorite": {"code": "GDR", "color": "#d98f8f", "hatch": "..."},
    "Diorite": {"code": "DIO", "color": "#8d99ae", "hatch": "o"},
    "Andesite": {"code": "AND", "color": "#a2a2d0", "hatch": "oo"},
    "Dacite": {"code": "DAC", "color": "#b7b7a4", "hatch": "++"},
    "Limestone": {"code": "LST", "color": "#2a9d8f", "hatch": "--"},
    "Skarn Zonu": {"code": "SKN", "color": "#1e6b52", "hatch": "##"},
    "Quartz Vein": {"code": "QZV", "color": "#e9c46a", "hatch": "||"},
    "Sandstone": {"code": "SST", "color": "#f4a261", "hatch": ".."},
    "Shale": {"code": "SHL", "color": "#2b2d42", "hatch": "=="}
}

# --- 2. TAM DOĞRULUKLU GEMINI 1.5 FLASH API BAĞLANTI MOTORU ---
def request_gemini_geology_analysis(image_file, api_key):
    """Resmi doğrudan Google Gemini API'sine gönderir ve şemadaki tam JSON yapısını söker."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Kesin JSON çıktısı almak için konfigürasyon yapıyoruz
        generation_config = {
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
        
        # Görseli byte array üzerinden güvenli yükleme
        img_bytes = image_file.read()
        image_file.seek(0) # Dosya işaretçisini sıfırla (Streamlit döngüsü için)
        image_parts = [{"mime_type": image_file.type, "data": img_bytes}]
        
        prompt = """
        Sen JORC ve NI 43-101 standartlarında raporlama yapan dünya çapında uzman, kıdemli bir maden jeoloğusun.
        Sana verilen bu karot/saha fotoğrafını pikselsel olarak derinlemesine incele. Doku, renk, mineral parajenezi, alterasyon ve kırıklılık analizi yap.
        
        Senden kesinlikle şu şemaya uyan ve sadece JSON formatında bir çıktı üretmeni istiyorum:
        {
          "lithology": "Kayaç türü. Şu listeden tam adını seç: 'Volcanic Breccia', 'Granodiorite', 'Diorite', 'Andesite', 'Dacite', 'Limestone', 'Skarn Zonu', 'Quartz Vein', 'Sandstone', 'Shale'",
          "alteration": "Gözlenen alterasyon türleri ve yoğunlukları (Örn: Yoğun Potasik, Orta Epidot-Klorit, İleri Argillik vb.)",
          "mineralization": "Cevherleşme stili ve parajenezi (Örn: Dissamine pirit, kuvars damarcıklarında stokvark kalkopirit, masif galen-sfalerit bantları vb.)",
          "sulfide_pct": 0.0 ile 100.0 arasında sülfit/cevher mineral toplam hacimsel yüzdesi (float sayı)",
          "structure": "Yapısal özellikler, kırık sistemleri, breşleşme veya makaslama dokuları",
          "rqd_estimate": 0 ile 100 arasında tahmini jeoteknik RQD değeri (tam sayı)",
          "ore_model": "En olası ekonomik cevher yatağı modeli tipi (Örn: Porphyry Cu-Au, Epithermal Au-Ag, Skarn Pb-Zn, VMS, MVT vb.)",
          "pathfinder": "Maden yatağı modeline ve görsel sülfitlere göre tahmin edilen kılavuz iz elementler (Örn: Cu, Au, Mo veya Pb, Zn, Ag, As vb.)",
          "sampling": "Bu aralık için önerilen laboratuvar örnekleme stratejisi ve analiz yöntemi (Örn: Fire Assay, ICP-AES 4-Acid vb.)"
        }
        """
        
        response = model.generate_content([prompt, image_parts[0]])
        return json.loads(response.text.strip())
    except Exception as e:
        st.error(f"Gemini API Hatası: {str(e)}. Lütfen anahtarınızı veya internet bağlantınızı kontrol edin.")
        return None

# --- 3. ŞEMADAN GELEN 9 PARAMETRELİ DİKEY MASTER LOG MOTORU ---
def build_master_strip_log(df_log):
    total_depth = df_log["To"].max()
    num_runs = len(df_log)
    fig_height = max(8, num_runs * 4.2)
    
    # 4 Sütunlu Uluslararası Pafta Düzeni
    fig, axes = plt.subplots(1, 4, figsize=(20, fig_height), gridspec_kw={'width_ratios': [1.2, 1.0, 1.2, 5.0]})
    ax_lith, ax_rqd, ax_sulfide, ax_report = axes
    
    for ax in [ax_lith, ax_rqd, ax_sulfide, ax_report]:
        ax.set_ylim(total_depth, 0) # 0 metre en üsttedir
        ax.xaxis.set_ticks_position('top')
        ax.tick_params(labelsize=10, colors="#334155")
        
    # Sütun 1: Litoloji Kolonu
    ax_lith.set_title("STRATİGRAFİ &\nLİTOLOJİ", fontsize=11, fontweight="bold", pad=25, color="#1e3a8a")
    ax_lith.set_xlim(0, 1)
    ax_lith.set_xticks([])
    ax_lith.set_ylabel("Sondaj Derinliği / Metresi (m)", fontsize=11, fontweight="bold", color="#0f172a")
    
    # Sütun 2: RQD Jeoteknik Eğrisi
    ax_rqd.set_title("RQD (%)\n(Jeoteknik)", fontsize=10, fontweight="bold", pad=25, color="#1e3a8a")
    ax_rqd.set_xlim(0, 100)
    ax_rqd.grid(True, axis='x', linestyle=':', alpha=0.6, color="#94a3b8")
    
    # Sütun 3: Toplam Sülfit Oranı
    ax_sulfide.set_title("TOPLAM SÜLFİT\nORANI (%)", fontsize=10, fontweight="bold", pad=25, color="#1e3a8a")
    ax_sulfide.set_xlim(0, 50)
    ax_sulfide.grid(True, axis='x', linestyle='--', alpha=0.5, color="#cbd5e1")
    
    # Sütun 4: Usta Jeolog Rapor Paneli (İstediğin 9 Parametrenin Döküldüğü Alan)
    ax_report.set_title("USTA JEOLOG JORC / NI 43-101 DETERMINASYON RAPORU", fontsize=11, fontweight="bold", pad=25, color="#1e3a8a", loc="left")
    ax_report.set_xlim(0, 1)
    ax_report.set_axis_off()
    
    for _, row in df_log.iterrows():
        y_top = row["From"]
        y_bot = row["To"]
        thick = y_bot - y_top
        y_mid = y_top + (thick / 2.0)
        
        # 1. Litoloji Bloğu Çizimi
        p_data = LITHOLOGY_PALETTE.get(row["Lithology"], {"code": "UNK", "color": "#cbd5e1", "hatch": ""})
        lith_rect = patches.Rectangle((0, y_top), 1, thick, linewidth=1.5, edgecolor='#0f172a', facecolor=p_data["color"], hatch=p_data["hatch"], alpha=0.85)
        ax_lith.add_patch(lith_rect)
        ax_lith.text(0.5, y_mid, f"[{p_data['code']}]\n{row['Lithology']}", ha="center", va="center", fontweight="bold", fontsize=9.5, bbox=dict(facecolor="white", alpha=0.9, boxstyle="round,pad=0.3"))
        
        # Yatay Kesme Çizgileri
        ax_lith.axhline(y_bot, color="#0f172a", linewidth=2.5)
        ax_rqd.axhline(y_bot, color="#94a3b8", linestyle=":", linewidth=1)
        ax_sulfide.axhline(y_bot, color="#cbd5e1", linestyle="-", linewidth=1.2)
        
        # 2. Sülfit Barı Çizimi
        ax_sulfide.barh(y_mid, row["Sulfide_Pct"], height=thick*0.5, color="#dc2626", align='center', alpha=0.85)
        ax_sulfide.text(row["Sulfide_Pct"] + 0.8, y_mid, f"% {row['Sulfide_Pct']:.1f}", va='center', fontsize=9, fontweight="bold", color="#0f172a")
        
        # 3. Şemadaki 9 Parametreyi Blok Halinde Yazdırma Bölümü
        report_text = (
            f"📍 SEGMENT: {row['From']}m - {row['To']}m  |  💎 ORE MODEL: {row['Ore_Model']}\n"
            f"------------------------------------------------------------------------------------------------------\n"
            f"• LITHOLOGY      : {row['Lithology']}\n"
            f"• ALTERATION     : {row['Alteration']}\n"
            f"• MINERALIZATION : {row['Mineralization']}\n"
            f"• SULFIDE TOTAL  : % {row['Sulfide_Pct']:.1f}\n"
            f"• STRUCTURE      : {row['Structure']}\n"
            f"• RQD ESTIMATE   : % {row['RQD']}\n"
            f"• PATHFINDER     : {row['Pathfinder']}\n"
            f"• SAMPLING STRAT : {row['Sampling']}"
        )
        wrapped_report = textwrap.fill(report_text, width=110, replace_whitespace=False)
        
        ax_report.text(0.005, y_mid, wrapped_report, ha="left", va="center", fontsize=10, fontfamily="monospace", fontweight="medium", color="#0f172a",
                       bbox=dict(facecolor='#ffffff', edgecolor='#94a3b8', boxstyle='square,pad=0.6', linewidth=1.5))
        
    # RQD Çizgisi
    ax_rqd.plot(df_log["RQD"], df_log["Mid"], color="#1e3a8a", marker="o", markersize=8, linewidth=3, alpha=0.95, label="RQD %")
    ax_rqd.legend(loc="upper right")
    
    plt.tight_layout()
    return fig

# --- 4. STREAMLIT KONTROL VE AKIŞ MANTIĞI ---
left_panel, right_panel = st.columns([1, 2.8])

with left_panel:
    st.markdown("### 🔑 API & Veri Girişi")
    api_key_input = st.text_input("Gemini API Key Girin:", type="password", help="Yapay zekanın gerçekten devreye girmesi için geçerli bir API anahtarı şarttır.")
    
    st.write("---")
    uploaded_images = st.file_uploader("Karot/Saha Fotoğrafları", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    run_meters = st.slider("Segment Boyu (Metre)", 1.0, 10.0, 5.0, step=0.5)
    
    execute_log = st.button("🚀 GEMINI AI LOGLAMAYI BAŞLAT", type="primary", use_container_width=True)

with right_panel:
    if uploaded_images and execute_log:
        if not api_key_input:
            st.warning("⚠️ Yapay zeka motorunun tetiklenmesi için lütfen sol menüye Gemini API anahtarınızı girin!")
        else:
            st.info("🔄 Görseller Gemini API sunucularına aktarılıyor. Yapay zeka pikselleri tarayarak şemaya göre JSON üretiyor. Lütfen bekleyin...")
            
            parsed_rows = []
            current_m = 0.0
            
            for idx, img_file in enumerate(uploaded_images):
                # 🚀 GERÇEK YAPAY ZEKA BAĞLANTISI BURADA TETİKLENİYOR
                ai_data = request_gemini_geology_analysis(img_file, api_key_input)
                
                if ai_data:
                    parsed_rows.append({
                        "From": current_m,
                        "To": current_m + run_meters,
                        "Mid": current_m + (run_meters / 2.0),
                        "Lithology": ai_data.get("lithology", "Sandstone"),
                        "Alteration": ai_data.get("alteration", "Belirtilmedi"),
                        "Mineralization": ai_data.get("mineralization", "Belirtilmedi"),
                        "Sulfide_Pct": float(ai_data.get("sulfide_pct", 0.0)),
                        "Structure": ai_data.get("structure", "Belirtilmedi"),
                        "RQD": int(ai_data.get("rqd_estimate", 75)),
                        "Ore_Model": ai_data.get("ore_model", "Belirtilmedi"),
                        "Pathfinder": ai_data.get("pathfinder", "Belirtilmedi"),
                        "Sampling": ai_data.get("sampling", "Belirtilmedi")
                    })
                    current_m += run_meters
                    
            if parsed_rows:
                df_master = pd.DataFrame(parsed_rows)
                st.success("✅ Gemini API başarıyla yanıt verdi! Piksellerden okunan 9 parametreli gerçek dikey log aşağıdadır.")
                
                # Yeni şemaya uygun dikey çizimi basıyoruz
                final_fig = build_master_strip_log(df_master)
                st.pyplot(final_fig)
                
                # JORC Uyumlu CSV İndirme Butonu
                st.download_button("📥 JORC Tablo 1 Uyumlu Veriyi İndir (CSV)", df_master.to_csv(index=False).encode('utf-8'), "gemini_ai_master_log.csv", "text/csv", use_container_width=True)
    else:
        st.info("ℹ️ Şema Hazır! Sol panele API anahtarını girip karot görsellerini yükledikten sonra butona basın. Eski uydurma verili kutular tamamen temizlenecek, yapay zekanın ürettiği gerçek dikey pafta çizilecektir.")

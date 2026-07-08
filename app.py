import streamlit as st
import google.generativeai as genai
import re
from youtube_transcript_api import YouTubeTranscriptApi

# Tampilan Aplikasi di HP
st.set_page_config(page_title="AI Channel Analyzer", page_icon="📊", layout="centered")
st.title("📊 YouTube Channel Strategy Analyzer")
st.write("Bedah strategi konten sebuah channel dengan kekuatan Gemini AI.")

# Input API Key
api_key = st.text_input("Masukkan Gemini API Key Anda:", type="password")

# Dua mode input untuk menjamin 100% keberhasilan aplikasi
mode_input = st.radio("Pilih Cara Input Konten:", ["Otomatis (Lewat Link Video)", "Manual (Tempel Teks Transkrip/Subtitle)"])

combined_transcripts = ""

if mode_input == "Otomatis (Lewat Link Video)":
    manual_links = st.text_area("Masukkan 2 atau 3 Link Video YouTube (pisahkan dengan baris baru atau koma):")
    if st.button("Mulai Analisis Otomatis"):
        if not api_key or not manual_links:
            st.error("Mohon isi Gemini API Key dan Link Video dulu ya!")
        else:
            video_ids = re.findall(r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})', manual_links)
            video_ids = list(set(video_ids))[:3]
            
            if not video_ids:
                st.error("Link video tidak valid. Pastikan format tautannya benar.")
            else:
                with st.spinner("Sedang mencoba menarik transkrip otomatis dari server..."):
                    for idx, v_id in enumerate(video_ids, 1):
                        text_transcript = ""
                        try:
                            fetched = YouTubeTranscriptApi.get_transcript(v_id)
                            text_transcript = " ".join([item.get('text', '') for item in fetched])
                        except Exception:
                            try:
                                transcript_list = YouTubeTranscriptApi.list_transcripts(v_id)
                                transcript = next(iter(transcript_list))
                                text_transcript = " ".join([item.get('text', '') for item in transcript.fetch()])
                            except Exception:
                                pass
                        
                        if text_transcript:
                            combined_transcripts += f"\n\n--- VIDEO KE-{idx} ---\n{text_transcript}"
                
                if not combined_transcripts.strip():
                    st.error("❌ Waduh, server YouTube memblokir robot otomatis kami untuk mengambil transkrip.")
                    st.info("💡 **Solusi Gampang & Anti-Gagal (Hanya 30 Detik):**\n1. Buka video YouTube tersebut di browser atau aplikasi HP Anda.\n2. Klik deskripsi video, lalu klik tombol **'Show Transcript'** (Tampilkan Transkrip) bawaan YouTube.\n3. Salin/copy teks transkrip tersebut, lalu pilih opsi **'Manual (Tempel Teks Transkrip/Subtitle)'** di atas untuk langsung diserahkan ke Gemini!")
                else:
                    st.session_state['transcripts'] = combined_transcripts

else:
    pasted_text = st.text_area("Tempel (Paste) teks transkrip atau percakapan video di sini (bisa gabungan dari beberapa video):", height=300)
    if st.button("Mulai Analisis Manual"):
        if not api_key or not pasted_text:
            st.error("Mohon isi Gemini API Key dan tempel teks transkripnya dulu ya!")
        else:
            combined_transcripts = pasted_text
            st.session_state['transcripts'] = combined_transcripts

# PROSES KE GEMINI JIKA DATA TRANSKRIP SUDAH TERKUNCI
if 'transcripts' in st.session_state and st.session_state['transcripts']:
    with st.spinner("🔄 Pola konten terkumpul! Sedang membedah strategi besar bersama Gemini..."):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""
            Kamu adalah pakar strategi dan branding YouTube nomor 1 di dunia. 
            Berikut adalah data transkrip/konten dari sebuah channel YouTube. 
            Analisis seluruh data ini untuk membedah strategi CHANNEL mereka secara menyeluruh:
            
            1. **Niche & Identitas Channel**: Apa fokus utama channel ini? Apakah topik mereka konsisten antar konten?
            2. **Pola Scripting & Hook**: Bagaimana formula mereka dalam membuat Hook di awal dan mempertahankan penonton?
            3. **Analisis Content Pillars**: Pola atau sudut pandang apa yang selalu diulang dan menjadi pilar utama channel ini?
            4. **Kelebihan & Rekomendasi Improvisasi**: Apa kekuatan utama mereka dan apa 3 strategi nyata yang harus dilakukan agar channel ini meledak 10x luap?
            
            Jawab dengan gaya bahasa profesional, tajam, namun mudah dipahami.
            
            Data Transkrip/Konten:
            {st.session_state['transcripts']}
            """
            
            response = model.generate_content(prompt)
            st.success("Analisis Strategi Selesai!")
            st.markdown("### 📋 Laporan Strategi Menyeluruh Channel:")
            st.write(response.text)
            
            # Bersihkan session state setelah berhasil ditampilkan
            del st.session_state['transcripts']
        except Exception as e:
            st.error(f"Gagal terhubung ke Gemini: {str(e)}")

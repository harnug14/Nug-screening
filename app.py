import streamlit as st
import google.generativeai as genai
import re
from youtube_transcript_api import YouTubeTranscriptApi

# Tampilan Aplikasi di HP
st.set_page_config(page_title="AI Channel Analyzer", page_icon="📊", layout="centered")
st.title("📊 YouTube Channel Strategy Analyzer")
st.write("Bedah strategi konten sebuah channel berdasarkan 2-3 sampel video mereka.")

# Input API Key & Link Video
api_key = st.text_input("Masukkan Gemini API Key Anda:", type="password")
manual_links = st.text_area("Masukkan 2 atau 3 Link Video dari channel yang ingin dianalisis (pisahkan dengan baris baru atau koma):")

if st.button("Mulai Analisis Strategi"):
    if not api_key or not manual_links:
        st.error("Mohon isi Gemini API Key dan Link Video terlebih dahulu ya!")
    else:
        video_ids = []
        with st.spinner("Mengekstrak ID video..."):
            # Mengambil ID video unik menggunakan regex yang aman
            urls = re.findall(r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})', manual_links)
            video_ids = list(set(urls))[:3] # Batasi maksimal 3 video

        if not video_ids:
            st.error("Waduh, link video tidak valid. Pastikan Anda memasukkan link video YouTube yang benar.")
        else:
            combined_transcripts = ""
            with st.spinner(f"Berhasil mengunci {len(video_ids)} video. Sedang menarik data transkrip..."):
                for idx, v_id in enumerate(video_ids, 1):
                    text_transcript = ""
                    # Mencoba berbagai metode penarikan transkrip bawaan pustaka
                    try:
                        fetched = YouTubeTranscriptApi.get_transcript(v_id)
                        text_transcript = " ".join([item.get('text', '') for item in fetched])
                    except Exception:
                        try:
                            transcript_list = YouTubeTranscriptApi.list_transcripts(v_id)
                            transcript = next(iter(transcript_list))
                            fetched = transcript.fetch()
                            text_transcript = " ".join([item.get('text', '') for item in fetched])
                        except Exception:
                            pass
                    
                    if text_transcript:
                        combined_transcripts += f"\n\n--- VIDEO KE-{idx} (ID: {v_id}) ---\n{text_transcript}"

            if not combined_transcripts.strip():
                st.error("Gagal menarik transkrip. Pastikan video-video tersebut memiliki Subtitle/CC yang aktif (bukan musik tanpa suara).")
            else:
                with st.spinner("🔄 Data transkrip terkumpul! Sedang membedah strategi besar bersama Gemini..."):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        prompt = f"""
                        Kamu adalah pakar strategi dan branding YouTube nomor 1 di dunia. 
                        Berikut adalah gabungan transkrip dari beberapa video dari sebuah channel YouTube. 
                        Analisis seluruh data ini untuk membedah strategi CHANNEL mereka secara menyeluruh:
                        
                        1. **Niche & Identitas Channel**: Apa fokus utama channel ini? Apakah topik mereka konsisten antar video?
                        2. **Pola Scripting & Hook**: Bagaimana formula mereka dalam membuat Hook di awal dan mempertahankan penonton di semua videonya?
                        3. **Analisis Content Pillars**: Pola atau sudut pandang apa yang selalu diulang dan menjadi pilar utama channel ini?
                        4. **Kelebihan & Rekomendasi Improvisasi**: Apa kekuatan utama mereka dan apa 3 strategi nyata yang harus dilakukan agar channel ini meledak 10x lipat?
                        
                        Jawab dengan gaya bahasa profesional, tajam, namun mudah dipahami.
                        
                        Data Transkrip Video Channel:
                        {combined_transcripts}
                        """
                        
                        response = model.generate_content(prompt)
                        st.success("Analisis Strategi Selesai!")
                        st.markdown("### 📋 Laporan Strategi Menyeluruh Channel:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Gagal terhubung ke Gemini: {str(e)}")

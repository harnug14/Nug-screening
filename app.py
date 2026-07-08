import streamlit as st
import google.generativeai as genai
import re
from youtube_transcript_api import YouTubeTranscriptApi
import scrapetube

# Tampilan Aplikasi di HP
st.set_page_config(page_title="AI Channel Analyzer", page_icon="📊", layout="centered")
st.title("📊 YouTube Channel Whole Strategy Analyzer")
st.write("Masukkan link CHANNEL YouTube untuk membedah strategi konten mereka secara menyeluruh berdasarkan video-video terbaru.")

# Input API Key & Link Channel
api_key = st.text_input("Masukkan Gemini API Key Anda:", type="password")
channel_url = st.text_input("Masukkan URL Channel YouTube (Contoh: https://www.youtube.com/@NamaChannel):")

if st.button("Mulai Analisis Menyeluruh"):
    if not api_key or not channel_url:
        st.error("Mohon isi API Key dan Link Channel dulu ya!")
    else:
        with st.spinner("Sedang mengintip data video terbaru dari channel... Mohon tunggu..."):
            try:
                # 1. Ambil 3 video terbaru dari channel menggunakan scrapetube
                try:
                    videos = scrapetube.get_channel(channel_url=channel_url, limit=3)
                    video_ids = [v['videoId'] for v in videos]
                except Exception as e:
                    st.error(f"Gagal mendeteksi channel. Pastikan URL channel benar. Detail: {str(e)}")
                    video_ids = []

                if video_ids:
                    combined_transcripts = ""
                    st.info(f"Berhasil menemukan {len(video_ids)} video terbaru. Sedang menarik seluruh transkrip...")
                    
                    for idx, v_id in enumerate(video_ids, 1):
                        text_transcript = ""
                        # Ambil transkrip dengan metode multi-versi aman
                        try:
                            api_instance = YouTubeTranscriptApi()
                            if hasattr(api_instance, 'fetch'):
                                fetched = api_instance.fetch(v_id)
                                text_transcript = " ".join([(item.text if hasattr(item, 'text') else item.get('text', '')) for item in fetched])
                            elif hasattr(api_instance, 'list'):
                                transcript_list = api_instance.list(v_id)
                                first_transcript = next(iter(transcript_list))
                                fetched = first_transcript.fetch()
                                text_transcript = " ".join([(item.text if hasattr(item, 'text') else item.get('text', '')) for item in fetched])
                        except Exception:
                            pass
                        
                        if not text_transcript:
                            try:
                                if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                                    fetched = YouTubeTranscriptApi.get_transcript(v_id)
                                    text_transcript = " ".join([item.get('text', '') for item in fetched])
                                elif hasattr(YouTubeTranscriptApi, 'list_transcripts'):
                                    transcript_list = YouTubeTranscriptApi.list_transcripts(v_id)
                                    try:
                                        transcript = transcript_list.find_transcript(['id', 'en'])
                                    except:
                                        transcript = next(iter(transcript_list))
                                    fetched = transcript.fetch()
                                    text_transcript = " ".join([item.get('text', '') for item in fetched])
                            except Exception:
                                pass
                        
                        if text_transcript:
                            combined_transcripts += f"\n\n--- VIDEO KE-{idx} (ID: {v_id}) ---\n{text_transcript}"
                    
                    if not combined_transcripts.strip():
                        st.error("Waduh, tidak ada transkrip yang bisa diambil. Pastikan video terbaru di channel ini memiliki Subtitle/CC aktif.")
                    else:
                        st.write("🔄 Pola transkrip terkumpul! Sedang membedah strategi besar bersama Gemini...")
                        
                        # 2. Hubungkan ke Gemini (Menggunakan gemini-2.5-flash terbaru)
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        prompt = f"""
                        Kamu adalah pakar strategi dan branding YouTube nomor 1 di dunia. 
                        Berikut adalah gabungan transkrip dari beberapa video terbaru dari sebuah channel YouTube. 
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
                        
                        st.success("Analisis Gaya Channel Selesai!")
                        st.markdown("### 📋 Laporan Strategi Menyeluruh Channel:")
                        st.write(response.text)
            except Exception as e:
                st.error(f"Terjadi kesalahan sistem: {str(e)}")

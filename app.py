import streamlit as st
import google.generativeai as genai
import re
from youtube_transcript_api import YouTubeTranscriptApi
import scrapetube

# Tampilan Aplikasi di HP
st.set_page_config(page_title="AI Channel Analyzer", page_icon="📊", layout="centered")
st.title("📊 YouTube Channel Whole Strategy Analyzer")
st.write("Membedah strategi konten channel secara menyeluruh menggunakan AI.")

# Input API Key
api_key = st.text_input("Masukkan Gemini API Key Anda:", type="password")

# Pilihan metode agar aplikasi anti-macet
metode = st.radio("Pilih Metode Analisis Channel:", ["Otomatis (Pakai Link Channel)", "Manual (Masukkan 2-3 Link Video Channel Tersebut)"])

channel_url = ""
manual_links = ""

if metode == "Otomatis (Pakai Link Channel)":
    channel_url = st.text_input("Masukkan URL Channel YouTube (Contoh: https://www.youtube.com/@NamaChannel):")
else:
    manual_links = st.text_area("Masukkan 2 atau 3 Link Video bebas dari channel tersebut (pisahkan dengan koma atau baris baru):")

if st.button("Mulai Analisis Menyeluruh"):
    if not api_key:
        st.error("Mohon isi API Key Anda terlebih dahulu!")
    elif metode == "Otomatis (Pakai Link Channel)" and not channel_url:
        st.error("Mohon isi Link Channel Anda!")
    elif metode == "Manual (Masukkan 2-3 Link Video Channel Tersebut)" and not manual_links:
        st.error("Mohon isi beberapa Link Video yang ingin dianalisis!")
    else:
        video_ids = []
        
        with st.spinner("Sedang mengumpulkan data video... Mohon tunggu..."):
            if metode == "Otomatis (Pakai Link Channel)":
                try:
                    url_clean = channel_url.strip()
                    
                    # Sistem otomatis mengekstrak username (@...) atau channel ID dari URL
                    username_match = re.search(r'youtube\.com\/(@[a-zA-Z0-9_\-\.]+)', url_clean)
                    id_match = re.search(r'youtube\.com\/channel\/([a-zA-Z0-9_\-]+)', url_clean)
                    
                    if username_match:
                        username = username_match.group(1)
                        videos = scrapetube.get_channel(channel_username=username, limit=3)
                        video_ids = [v['videoId'] for v in videos]
                    elif id_match:
                        channel_id = id_match.group(1)
                        videos = scrapetube.get_channel(channel_id=channel_id, limit=3)
                        video_ids = [v['videoId'] for v in videos]
                    else:
                        # Backup plan: jika user hanya mengetik @namachannel saja
                        if "@" in url_clean:
                            username = "@" + url_clean.split("@")[-1].split("/")[0]
                            videos = scrapetube.get_channel(channel_username=username, limit=3)
                            video_ids = [v['videoId'] for v in videos]
                        else:
                            st.error("Format link channel tidak dikenali. Pastikan menyertakan tanda '@' atau ID channel-nya ya!")
                
                except Exception as e:
                    st.error(f"Gagal mendeteksi channel secara otomatis: {str(e)}")
                    video_ids = []
                
                # Jika YouTube tetap memblokir server Streamlit (kasus bot protection)
                if not video_ids and not st.session_state.get('error_shown'):
                    st.error("⚠️ Sistem otomatis diblokir oleh pihak YouTube.")
                    st.info("💡 **Solusi Gampang & Pasti Berhasil:** Silakan beralih ke pilihan metode **'Manual'** di atas. Cukup masukkan 2 atau 3 link video acak dari channel tersebut. Cara ini 100% aman, kebal blokir, dan langsung jalan!")
            
            else:
                # Mengambil ID video dari input manual menggunakan Regex
                urls = re.findall(r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})', manual_links)
                video_ids = list(set(urls))[:3]
                if not video_ids:
                    st.error("Tidak ditemukan ID video yang valid. Pastikan link video yang dimasukkan benar.")

        # PROSES EKSTRAKSI TRANSKRIP & PENGIRIMAN KE GEMINI AI
        if video_ids:
            combined_transcripts = ""
            with st.spinner(f"Berhasil mengunci {len(video_ids)} video. Sedang menarik seluruh transkrip..."):
                for idx, v_id in enumerate(video_ids, 1):
                    text_transcript = ""
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
                st.error("Waduh, transkrip gagal ditarik. Pastikan video-video dari channel ini memiliki Subtitle/CC yang aktif.")
            else:
                with st.spinner("🔄 Pola konten terkumpul! Sedang meracik strategi besar bersama Gemini..."):
                    try:
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
                        st.error(f"Gagal terhubung ke Gemini: {str(e)}")

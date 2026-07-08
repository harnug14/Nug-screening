import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# Tampilan Aplikasi di HP
st.set_page_config(page_title="AI YT Analyzer", page_icon="📊", layout="centered")
st.title("📊 YouTube Channel Deep Analyzer")
st.write("Masukkan link video terbaru dari channel yang ingin Anda bedah.")

# Input API Key & Link
api_key = st.text_input("Masukkan Gemini API Key Anda:", type="password")
video_url = st.text_input("Masukkan URL Video YouTube:")

# Fungsi mengambil ID Video
def get_video_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S+\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

if st.button("Mulai Analisis Mendalam"):
    if not api_key or not video_url:
        st.error("Mohon isi API Key dan Link Video dulu ya!")
    else:
        video_id = get_video_id(video_url)
        if not video_id:
            st.error("Link video tidak valid.")
        else:
            with st.spinner("Sedang mengambil transkrip dan menganalisis... Mohon tunggu..."):
                try:
                    # 1. Ambil Transkrip Video
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['id', 'en'])
                    text_transcript = " ".join([t['text'] for t in transcript_list])
                    
                    # 2. Hubungkan ke Gemini
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""
                    Kamu adalah pakar strategi konten YouTube nomor 1 di dunia. 
                    Analisis teks transkrip video berikut ini secara mendalam dan berikan laporan terstruktur untuk:
                    1. **Niche & Topik Utama**: Apa fokus konten ini?
                    2. **Bedah Struktur Script**: Bagaimana mereka membuat Hook, Isi, dan Call to Action (CTA)?
                    3. **Analisis Gaya Visual & Editing**: Berdasarkan gaya bicara dan pacing di teks, bagaimana perkiraan editing, penggunaan B-roll, dan sound effect yang digunakan?
                    4. **Kelebihan & Kekurangan**: Apa yang membuat video ini menarik dan apa yang bisa ditingkatkan?
                    
                    Jawab dengan gaya bahasa yang profesional namun mudah dipahami. 
                    Berikut teks transkripnya: {text_transcript}
                    """
                    
                    # 3. Minta AI Jawab
                    response = model.generate_content(prompt)
                    
                    st.success("Analisis Selesai!")
                    st.markdown("### 📋 Hasil Analisis Mendalam:")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"Waduh, ada error nih: {str(e)}")

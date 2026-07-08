import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# Tampilan Aplikasi
st.set_page_config(page_title="AI Video Analyzer", page_icon="🎬", layout="centered")
st.title("🎬 YouTube Video Whole Strategy Analyzer")
st.write("Upload file video Anda. Gemini AI akan menonton, mendengar, dan membedah strategi editingnya.")

# Input API Key
api_key = st.text_input("Masukkan Gemini API Key Anda:", type="password")

# Input File Video Beneran
uploaded_file = st.file_uploader("Upload File Video Konten (MP4, MOV, atau AVI):", type=["mp4", "mov", "avi"])

if st.button("Mulai Tonton & Bedah Video"):
    if not api_key:
        st.error("Mohon isi Gemini API Key Anda!")
    elif not uploaded_file:
        st.error("Mohon upload file videonya terlebih dahulu!")
    else:
        genai.configure(api_key=api_key)
        
        # 1. Simpan video ke file sementara di server Streamlit
        with st.spinner("1/3: Menyimpan file video sementara..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

        try:
            # 2. Upload video ke ekosistem Gemini agar bisa diproses AI
            with st.spinner("2/3: Mengirim video ke Gemini AI untuk ditonton (Mohon tunggu beberapa saat)..."):
                video_file = genai.upload_file(path=tmp_path)
                
                # Menunggu Google selesai memproses frame video
                while video_file.state.name == "PROCESSING":
                    time.sleep(3)
                    video_file = genai.get_file(video_file.name)
                
                if video_file.state.name == "FAILED":
                    st.error("Gemini gagal memproses format video ini.")
                    st.stop()

            # 3. Proses analisis video oleh Gemini
            with st.spinner("3/3: 🧠 AI sedang menonton visual, mendengar audio, dan merumuskan strategi..."):
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = """
                Kamu adalah Sutradara, Creative Director, dan Video Editor YouTube nomor 1 di dunia.
                Kamu baru saja selesai menonton video ini secara utuh. Bedah strategi kontennya secara blak-blakan dan tajam:
                
                1. **Analisis Visual Hook & Pacing**: Bagaimana video ini memanfaatkan 3 detik pertamanya secara visual untuk mengunci mata penonton? Bagaimana ritme perpindahan antar adegannya (pacing)?
                2. **Gaya Editing & Grafis**: Bedah penggunaan teks di layar (captions), efek transisi, b-roll, warna, dan elemen grafis yang mereka pakai. Apa rahasia yang bikin video ini tidak membosankan?
                3. **Sound Design & Audio**: Bagaimana peran musik latar (BGM) dan efek suara (SFX) dalam membangun emosi penonton di video ini?
                4. **Rumus Sukses Yang Bisa Dicontek**: Berikan 3 poin penting dari gaya video ini yang wajib ditiru atau dikembangkan agar retensi penonton melesat tinggi.
                
                Jawab langsung ke inti poinnya, profesional, tanpa basa-basi teori.
                """
                
                response = model.generate_content([prompt, video_file])
                
                st.success("Analisis Video Selesai!")
                st.markdown("### 📋 Hasil Laporan Bedah Video Menyeluruh:")
                st.write(response.text)
                
                # Hapus file dari server Google setelah selesai biar bersih
                genai.delete_file(video_file.name)

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses video: {str(e)}")
        
        finally:
            # Bersihkan file sampah di server lokal Streamlit
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

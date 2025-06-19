import nest_asyncio
import streamlit as st
import streamlit.components.v1 as components
from datetime import timedelta
import sys
import os
import asyncio
import json
import whisper
import tempfile
import requests
import urllib.parse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import character_tropes_generator

nest_asyncio.apply()

def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

def format_size(size_bytes):
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.2f} MB"

def clean_title(title):
    clean = title.replace('File:', '').rsplit('.', 1)[0]
    return clean

def format_timestamp(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def convert_srt_to_vtt(srt_content):
    return "WEBVTT\n\n" + srt_content.replace(',', '.')

def generate_english_subtitles(video_url):
    model = whisper.load_model("base")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_path = tmp_video.name
            headers = {"User-Agent": "Mozilla/5.0"}
            video_bytes = requests.get(video_url, headers=headers).content
            tmp_video.write(video_bytes)
        result = model.transcribe(tmp_path, task='translate')
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
    detected_language = result.get('language', 'unknown')
    subtitles = []
    for i, seg in enumerate(result['segments']):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        subtitles.append(f"{i+1}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n")

        return "\n".join(subtitles), detected_language

async def get_trope_analysis(movie_title, description_url):
    try:
        return await character_tropes_generator(movie_title, description_url)
    except Exception as e:
        return json.dumps({
            "film_title": movie_title,
            "estimated_year": "Unknown",
            "estimated_genre": "Drama",
            "plot_available": False,
            "tropes_identified": [{
                "trope_name": "Classic Cinema",
                "description": "Elements typical of early filmmaking and storytelling",
                "confidence_score": 5,
                "evidence": f"Analysis unavailable due to error: {str(e)}"
            }],
            "thematic_elements": ["Classic Cinema", "Historical Significance"],
            "analysis_summary": f"Unable to perform detailed analysis of {movie_title}. This appears to be a classic film from the public domain collection."
        }, indent=2)

st.set_page_config(page_title="Video Player - Wikimedia Commons", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

if 'selected_video' not in st.session_state or not st.session_state.selected_video:
    st.error("No video selected. Please select a video from the browse page.")
    if st.button("Back to Browse"):
        st.switch_page("streamlit_frontend.py")
else:
    video = st.session_state.selected_video
    movie_title = clean_title(video["canonicaltitle"])

    subtitle_key = f'subtitles_{video["pageid"]}'
    lang_key = f'language_{video["pageid"]}'
    if subtitle_key not in st.session_state:
        st.session_state[subtitle_key] = None
        st.session_state[lang_key] = None


    st.markdown(f"<h1 style='color:#dc2626;text-align:center;'>{movie_title}</h1>", unsafe_allow_html=True)

    if st.session_state[subtitle_key]:
        vtt_subtitles = convert_srt_to_vtt(st.session_state[subtitle_key])
        st.video(video['url'], subtitles=vtt_subtitles)
    else:
        st.video(video['url'])

    st.markdown("""</div>""", unsafe_allow_html=True)


        st.markdown("### 📊 Video Metadata")
        st.markdown(f"""
        <div style="background: rgba(30,30,30,0.6); padding:1rem; border-radius:12px; backdrop-filter: blur(8px);">
            <p><strong>Resolution:</strong> {video['width']}×{video['height']}</p>
            <p><strong>Duration:</strong> {format_duration(video['duration'])}</p>
            <p><strong>Size:</strong> {format_size(video['size'])}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔗 Related Links")
        st.markdown(f"- [📘 View on Wikimedia]({video['descriptionurl']})")
        st.markdown(f"- [🎥 Direct Video URL]({video['url']})")

        st.markdown("### 📝 Subtitles")
        if st.session_state[subtitle_key]:
            if st.button("❌ Remove Subtitles"):
                st.session_state[subtitle_key] = None
                st.success("Subtitles removed.")
                st.rerun()
        else:
            if st.button("📝 Generate English Subtitles"):
                with st.spinner("Generating subtitles..."):
                    try:
                        subs, lang = generate_english_subtitles(video["url"])
                        st.session_state[subtitle_key] = subs
                        st.session_state[lang_key] = lang.upper()
                        st.success(f"Subtitles ready. Language: {lang.upper()}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate: {e}")

        st.markdown("### 🤖 AI Movie Analysis")
        analysis_key = f'analysis_{video["pageid"]}'
        if analysis_key not in st.session_state:
            st.session_state[analysis_key] = None
        if st.button("🔍 Analyze Movie Tropes"):
            with st.spinner("Analyzing..."):
                try:
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    analysis = loop.run_until_complete(get_trope_analysis(movie_title, video["descriptionurl"]))
                    st.session_state[analysis_key] = analysis
                    st.success("Analysis complete.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        ...
    if st.session_state[analysis_key]:
        try:
            data = json.loads(st.session_state[analysis_key])
            st.markdown("""
                <style>
                .analysis-layout {
                    background: rgba(20, 20, 20, 0.6);
                    padding: 2rem;
                    border-radius: 16px;
                    display: grid;
                    grid-template-columns: 200px 1fr;
                    gap: 2rem;
                    box-shadow: 0 0 20px rgba(255,0,0,0.1);
                    color: white;
                }
                .left-column {
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                }
                .left-column div {
                    background: rgba(255,255,255,0.07);
                    padding: 0.8rem;
                    border-radius: 10px;
                    text-align: center;
                    font-weight: bold;
                    backdrop-filter: blur(6px);
                }
                .right-column {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }
                .title {
                    font-size: 1.8rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                    color: #ff3333;
                    text-align: left;
                }
                .section-label {
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin: 0.5rem 0;
                    color: #f87171;
                    text-align: left;
                }
                .tropes-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 1rem;
                    max-height: 250px;
                    overflow-y: auto;
                    padding-right: 0.5rem;
                }
                .trope-card {
                    background: rgba(255,255,255,0.05);
                    padding: 1rem;
                    border-left: 5px solid #dc2626;
                    border-radius: 12px;
                    backdrop-filter: blur(4px);
                    text-align: justify;
                }
                .summary {
                    background: rgba(255,255,255,0.03);
                    padding: 1rem;
                    border-radius: 12px;
                    line-height: 1.6;
                    text-align: justify;
                    font-size: 0.95rem;
                }
                </style>
            """, unsafe_allow_html=True)

            tropes_html = ''.join([
                f"<div class='trope-card'><strong>{t['trope_name']}</strong><br>{t['description']}<br><small>Confidence: {t['confidence_score']}/10</small></div>"
                for t in data['tropes_identified']
            ])

            st.markdown(f"""
                <div class="analysis-layout">
                    <div class="left-column">
                        <div>🎞 <span class='section-label'>Year</span><br>{data['estimated_year']}</div>
                        <div>🎭 <span class='section-label'>Genre</span><br>{data['estimated_genre']}</div>
                        <div>🎨 <span class='section-label'>Themes</span><br>{' | '.join(data['thematic_elements'])}</div>
                    </div>
                    <div class="right-column">
                        <div class="title">{data['film_title']}</div>
                        <div class="section-label">🧠 Character Tropes</div>
                        <div class="tropes-grid">{tropes_html}</div>
                        <div class="section-label">📜 Summary</div>
                        <div class="summary">{data['analysis_summary']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.error("Failed to parse analysis.")
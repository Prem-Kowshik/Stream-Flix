# 01_Video_Player.py

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
    return f"{size_bytes / (1024 * 1024):.2f} MB"

def clean_title(title):
    return title.replace('File:', '').rsplit('.', 1)[0]

def format_timestamp(seconds):
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def convert_srt_to_vtt(srt_content):
    return "WEBVTT\n\n" + srt_content.replace(',', '.')

def generate_english_subtitles(video_url):
    model = whisper.load_model("base")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        headers = {"User-Agent": "Mozilla/5.0"}
        video_bytes = requests.get(video_url, headers=headers).content
        tmp_video.write(video_bytes)
        tmp_path = tmp_video.name

    result = model.transcribe(tmp_path, task='translate')
    os.remove(tmp_path)

    subtitles = [
        f"{i+1}\n{format_timestamp(s['start'])} --> {format_timestamp(s['end'])}\n{s['text'].strip()}\n"
        for i, s in enumerate(result['segments'])
    ]
    return "\n".join(subtitles), result.get('language', 'unknown')

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

# ---------- Streamlit App ----------
st.set_page_config("Video Player - Wikimedia Commons", page_icon="🎬", layout="wide")

if 'selected_video' not in st.session_state or not st.session_state.selected_video:
    st.error("No video selected. Please go back to browse.")
    if st.button("Back to Browse"):
        st.switch_page("streamlit_frontend.py")
    st.stop()

video = st.session_state.selected_video
movie_title = clean_title(video["canonicaltitle"])
subtitle_key = f'subtitles_{video["pageid"]}'
lang_key = f'language_{video["pageid"]}'
st.session_state.setdefault(subtitle_key, None)
st.session_state.setdefault(lang_key, None)

subtitle_track = ""
if st.session_state[subtitle_key]:
    vtt = convert_srt_to_vtt(st.session_state[subtitle_key])
    b64_subs = urllib.parse.quote(vtt)
    subtitle_uri = f"data:text/vtt;charset=utf-8,{b64_subs}"
    subtitle_track = f'<track label="English" kind="subtitles" srclang="en" src="{subtitle_uri}" default>'

video_html = f"""
<style>
.video-wrapper {{ display: flex; flex-direction: column; align-items: flex-start; width: 100%; padding-left: 2rem; font-family: 'Segoe UI', sans-serif; }}
.video-container {{ position: relative; max-width: 1080px; height: 600px; width: 100%; background: black; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3); }}
.video-container video {{ width: 100%; height: 100%; object-fit: contain; }}
.video-title {{ margin-top: 1rem; font-size: 2.5rem; font-weight: bold; color: #dc2626; text-shadow: 1px 1px 3px rgba(0,0,0,0.6); }}
.playback-select-wrapper {{ position: absolute; bottom: 60px; right: 20px; background: rgba(0,0,0,0.85); border-radius: 8px; padding: 6px 10px; color: white; }}
.playback-select-wrapper label {{ font-size: 14px; margin-right: 6px; }}
.playback-select-wrapper select {{ background: #dc2626; color: white; border: none; padding: 4px 8px; font-size: 14px; border-radius: 4px; }}
</style>
<div class="video-wrapper">
  <div class="video-container">
    <video id="customVideo" controls>
      <source src="{video['url']}" type="video/mp4">
      {subtitle_track}
    </video>
    <div class="playback-select-wrapper">
      <label for="speedSelector">Speed:</label>
      <select id="speedSelector" onchange="document.getElementById('customVideo').playbackRate = parseFloat(this.value);">
        <option value="0.25">0.25x</option>
        <option value="0.5">0.5x</option>
        <option value="0.75">0.75x</option>
        <option value="1.0" selected>1.0x</option>
        <option value="1.25">1.25x</option>
        <option value="1.5">1.5x</option>
        <option value="1.75">1.75x</option>
        <option value="2.0">2.0x</option>
      </select>
    </div>
  </div>
  <div class="video-title">{movie_title}</div>
</div>
"""
components.html(video_html, height=750)

# ----- Details -----
st.subheader("📊 Video Details")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Page ID", video["pageid"])
col2.metric("Resolution", f"{video['width']}×{video['height']}")
col3.metric("Duration", format_duration(video["duration"]))
col4.metric("Size", format_size(video["size"]))

# ----- Subtitles -----
st.subheader("📝 Generate English Subtitles")
if st.button("Generate English Subtitles"):
    with st.spinner("Translating audio..."):
        try:
            srt, lang = generate_english_subtitles(video["url"])
            st.session_state[subtitle_key] = srt
            st.session_state[lang_key] = lang.upper()
            st.success(f"✅ Detected: {lang.upper()} — Subtitles ready!")
            st.rerun()
        except Exception as e:
            st.error(f"Subtitle generation failed: {e}")

if st.session_state[subtitle_key]:
    st.info(f"🎧 Subtitles available — Original Language: {st.session_state.get(lang_key, 'N/A')}")
    st.download_button("⬇️ Download English Subtitles (.srt)", st.session_state[subtitle_key], f"{movie_title}_English.srt")

# ----- Tropes -----
st.markdown("---")
st.subheader("🤖 AI Movie Analysis")
analysis_key = f'analysis_{video["pageid"]}'
st.session_state.setdefault(analysis_key, None)

if st.button("🔍 Analyze Movie Tropes"):
    with st.spinner("Analyzing film themes..."):
        try:
            loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(get_trope_analysis(movie_title, video["descriptionurl"]))
            st.session_state[analysis_key] = analysis
            st.success("✅ Analysis complete")
        except Exception as e:
            st.error(f"Error: {e}")

if st.session_state[analysis_key]:
    try:
        trope_data = json.loads(st.session_state[analysis_key])
        tropes_html = ''.join(
            f'<div class="wikiflix-trope"><strong>{t["trope_name"]}</strong><br>{t["description"]}<br><em>Confidence: {t["confidence_score"]} / 10</em></div>'
            for t in trope_data['tropes_identified']
        )
        themes_html = ''.join(
            f'<span class="wikiflix-tag">{theme}</span>'
            for theme in trope_data['thematic_elements']
        )
        st.markdown(f"""
        <style>
        .wikiflix-info-box {{ background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(220, 38, 38, 0.3); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; }}
        .wikiflix-info-box h3 {{ color: #f87171; font-size: 20px; margin-bottom: 0.5rem; }}
        .wikiflix-trope {{ background-color: rgba(255, 255, 255, 0.03); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #f87171; }}
        .wikiflix-tag {{ background-color: rgba(252, 165, 165, 0.15); color: #fca5a5; padding: 0.3rem 0.6rem; margin: 0.2rem; border-radius: 6px; display: inline-block; font-size: 14px; }}
        </style>
        <div class="wikiflix-info-box">
          <h3>📋 Movie Information</h3>
          <p><strong>Title:</strong> {trope_data['film_title']}</p>
          <p><strong>Year:</strong> {trope_data['estimated_year']}</p>
          <p><strong>Genre:</strong> {trope_data['estimated_genre']}</p>
          <p><strong>Plot Available:</strong> {'Yes' if trope_data['plot_available'] else 'No'}</p>
        </div>
        <div class="wikiflix-info-box">
          <h3>🎭 Character Tropes</h3>
          {tropes_html}
        </div>
        <div class="wikiflix-info-box">
          <h3>🎨 Thematic Elements</h3>
          {themes_html}
        </div>
        <div class="wikiflix-info-box">
          <h3>📝 Summary</h3>
          <p>{trope_data['analysis_summary']}</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to display analysis: {e}")

# ----- Links -----
st.markdown("---")
st.subheader("🔗 External Links")
st.markdown(f"- 📙 [View on Wikimedia Commons]({video['descriptionurl']})")
st.markdown(f"- 🎬 [Direct Video URL]({video['url']})")

st.markdown("---")
if st.button("← Back to Browse"):
    st.switch_page("streamlit_frontend.py")

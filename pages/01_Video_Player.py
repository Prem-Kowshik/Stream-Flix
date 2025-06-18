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
import urllib.parse # Required for creating the subtitle Data URI
from streamlit.components.v1 import html


# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import character_tropes_generator

nest_asyncio.apply()

# --- UTILITY FUNCTIONS (No Changes) ---
def format_duration(seconds):
    """Convert seconds to human-readable format"""
    return str(timedelta(seconds=int(seconds)))

def format_size(size_bytes):
    """Convert bytes to MB"""
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.2f} MB"

def clean_title(title):
    """Remove 'File:' prefix and file extension from title"""
    clean = title.replace('File:', '')
    clean = clean.rsplit('.', 1)[0]
    return clean

def format_timestamp(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def convert_srt_to_vtt(srt_content):
    vtt_content = srt_content.replace(',', '.')
    return "WEBVTT\n\n" + vtt_content

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
    subtitles = [f"{i+1}\n{format_timestamp(s['start'])} --> {format_timestamp(s['end'])}\n{s['text'].strip()}\n" for i, s in enumerate(result['segments'])]
    return "\n".join(subtitles), detected_language

async def get_trope_analysis(movie_title, description_url):
    try:
        return await character_tropes_generator(movie_title, description_url)
    except Exception as e:
        fallback_analysis = { "film_title": movie_title, "estimated_year": "Unknown", "estimated_genre": "Drama", "plot_available": False, "tropes_identified": [{"trope_name": "Classic Cinema", "description": "Elements typical of early filmmaking and storytelling", "confidence_score": 5, "evidence": f"Analysis unavailable due to error: {str(e)}"}], "thematic_elements": ["Classic Cinema", "Historical Significance"], "analysis_summary": f"Unable to perform detailed analysis of {movie_title}. This appears to be a classic film from the public domain collection." }
        return json.dumps(fallback_analysis, indent=2)

# ---- Streamlit App ----
st.set_page_config(page_title="Video Player - Wikimedia Commons", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

# # Custom CSS for video player page
# st.markdown("""
# <style>
#     /* Main theme colors */
#     .stApp {
#         background-color: #1a1a1a;
#         color: #ffffff;
#     }
    
#     /* Video player container */
#     .video-player-container {
#         background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
#         border: 2px solid #dc2626;
#         border-radius: 15px;
#         padding: 2rem;
#         margin-bottom: 2rem;
#         box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
#     }
    
#     /* Title styling */
#     h1 {
#         color: #dc2626 !important;
#         text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
#         text-align: center;
#         margin-bottom: 2rem !important;
#     }
    
#     /* Metric styling */
#     .metric-container {
#         background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
#         border: 1px solid #dc2626;
#         border-radius: 10px;
#         padding: 1rem;
#         text-align: center;
#         box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
#     }
    
#     /* Button styling */
#     .stButton > button {
#         background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
#         color: white;
#         border: none;
#         border-radius: 10px;
#         padding: 0.5rem 1rem;
#         font-weight: bold;
#         transition: all 0.3s ease;
#         box-shadow: 0 4px 10px rgba(220, 38, 38, 0.3);
#     }
    
#     .stButton > button:hover {
#         background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
#         transform: translateY(-2px);
#         box-shadow: 0 6px 15px rgba(220, 38, 38, 0.4);
#     }
    
#     /* Video player styling */
#     .stVideo {
#         border-radius: 15px;
#         overflow: hidden;
#         box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
#     }
    
#     /* AI Analysis container */
#     .ai-analysis {
#         background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
#         border: 2px solid #dc2626;
#         border-radius: 15px;
#         padding: 1.5rem;
#         margin: 2rem 0;
#         box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
#     }
    
#     .ai-analysis h2 {
#         color: #dc2626 !important;
#         margin-bottom: 1rem !important;
#     }
    
#     .ai-analysis p {
#         color: #ffffff;
#         line-height: 1.6;
#         font-size: 1.1rem;
#     }
    
#     /* Trope card styling */
#     .trope-card {
#         background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
#         border: 1px solid #dc2626;
#         border-radius: 10px;
#         padding: 1rem;
#         margin: 1rem 0;
#         box-shadow: 0 4px 10px rgba(220, 38, 38, 0.2);
#     }
    
#     .trope-card h4 {
#         color: #dc2626 !important;
#         margin-bottom: 0.5rem !important;
#     }
    
#     /* Error message styling */
#     .error-message {
#         background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
#         border: 1px solid #dc2626;
#         border-radius: 10px;
#         padding: 1rem;
#         margin: 1rem 0;
#         color: white;
#     }
    
#     /* Success message styling */
#     .success-message {
#         background: linear-gradient(135deg, #166534 0%, #15803d 100%);
#         border: 1px solid #22c55e;
#         border-radius: 10px;
#         padding: 1rem;
#         margin: 1rem 0;
#         color: white;
#     }
    
#     /* Loading animation */
#     .loading {
#         display: inline-block;
#         width: 20px;
#         height: 20px;
#         border: 3px solid rgba(220, 38, 38, 0.3);
#         border-radius: 50%;
#         border-top-color: #dc2626;
#         animation: spin 1s ease-in-out infinite;
#     }
    
#     @keyframes spin {
#         to { transform: rotate(360deg); }
#     }
# </style>
# """, unsafe_allow_html=True)

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

    with st.container():
        st.markdown("""
        <style>
            .video-container {
                background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
                border: 2px solid #dc2626;
                border-radius: 15px;
                padding: 2rem;
                box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="video-container">', unsafe_allow_html=True)

    # Playback speed selector
    # speed = st.selectbox("Select playback speed", [0.25, 0.5, 1.0, 1.25, 1.5, 2.0], index=2)

    subtitle_track = ""
    if st.session_state[subtitle_key]:
        vtt_subs = convert_srt_to_vtt(st.session_state[subtitle_key])
        b64_subs = urllib.parse.quote(vtt_subs)
        subtitle_uri = f"data:text/vtt;charset=utf-8,{b64_subs}"
        subtitle_track = f'<track label="English" kind="subtitles" srclang="en" src="{subtitle_uri}" default>'

    video_url = video['url']
    custom_player = f"""
    <div style="background: linear-gradient(135deg, #2d2d2d, #1a1a1a); padding: 1rem; border-radius: 15px; border: 2px solid #dc2626; box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3); max-width: 100%; margin: auto;">
    <div style="position: relative; width: 100%; padding-top: 56.25%; border-radius: 15px; overflow: hidden;">
        <video id="videoPlayer" controls style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 15px;">
        <source src="{video_url}" type="video/mp4">
        {subtitle_track}
        Your browser does not support the video tag.
        </video>
    </div>
    </div>
    """

    html(custom_player, height=650)  # Increase slightly if you want margin below player


    st.markdown("</div>", unsafe_allow_html=True)

   # Technical details
    st.subheader("📊 Video Details")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-container"><strong>🆔 Page ID</strong><br>{video["pageid"]}</div>', 
                  unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><strong>📐 Resolution</strong><br>{video["width"]}×{video["height"]}</div>', 
                  unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><strong>⏱️ Duration</strong><br>{format_duration(video["duration"])}</div>', 
                  unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-container"><strong>📁 Size</strong><br>{format_size(video["size"])}</div>', 
                  unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Subtitle UI is added
    st.subheader("📝 Generate English Subtitles")
    if st.button("Generate English Subtitles", key="generate_subtitles_btn"):
        with st.spinner("Translating audio to English... This may take a few minutes..."):
            try:
                subtitles_srt, detected_lang = generate_english_subtitles(video["url"])
                st.session_state[subtitle_key] = subtitles_srt
                st.session_state[lang_key] = detected_lang.upper()
                st.success(f"✅ Detected language: {detected_lang.upper()}. Subtitles are ready!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate subtitles: {e}")

    if st.session_state[subtitle_key]:
        lang_info = f"Original Language Detected: {st.session_state.get(lang_key, 'N/A')}"
        st.info(f"Subtitles are active on the video player. {lang_info}")
        st.download_button(
            label="Download English Subtitles (.srt)",
            data=st.session_state[subtitle_key],
            file_name=f"{movie_title}_English.srt",
            mime="text/plain",
            key="subtitle_download_btn")
    
    # AI Analysis Section
    st.markdown("---")
    st.subheader("🤖 AI Movie Analysis")
    
    # Initialize session state for analysis if not exists
    analysis_key = f'analysis_{video["pageid"]}'
    if analysis_key not in st.session_state: st.session_state[analysis_key] = None
    
    # Button to trigger analysis
    if st.button("🔍 Analyze Movie Tropes", key="analyze_tropes_btn"):
        with st.spinner("🎭 Analyzing movie tropes and themes..."):
            try:
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                trope_analysis = loop.run_until_complete(get_trope_analysis(movie_title, video["descriptionurl"]))
                st.session_state[analysis_key] = trope_analysis
                st.success("✅ Analysis completed successfully!")
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}"); st.session_state[analysis_key] = None
    
    # Display analysis if available
    if st.session_state[analysis_key]:
        try:
            trope_data = json.loads(st.session_state[analysis_key])
            st.markdown("<h3>📋 Movie Information</h3>", unsafe_allow_html=True); st.markdown(f"**Film Title:** {trope_data['film_title']}  \n**Estimated Year:** {trope_data['estimated_year']}  \n**Genre:** {trope_data['estimated_genre']}  \n**Plot Available:** {'Yes' if trope_data['plot_available'] else 'No'}")
            st.markdown("<h3>🎭 Character Tropes</h3>", unsafe_allow_html=True)
            for trope in trope_data['tropes_identified']: st.markdown(f'<div class="trope-card"><h4>{trope["trope_name"]}</h4><p><strong>Description:</strong> {trope["description"]}<br><strong>Confidence:</strong> {trope["confidence_score"]}/10 | <strong>Evidence:</strong> {trope["evidence"]}</p></div>', unsafe_allow_html=True)
            st.markdown("<h3>🎨 Thematic Elements</h3>", unsafe_allow_html=True); st.markdown(" • ".join([f"`{theme}`" for theme in trope_data['thematic_elements']]))
            st.markdown("<h3>📝 Analysis Summary</h3>", unsafe_allow_html=True); st.write(trope_data['analysis_summary'])
        except Exception as e:
            st.error(f"Error displaying analysis: {str(e)}"); st.code(st.session_state[analysis_key], language='json')
    else: 
        st.info("Click the 'Analyze Movie Tropes' button above to get AI-powered insights.")

    # Links
    st.markdown("---")
    st.subheader("🔗 External Links")
    col_link1, col_link2 = st.columns(2)
    with col_link1: st.markdown(f'<a href="{video["descriptionurl"]}" target="_blank" style="display: block; width: 100%; text-align: center; padding: 0.75rem 1rem; background: linear-gradient(135deg, #4b5563 0%, #1f2937 100%); color: white; text-decoration: none; border-radius: 10px; font-weight: bold;">📚 View on Wikimedia Commons</a>', unsafe_allow_html=True)
    with col_link2: st.markdown(f'<a href="{video["url"]}" target="_blank" style="display: block; width: 100%; text-align: center; padding: 0.75rem 1rem; background: linear-gradient(135deg, #4b5563 0%, #1f2937 100%); color: white; text-decoration: none; border-radius: 10px; font-weight: bold;">🎬 Direct Video URL</a>', unsafe_allow_html=True)
    
    # Back Button
    st.markdown("---")
    if st.button("← Back to Browse", type="primary", key="back_to_browse_btn"): st.switch_page("streamlit_frontend.py")

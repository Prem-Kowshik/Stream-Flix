import nest_asyncio 
import streamlit as st
from datetime import timedelta
import sys
import os
import asyncio
import json
import whisper
import tempfile
import requests

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import character_tropes_generator

nest_asyncio.apply()

def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

def format_size(size_bytes):
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.2f} MB"

def clean_title(title):
    clean = title.replace('File:', '')
    clean = clean.rsplit('.', 1)[0]
    return clean

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def convert_srt_to_vtt(srt_content):
    """
    Converts subtitle content from SRT format to VTT format.
    The main difference is the timestamp separator (',' vs '.') and the WEBVTT header.
    """
    # Replace the comma decimal separator with a period
    vtt_content = srt_content.replace(',', '.')
    # Add the WEBVTT header
    return "WEBVTT\n\n" + vtt_content

def generate_subtitles(video_url):
    """
    Downloads a video, transcribes it, and returns SRT formatted subtitles.
    """
    model = whisper.load_model("base")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_path = tmp_video.name
            headers = {"User-Agent": "Mozilla/5.0"}
            video_bytes = requests.get(video_url, headers=headers).content
            tmp_video.write(video_bytes)
        
        result = model.transcribe(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    subtitles = []
    for i, seg in enumerate(result['segments']):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        subtitles.append(f"{i+1}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n")
    return "\n".join(subtitles)

async def get_trope_analysis(movie_title, description_url):
    # (No changes to this function)
    try:
        return await character_tropes_generator(movie_title, description_url)
    except Exception as e:
        fallback_analysis = {
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
        }
        return json.dumps(fallback_analysis, indent=2)

# ---- Streamlit App ----
st.set_page_config(page_title="Video Player - Wikimedia Commons", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

if 'selected_video' not in st.session_state or not st.session_state.selected_video:
    st.error("No video selected. Please select a video from the browse page.")
    if st.button("Back to Browse"):
        st.switch_page("streamlit_frontend.py")
else:
    video = st.session_state.selected_video
    movie_title = clean_title(video["canonicaltitle"])

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
        # speed = st.selectbox("🎞️ Playback speed", [0.25, 0.5, 1.0, 1.25, 1.5, 2.0], index=2)

        from streamlit.components.v1 import html

        video_url = video['url']
        # Use a responsive 16:9 aspect ratio container with CSS
        custom_player = f"""
        <div style="background: linear-gradient(135deg, #2d2d2d, #1a1a1a); padding: 1rem; border-radius: 15px; border: 2px solid #dc2626; box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3); max-width: 960px; margin: auto;">
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 15px;">
            <video id="videoPlayer" controls style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 15px;">
            <source src="{video['url']}" type="video/mp4">
            Your browser does not support the video tag.
            </video>
        </div>
        
        </div>
        """

        from streamlit.components.v1 import html
        html(custom_player, height=500)

        st.markdown("</div>", unsafe_allow_html=True)

    # Use a unique key for session state based on the video's page ID
    subtitle_key = f'subtitles_{video["pageid"]}'
    if subtitle_key not in st.session_state:
        st.session_state[subtitle_key] = None

    st.markdown(f'<h1>{movie_title}</h1>', unsafe_allow_html=True)
    
    # --- MODIFIED VIDEO DISPLAY LOGIC ---
    # Display the video with subtitles if they exist in the session state
    if st.session_state[subtitle_key]:
        vtt_subtitles = convert_srt_to_vtt(st.session_state[subtitle_key])
        st.video(video['url'], subtitles=vtt_subtitles)
    else:
        # Otherwise, display the video without subtitles
        st.video(video['url'])
    # --- END OF MODIFIED LOGIC ---


    st.subheader("📊 Video Details")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'🆔 Page ID\n{video["pageid"]}')
    with col2:
        st.markdown(f'📐 Resolution\n{video["width"]}×{video["height"]}')
    with col3:
        st.markdown(f'⏱️ Duration\n{format_duration(video["duration"])}')
    with col4:
        st.markdown(f'📁 Size\n{format_size(video["size"])}')

    st.subheader("📝 Auto-Generate Subtitles")

    if st.button("Generate Subtitles", key="generate_subtitles_btn", disabled=(st.session_state[subtitle_key] is not None)):
        with st.spinner("Transcribing... This may take a few minutes..."):
            try:
                # Generate SRT content
                subtitles_srt = generate_subtitles(video["url"])
                # Store the SRT content in session state
                st.session_state[subtitle_key] = subtitles_srt
                st.success("✅ Subtitles generated successfully! Refreshing video with captions...")
                # Rerun to update the video player with the new subtitles
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate subtitles: {e}")
                st.session_state[subtitle_key] = None

    # Conditionally display the download button if subtitles exist
    if st.session_state[subtitle_key]:
        st.info("Subtitles are now displayed on the video player. You can also download them.")
        st.download_button(
            label="Download Subtitles (.srt)",
            data=st.session_state[subtitle_key], # Download the original SRT format
            file_name=f"{movie_title}.srt",
            mime="text/plain",
            key="subtitle_download_btn"
        )

    st.markdown("---") # Replaces st.write("") for better formatting

    # --- AI ANALYSIS SECTION (No changes) ---
    st.subheader("🤖 AI Movie Analysis")
    analysis_key = f'analysis_{video["pageid"]}'
    if analysis_key not in st.session_state:
        st.session_state[analysis_key] = None

    if st.button("🔍 Analyze Movie Tropes", key="analyze_tropes_btn"):
        with st.spinner("🎭 Analyzing movie tropes and themes..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                trope_analysis = loop.run_until_complete(get_trope_analysis(movie_title, video["descriptionurl"]))
                st.session_state[analysis_key] = trope_analysis
                st.success("✅ Analysis completed successfully!")
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.session_state[analysis_key] = None

    if st.session_state[analysis_key]:
        try:
            trope_data = json.loads(st.session_state[analysis_key])
            st.markdown("### 📋 Movie Information")
            st.markdown(f"**Film Title:** {trope_data['film_title']}  \n**Estimated Year:** {trope_data['estimated_year']}  \n**Genre:** {trope_data['estimated_genre']}  \n**Plot Available:** {'Yes' if trope_data['plot_available'] else 'No'}")
            st.subheader("🎭 Character Tropes")
            for trope in trope_data['tropes_identified']:
                st.markdown(f"**{trope['trope_name']}**\n- Description: {trope['description']}\n- Confidence Score: {trope['confidence_score']}/10\n- Evidence: {trope['evidence']}")
            st.subheader("🎨 Thematic Elements")
            st.markdown("**Themes:** " + " • ".join(trope_data['thematic_elements']))
            st.subheader("📝 Analysis Summary")
            st.write(trope_data['analysis_summary'])
        except Exception as e:
            st.error(f"Error displaying analysis: {str(e)}")
            st.code(st.session_state[analysis_key], language='json')
    else:
        st.info("Click the 'Analyze Movie Tropes' button above to get AI-powered insights.")

    st.markdown("---")

    st.subheader("📄 Additional Information")
    st.write(f"**Original Title:** {video['title']}")
    st.write(f"**Canonical Title:** {video['canonicaltitle']}")

    st.subheader("🔗 External Links")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        st.markdown(f"[📚 View on Wikimedia Commons]({video['descriptionurl']})")
    with col_link2:
        st.markdown(f"[🎬 Direct Video URL]({video['url']})")

    st.markdown("---")
    if st.button("← Back to Browse", type="primary", key="back_to_browse_btn"):
        st.switch_page("streamlit_frontend.py")
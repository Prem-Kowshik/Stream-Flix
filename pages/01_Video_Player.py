import streamlit as st
from datetime import timedelta
import sys
import os
import asyncio
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import character_tropes_generator

def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

def format_size(size_bytes):
    return f"{size_bytes / (1024 * 1024):.2f} MB"

def clean_title(title):
    return title.replace('File:', '').rsplit('.', 1)[0]

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
            "analysis_summary": f"Unable to analyze {movie_title}. Likely a classic film."
        }, indent=2)

# Page setup
st.set_page_config(page_title="Video Player - Wikimedia Commons", page_icon="🎬", layout="centered")

# Load video from session state
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

    # Video details
    st.subheader("📊 Video Details")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🆔 Page ID", video["pageid"])
    with col2:
        st.metric("📐 Resolution", f'{video["width"]}×{video["height"]}')
    with col3:
        st.metric("⏱️ Duration", format_duration(video["duration"]))
    with col4:
        st.metric("📁 Size", format_size(video["size"]))

    # AI Analysis section
    st.markdown('<div style="margin-top:2rem;"></div>', unsafe_allow_html=True)
    st.subheader("🤖 AI Movie Analysis")

    if f'analysis_{video["pageid"]}' not in st.session_state:
        st.session_state[f'analysis_{video["pageid"]}'] = None

    if st.button("🔍 Analyze Movie Tropes"):
        with st.spinner("Analyzing movie tropes..."):
            try:
                analysis = asyncio.run(get_trope_analysis(movie_title, video["descriptionurl"]))
                st.session_state[f'analysis_{video["pageid"]}'] = analysis
                st.success("✅ Analysis completed.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    analysis_data = st.session_state.get(f'analysis_{video["pageid"]}')
    if analysis_data:
        try:
            trope_data = json.loads(analysis_data)

            st.markdown("### 📋 Movie Info")
            st.write(f"**Film Title:** {trope_data['film_title']}")
            st.write(f"**Year:** {trope_data['estimated_year']}")
            st.write(f"**Genre:** {trope_data['estimated_genre']}")
            st.write(f"**Plot Available:** {'Yes' if trope_data['plot_available'] else 'No'}")

            st.subheader("🎭 Character Tropes")
            for trope in trope_data['tropes_identified']:
                st.markdown(f"""<div style='border:1px solid #dc2626; border-radius:10px; padding:10px; margin-bottom:10px; background:#2d2d2d'>
                <h4 style='color:#dc2626'>{trope['trope_name']}</h4>
                <p><strong>Description:</strong> {trope['description']}</p>
                <p><strong>Confidence:</strong> {trope['confidence_score']}/10</p>
                <p><strong>Evidence:</strong> {trope['evidence']}</p>
                </div>""", unsafe_allow_html=True)

            st.subheader("🎨 Themes")
            st.markdown(f"**{', '.join(trope_data['thematic_elements'])}**")

            st.subheader("📝 Summary")
            st.write(trope_data['analysis_summary'])

        except Exception:
            st.error("❌ Failed to parse analysis.")

    st.subheader("📄 Additional Info")
    st.write(f"**Original Title:** {video['title']}")
    st.write(f"**Canonical Title:** {video['canonicaltitle']}")

    st.subheader("🔗 Links")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        st.markdown(f"[📚 Wikimedia Commons]({video['descriptionurl']})")
    with col_link2:
        st.markdown(f"[🎬 Direct Video URL]({video['url']})")

    st.markdown("___")
    if st.button("← Back to Browse"):
        st.switch_page("streamlit_frontend.py")

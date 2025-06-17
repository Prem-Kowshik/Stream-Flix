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


# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import character_tropes_generator

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

async def get_trope_analysis(movie_title, description_url):
    """Async wrapper for trope analysis"""
    try:
        return await character_tropes_generator(movie_title, description_url)
    except Exception as e:
        fallback_analysis = {
            "film_title": movie_title,
            "estimated_year": "Unknown",
            "estimated_genre": "Drama",
            "plot_available": False,
            "tropes_identified": [
                {
                    "trope_name": "Classic Cinema",
                    "description": "Elements typical of early filmmaking and storytelling",
                    "confidence_score": 5,
                    "evidence": f"Analysis unavailable due to error: {str(e)}"
                }
            ],
            "thematic_elements": ["Classic Cinema", "Historical Significance"],
            "analysis_summary": f"Unable to perform detailed analysis of {movie_title}. This appears to be a classic film from the public domain collection."
        }
        return json.dumps(fallback_analysis, indent=2)

logging.basicConfig(level=logging.DEBUG)
logging.debug("Page Icon Removed")

title = "Video Player - Wikimedia Commons"
st.set_page_config(
    page_title="Video Player - Wikimedia Commons",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for video player page
st.markdown("""
<style>
    /* Main theme colors */
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    /* Video player container */
    .video-player-container {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        border: 2px solid #dc2626;
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
    }
    
    /* Title styling */
    h1 {
        color: #dc2626 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        text-align: center;
        margin-bottom: 2rem !important;
    }
    
    /* Metric styling */
    .metric-container {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        border: 1px solid #dc2626;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(220, 38, 38, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(220, 38, 38, 0.4);
    }
    
    /* Video player styling */
    .stVideo {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
    }
    
    /* AI Analysis container */
    .ai-analysis {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        border: 2px solid #dc2626;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
    }
    
    .ai-analysis h2 {
        color: #dc2626 !important;
        margin-bottom: 1rem !important;
    }
    
    .ai-analysis p {
        color: #ffffff;
        line-height: 1.6;
        font-size: 1.1rem;
    }
    
    /* Trope card styling */
    .trope-card {
        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
        border: 1px solid #dc2626;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 10px rgba(220, 38, 38, 0.2);
    }
    
    .trope-card h4 {
        color: #dc2626 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Error message styling */
    .error-message {
        background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
        border: 1px solid #dc2626;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: white;
    }
    
    /* Success message styling */
    .success-message {
        background: linear-gradient(135deg, #166534 0%, #15803d 100%);
        border: 1px solid #22c55e;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: white;
    }
    
    /* Loading animation */
    .loading {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(220, 38, 38, 0.3);
        border-radius: 50%;
        border-top-color: #dc2626;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

if 'selected_video' not in st.session_state or not st.session_state.selected_video:
    st.error("No video selected. Please select a video from the browse page.")
    if st.button("Back to Browse"):
        st.switch_page("streamlit_frontend.py")
else:
    video = st.session_state.selected_video
    movie_title = clean_title(video["canonicaltitle"])

    st.markdown(f'<h1>{movie_title}</h1>', unsafe_allow_html=True)
    st.markdown('<div class="video-player-container">', unsafe_allow_html=True)

    # Playback speed selector
    speed = st.selectbox("Select playback speed", [0.25, 0.5, 1.0, 1.25, 1.5, 2.0], index=2)


    # Custom HTML5 video player with speed control
    video_html = f"""
    <video id=\"customVideo\" width=\"100%\" height=\"auto\" controls>
      <source src=\"{video['url']}\" type=\"video/mp4\">
      Your browser does not support the video tag.
    </video>
    <script>
      var video = document.getElementById(\"customVideo\");
      video.playbackRate = {speed};
    </script>
    """
    components.html(video_html, height=400)

    st.markdown("""</div>""", unsafe_allow_html=True)

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
    
    # AI Analysis Section
    st.markdown('<div class="ai-analysis">', unsafe_allow_html=True)
    st.subheader("🤖 AI Movie Analysis")
    
    # Initialize session state for analysis if not exists
    if f'analysis_{video["pageid"]}' not in st.session_state:
        st.session_state[f'analysis_{video["pageid"]}'] = None
    
    # Button to trigger analysis
    if st.button("🔍 Analyze Movie Tropes", type="primary"):
        with st.spinner("🎭 Analyzing movie tropes and themes..."):
            try:
                # Run async function
                trope_analysis = asyncio.run(get_trope_analysis(movie_title, video["descriptionurl"]))
                st.session_state[f'analysis_{video["pageid"]}'] = trope_analysis
                st.success("✅ Analysis completed successfully!")
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.session_state[f'analysis_{video["pageid"]}'] = None
    
    # Display analysis if available
    if st.session_state[f'analysis_{video["pageid"]}']:
        try:
            trope_data = json.loads(st.session_state[f'analysis_{video["pageid"]}'])
            
            # Display movie metadata
            st.markdown("### 📋 Movie Information")
            st.markdown(f"""
            **Film Title:** {trope_data['film_title']}  
            **Estimated Year:** {trope_data['estimated_year']}  
            **Genre:** {trope_data['estimated_genre']}  
            **Plot Available:** {'Yes' if trope_data['plot_available'] else 'No'}
            """)
            
            # Display tropes
            st.subheader("🎭 Character Tropes")
            for trope in trope_data['tropes_identified']:
                st.markdown(f"""
                <div class="trope-card">
                    <h4>{trope['trope_name']}</h4>
                    <p><strong>Description:</strong> {trope['description']}</p>
                    <p><strong>Confidence Score:</strong> {trope['confidence_score']}/10</p>
                    <p><strong>Evidence:</strong> {trope['evidence']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Display thematic elements
            st.subheader("🎨 Thematic Elements")
            theme_tags = " • ".join(trope_data['thematic_elements'])
            st.markdown(f"**Themes:** {theme_tags}")
            
            # Display analysis summary
            st.subheader("📝 Analysis Summary")
            st.write(trope_data['analysis_summary'])
            
        except json.JSONDecodeError as e:
            st.markdown('<div class="error-message">❌ Error parsing analysis data. Please try running the analysis again.</div>', 
                      unsafe_allow_html=True)
        except KeyError as e:
            st.markdown('<div class="error-message">❌ Incomplete analysis data received. Please try again.</div>', 
                      unsafe_allow_html=True)
    else:
        st.info("Click the 'Analyze Movie Tropes' button above to get AI-powered insights about this film's characters, themes, and storytelling elements.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional information
    st.subheader("📄 Additional Information")
    st.write(f"**Original Title:** {video['title']}")
    st.write(f"**Canonical Title:** {video['canonicaltitle']}")
    
    # Links
    st.subheader("🔗 External Links")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        st.markdown(f"[📚 View on Wikimedia Commons]({video['descriptionurl']})")
    with col_link2:
        st.markdown(f"[🎬 Direct Video URL]({video['url']})")
    
    # Back button
    st.write("")  # Spacing
    if st.button("← Back to Browse", type="primary"):
        st.switch_page("streamlit_frontend.py")

import streamlit as st
from datetime import timedelta
import sys
import os
import asyncio
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import character_tropes_generator, analyze_multiple_movies

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

# Set up the page
st.set_page_config(
    page_title="Movie Details - Wikimedia Commons",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for movie details page
st.markdown("""
<style>
    /* Main theme colors */
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    /* Movie details container */
    .movie-details-container {
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

# Check if video is selected
if 'selected_video' not in st.session_state or not st.session_state.selected_video:
    st.error("No movie selected. Please select a movie from the browse page.")
    if st.button("← Back to Browse"):
        st.switch_page("streamlit_frontend.py")
else:
    video = st.session_state.selected_video
    movie_title = clean_title(video["canonicaltitle"])
    
    # Movie title
    st.markdown(f'<h1>{movie_title}</h1>', unsafe_allow_html=True)
    
    # Movie details container
    st.markdown('<div class="movie-details-container">', unsafe_allow_html=True)
    
    # Basic info
    st.subheader("📋 Basic Information")
    st.write(f"**Original Title:** {video['title']}")
    st.write(f"**Canonical Title:** {video['canonicaltitle']}")
    st.write(f"**Page ID:** {video['pageid']}")
    
    # Watch button
    if st.button("🎬 Watch Full Video", type="primary"):
        st.switch_page("pages/01_Video_Player.py")
    
    # Technical details
    st.subheader("🔧 Technical Details")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-container"><strong>📐 Resolution</strong><br>{video["width"]}×{video["height"]}</div>', 
                  unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><strong>⏱️ Duration</strong><br>{format_duration(video["duration"])}</div>', 
                  unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><strong>📁 Size</strong><br>{format_size(video["size"])}</div>', 
                  unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-container"><strong>🔗 Links</strong><br><a href="{video["descriptionurl"]}" target="_blank">Wiki Page</a><br><a href="{video["url"]}" target="_blank">Direct Video</a></div>', 
                  unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # AI Analysis Section
    st.markdown('<div class="ai-analysis">', unsafe_allow_html=True)
    st.subheader("🤖 AI Movie Analysis")
    
    # Get trope analysis
    with st.spinner("Analyzing movie tropes..."):
        try:
            # Create an event loop for the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = character_tropes_generator(movie_title, video["descriptionurl"])
            trope_analysis = loop.run_until_complete(response)
            loop.close()
            
            trope_data = json.loads(trope_analysis)
            
            # Display movie metadata
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
            st.write(", ".join(trope_data['thematic_elements']))
            
            # Display analysis summary
            st.subheader("📝 Analysis Summary")
            st.write(trope_data['analysis_summary'])
            
        except json.JSONDecodeError as e:
            st.markdown('<div class="error-message">Error parsing AI response. The analysis may be incomplete or unavailable.</div>', 
                      unsafe_allow_html=True)
            st.error(f"JSON Error: {str(e)}")
        except Exception as e:
            st.markdown('<div class="error-message">Error analyzing movie tropes. Please try again later.</div>', 
                      unsafe_allow_html=True)
            st.error(f"Error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Back button
    st.write("")  # Spacing
    if st.button("← Back to Browse", type="primary"):
        st.switch_page("streamlit_frontend.py") 
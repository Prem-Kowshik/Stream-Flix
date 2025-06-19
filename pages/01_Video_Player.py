import streamlit as st
import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
import hashlib
import pickle
import pickle
from typing import Dict, Any, Optional, List
from functools import wraps
import logging as logger
import time


# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from genre_utils import main as get_genre_data


class CacheManager:
    """Advanced cache manager with multiple caching strategies"""
    
    def __init__(self):
        self.cache_dir = "cache_data"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _generate_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate a unique cache key based on function name and parameters"""
        # Create a string representation of args and kwargs
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def save_to_disk(self, key: str, data: Any, ttl_hours: int = 24) -> None:
        """Save data to disk with TTL"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
            expiry_time = datetime.now() + timedelta(hours=ttl_hours)
            
            cache_data = {
                'data': data,
                'expiry': expiry_time,
                'created': datetime.now()
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"Data cached to disk with key: {key}")
        except Exception as e:
            logger.error(f"Failed to save cache to disk: {e}")
    
    def load_from_disk(self, key: str) -> Optional[Any]:
        """Load data from disk if not expired"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            if datetime.now() > cache_data['expiry']:
                os.remove(cache_file)
                logger.info(f"Cache expired and removed: {key}")
                return None
            
            logger.info(f"Cache hit from disk: {key}")
            return cache_data['data']
            
        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}")
            return None
    def clear_disk_cache(self) -> int:
        """Clear all disk cache and return number of files removed"""
        try:
            files_removed = 0
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, filename))
                    files_removed += 1
            
            logger.info(f"Cleared {files_removed} cache files from disk")
            return files_removed
        except Exception as e:
            logger.error(f"Failed to clear disk cache: {e}")
            return 0

# Global cache manager instance
cache_manager = CacheManager()


#CACHING
def async_cache_with_session_state(ttl_minutes: int = 30):
    """
    Custom decorator for caching async functions with session state
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(func.__name__, *args, **kwargs)
            session_cache_key = f"cache_{func.__name__}_{cache_key}"
            
            # Check session state cache first
            if session_cache_key in st.session_state:
                cached_data = st.session_state[session_cache_key]
                cache_time = cached_data.get('timestamp', 0)
                ttl_seconds = ttl_minutes * 60
                
                if time.time() - cache_time < ttl_seconds:
                    logger.info(f"Session state cache hit: {func.__name__}")
                    return cached_data['data']
            
            # Check disk cache
            disk_data = cache_manager.load_from_disk(cache_key)
            if disk_data is not None:
                # Store in session state for faster access
                st.session_state[session_cache_key] = {
                    'data': disk_data,
                    'timestamp': time.time()
                }
                return disk_data
            
            # Execute function and cache result
            logger.info(f"Cache miss, executing function: {func.__name__}")
            result = await func(*args, **kwargs)
            # Store in both session state and disk
            cache_data = {
                'data': result,
                'timestamp': time.time()
            }
            st.session_state[session_cache_key] = cache_data
            cache_manager.save_to_disk(cache_key, result, ttl_hours=24)
            
            return result
        
        return wrapper
    return decorator

@async_cache_with_session_state(ttl_minutes=60)  # 1 hour cache
async def load_genre_data_cached():
    """
    Cached version of genre data loading with comprehensive error handling
    """
    try:
        with st.spinner("🎬 Loading and classifying movies by genre..."):
            # Add progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Fetching video data from Wikimedia Commons...")
            progress_bar.progress(25)
            
            # Call the actual genre classification function
            genre_data = await get_genre_data()
            progress_bar.progress(75)
            
            status_text.text("Processing classification results...")
            progress_bar.progress(100)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            return genre_data
            
    except Exception as e:
        logger.error(f"Error in load_genre_data_cached: {e}")
        st.error(f"Failed to load genre data: {str(e)}")
        return {}

# Set up the page
st.set_page_config(
    page_title="Genre Classification - Wikiflix OTT",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for genre classification page that matches the application theme
st.markdown("""
<style>
/* Main theme colors */
.stApp {
    background-color: #1a1a1a;
    color: #ffffff;
}

/* Genre container */
.genre-container {
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

/* Stats container */
.stats-container {
    background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
    border: 2px solid #dc2626;
    border-radius: 15px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.stat-item {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
    border-radius: 15px;
    border: 1px solid #dc2626;
    transition: all 0.3s ease;
}

.stat-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(220, 38, 38, 0.3);
}

.stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: #dc2626;
    display: block;
}

.stat-label {
    font-size: 0.9rem;
    color: #cccccc;
    margin-top: 0.5rem;
}

/* Movie card styling */
.movie-card {
    background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
    border: 1px solid #dc2626;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.movie-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(220, 38, 38, 0.4);
    border: 1px solid #ef4444;
}

.movie-title {
    color: #ffffff;
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    height: 2.8em;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
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

/* Genre section styling */
.genre-title {
    color: #dc2626 !important;
    font-size: 1.5rem !important;
    margin-top: 1rem !important;
    margin-bottom: 1rem !important;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #dc2626;
}

/* Button container */
.button-container {
    margin-top: auto;
    display: flex;
    gap: 0.5rem;
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

/* Error and Success message styling */
.error-message {
    background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
    border: 1px solid #dc2626;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
    color: white;
}

.success-message {
    background: linear-gradient(135deg, #166534 0%, #15803d 100%);
    border: 1px solid #22c55e;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state for genre data
if 'genre_data' not in st.session_state:
    st.session_state.genre_data = None

# Initialize session state for selected video (for navigation compatibility)
if 'selected_video' not in st.session_state:
    st.session_state.selected_video = None

# Page title
st.markdown('<h1>🎭 Genre Classification</h1>', unsafe_allow_html=True)

# Function to clean title (consistent with other pages)
def clean_title(title):
    """Remove 'File:' prefix and file extension from title"""
    clean = title.replace('File:', '')
    clean = clean.rsplit('.', 1)[0]
    return clean

# Function to create mock video object for compatibility with other pages
def create_video_object(movie):
    """Create a video object compatible with other pages from movie data"""
    return {
        'pageid': hash(movie['url']),  # Generate a consistent hash for pageid
        'title': movie['title'],
        'canonicaltitle': f"File:{movie['title']}.webm",  # Mock canonical title
        'url': movie['url'],
        'descriptionurl': movie['url'],
        'width': 1280,  # Default values
        'height': 720,
        'duration': 3600,  # Default 1 hour
        'size': 100000000  # Default 100MB
    }

# Load genre data button
if st.button("🔄 Load Genre Data") or st.session_state.genre_data:
    if st.session_state.genre_data is None:
        with st.spinner("🎬 Classifying movies by genre using AI. This may take a few minutes..."):
            try:
                # Call the main function from genre_utils.py to get genre data
                genre_data = asyncio.run(load_genre_data_cached())
                st.session_state.genre_data = genre_data
                st.success("✅ Genre classification completed successfully!")
                if genre_data:
                    st.success("✅ Genre classification completed successfully!")
                    st.balloons()
                else:
                    st.warning("⚠️ No data was loaded. Please check the genre_utils.py file.")
                    
            except Exception as e:
                logger.error(f"Error loading genre data: {e}")
                st.error(f"❌ Failed to load genre data: {str(e)}")
            
    
    # If we have genre data, display it
    if st.session_state.genre_data:
        genre_data = st.session_state.genre_data
        
        # Stats container
        total_movies = sum(len(movies) for movies in genre_data.values())
        total_genres = len(genre_data)
        
        st.markdown(f'''
        <div class="stats-container">
            <h3>📊 Genre Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">{total_movies}</span>
                    <div class="stat-label">Total Movies</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{total_genres}</span>
                    <div class="stat-label">Genres</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{total_movies/total_genres:.1f}</span>
                    <div class="stat-label">Avg. Movies per Genre</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{datetime.now().strftime('%d %b %Y')}</span>
                    <div class="stat-label">Last Updated</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Display each genre and its movies
        for genre, movies in genre_data.items():
            st.markdown(f'<div class="genre-container">', unsafe_allow_html=True)
            st.markdown(f'<h2 class="genre-title">{genre} ({len(movies)} movies)</h2>', unsafe_allow_html=True)
            
            # Create three columns for movie cards
            cols = st.columns(3)
            
            # Display movies in each genre
            for i, movie in enumerate(movies):
                col = cols[i % 3]
                with col:
                    st.markdown(f'''
                    <div class="movie-card">
                        <div class="movie-title">{movie["title"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📋 Details", key=f"details-{movie['title']}-{i}"):
                            # Create a video object for the session state
                            st.session_state.selected_video = create_video_object(movie)
                            st.switch_page("pages/02_Movie_Details.py")
                    with col2:
                        if st.button("▶️ Watch", key=f"watch-{movie['title']}-{i}"):
                            # Create a video object for the session state
                            st.session_state.selected_video = create_video_object(movie)
                            st.switch_page("pages/01_Video_Player.py")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Add a button to clear and refresh the data
        if st.button("🔄 Refresh Genre Data"):
            st.session_state.genre_data = None
            st.rerun()
            
    else:
        st.info("Click the 'Load Genre Data' button to classify movies by genre using AI.")
else:
    # Initial message when no data is loaded
    st.markdown('''
    <div class="genre-container">
        <h3>🎬 AI-Powered Genre Classification</h3>
        <p>This page uses Google Gemini AI to automatically classify movies from Wikimedia Commons into genres.
        Click the "Load Genre Data" button below to start the genre classification process.</p>
        <p>The AI will analyze each movie's title and metadata to categorize it into appropriate genres,
        allowing you to browse movies by genre categories.</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.info("Click the 'Load Genre Data' button to begin the AI-powered genre classification.")

# Back button at the bottom
if st.button("← Back to Browse", type="primary"):
    st.switch_page("Homepage.py")

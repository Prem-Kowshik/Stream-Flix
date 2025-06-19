import streamlit as st
import aiohttp
from backoff import expo, on_exception
import pandas as pd
from datetime import timedelta
import json
from response_testing import return_video_data
import asyncio
import random

async def main():
    # Set up the page
    st.set_page_config(
        page_title="StreamFlix",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Enhanced CSS with modern design elements

    # .video-thumbnail::before {
    #         content: '';
    #         position: absolute;
    #         top: 50%;
    #         left: 50%;
    #         width: 100px;
    #         height: 100px;
    #         background: var(--primary-red);
    #         border-radius: 50%;
    #         transform: translate(-50%, -50%);
    #         opacity: 0.1;
    #         animation: ripple 2s infinite;
    #     }
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Root variables for consistent theming */
        :root {
            --primary-red: #dc2626;
            --primary-red-dark: #991b1b;
            --primary-red-light: #ef4444;
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2d2d2d;
            --text-primary: #ffffff;
            --text-secondary: #cccccc;
            --text-muted: #888888;
            --border-color: #333333;
            --shadow-red: rgba(220, 38, 38, 0.3);
            --shadow-red-hover: rgba(220, 38, 38, 0.5);
        }
        
        /* Main theme colors */
        .stApp {
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
        }
        
        /* Hero section */
        .hero-section {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 50%, var(--bg-secondary) 100%);
            border: 2px solid var(--primary-red);
            border-radius: 20px;
            padding: 3rem 2rem;
            margin-bottom: 3rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 50px var(--shadow-red);
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, var(--shadow-red) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
            z-index: -1;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.3; transform: scale(0.8); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-red) 0%, var(--primary-red-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
            text-shadow: 0 0 30px var(--shadow-red);
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            font-weight: 400;
            margin-bottom: 2rem;
        }
        
        /* Enhanced search container */
        .search-container {
            background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
            border: 2px solid var(--primary-red);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 3rem;
            box-shadow: 0 15px 35px var(--shadow-red);
            position: relative;
        }
        
        .search-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-red) 0%, var(--primary-red-light) 50%, var(--primary-red) 100%);
            border-radius: 20px 20px 0 0;
        }
        
        /* Enhanced video card styling */
        .video-card {
            border: 2px solid var(--border-color);
            border-radius: 20px;
            padding: 0;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            height: 480px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }
        
        .video-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, transparent 0%, var(--shadow-red) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 1;
            pointer-events: none;
        }
        
        .video-card:hover::before {
            opacity: 0.1;
        }
        
        .video-card:hover {
            transform: translateY(-10px) scale(1.02);
            border-color: var(--primary-red);
            box-shadow: 0 25px 50px var(--shadow-red-hover);
        }
        
        .video-thumbnail {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            border-radius: 20px 20px 0 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: var(--primary-red);
            position: relative;
            overflow: hidden;
        }
        
        .video-thumbnail::before {
            display: none;
        }
        
        @keyframes ripple {
            0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.1; }
            50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.05; }
            100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
        }
        
        .video-info {
            padding: 1.5rem;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 2;
        }
        
        .video-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
            height: 2.6em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            line-height: 1.3;
        }
        
        .video-metadata {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 1.5rem;
            flex-grow: 1;
        }
        
        .metadata-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            padding: 0.3rem 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .metadata-label {
            font-weight: 500;
            color: var(--text-secondary);
        }
        
        .metadata-value {
            color: var(--primary-red);
            font-weight: 600;
        }
        
        /* Enhanced button styling */
        .button-container {
            display: flex;
            gap: 0.5rem;
            margin-top: auto;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-red) 0%, var(--primary-red-dark) 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 6px 20px var(--shadow-red);
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, var(--primary-red-light) 0%, var(--primary-red) 100%);
            transform: translateY(-2px);
            box-shadow: 0 12px 30px var(--shadow-red-hover);
        }
        
        /* Enhanced input styling */
        .stTextInput > div > div > input {
            background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            border: 2px solid var(--border-color);
            border-radius: 15px;
            padding: 1rem 1.5rem;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--primary-red);
            box-shadow: 0 0 0 3px var(--shadow-red), inset 0 2px 4px rgba(0, 0, 0, 0.1);
            outline: none;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: var(--text-muted);
            font-weight: 400;
        }
        
        /* Enhanced title styling */
        h1 {
            color: var(--primary-red) !important;
            text-shadow: 0 0 20px var(--shadow-red);
            font-weight: 700 !important;
            font-size: 2.5rem !important;
        }
        
        h2 {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            margin-bottom: 1.5rem !important;
        }
        
        h3 {
            color: var(--text-primary) !important;
            font-weight: 500 !important;
        }
        
        /* Enhanced info boxes */
        .stInfo {
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%);
            border: 1px solid var(--primary-red);
            border-radius: 15px;
            padding: 1rem;
        }
        
        .stSuccess {
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%);
            border: 1px solid #22c55e;
            border-radius: 15px;
            padding: 1rem;
        }
        
        .stError {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
            border: 1px solid #ef4444;
            border-radius: 15px;
            padding: 1rem;
        }
        
        /* Stats container */
        .stats-container {
            background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
            border: 2px solid var(--primary-red);
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 25px var(--shadow-red);
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
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
            border-radius: 15px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            border-color: var(--primary-red);
            transform: translateY(-2px);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-red);
            display: block;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }
        
        /* Load more button */
        .load-more-container {
            text-align: center;
            padding: 2rem;
        }
        
        .load-more-button {
            background: linear-gradient(135deg, var(--primary-red) 0%, var(--primary-red-dark) 100%);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 1rem 2rem;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 8px 25px var(--shadow-red);
        }
        
        .load-more-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px var(--shadow-red-hover);
        }
        
        /* Footer styling */
        .footer {
            background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
            border-top: 2px solid var(--primary-red);
            padding: 2rem;
            margin-top: 3rem;
            text-align: center;
            border-radius: 20px 20px 0 0;
        }
        
        .footer-content {
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 1rem;
        }
        
        .footer-highlight {
            color: var(--primary-red);
            font-weight: 600;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.5rem;
            }
            
            .hero-section {
                padding: 2rem 1rem;
            }
            
            .video-card {
                height: auto;
                min-height: 400px;
            }
            
            .search-container {
                padding: 1.5rem;
            }
        }
        
                /* Enhanced search button */
        .stButton > button[data-testid="baseButton-primary"] {
            width: 100%;
            height: 40px;
            border-radius: 12px;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* Carousel container */
        .carousel-container {
            position: relative;
            height: 500px;
            overflow: hidden;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(220,38,38,0.3);
            margin-bottom: 2rem;
        }
        
        .carousel-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
            filter: brightness(0.6);
            border-radius: 20px;
            transition: all 0.5s ease;
        }
        
        .carousel-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 200px;
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
            display: flex;
            align-items: flex-end;
            padding: 20px;
        }
        
        .carousel-nav {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.3);
            border: 2px solid rgba(220,38,38,0.5);
            color: white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            font-size: 1.2rem;
        }
        
        .carousel-nav:hover {
            background: rgba(220,38,38,0.7);
            border-color: var(--primary-red);
            transform: translateY(-50%) scale(1.1);
        }
        
        .carousel-nav.prev {
            left: 20px;
        }
        
        .carousel-nav.next {
            right: 20px;
        }
        
        .carousel-indicators {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
        }
        
        .carousel-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: rgba(255,255,255,0.4);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .carousel-dot.active {
            background: var(--primary-red);
            transform: scale(1.2);
        }
        
        /* Video grid scrolling */
        .video-grid {
            max-height: 80vh;
            overflow-y: auto;
            padding-right: 10px;
            scroll-behavior: smooth;
        }
        
        .video-grid::-webkit-scrollbar {
            width: 8px;
        }
        
        .video-grid::-webkit-scrollbar-track {
            background: var(--bg-secondary);
            border-radius: 4px;
        }
        
        .video-grid::-webkit-scrollbar-thumb {
            background: var(--primary-red);
            border-radius: 4px;
        }
        
        .video-grid::-webkit-scrollbar-thumb:hover {
            background: var(--primary-red-light);
        }
        
        /* Loading animation */
        .loading-spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid var(--shadow-red);
            border-radius: 50%;
            border-top-color: var(--primary-red);
            animation: spin 1s ease-in-out infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-red);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-red-light);
        }
        
                /* Enhanced Netflix-style Hero Carousel */
        .hero-carousel {
            position: relative;
            width: 100%;
            height: 500px;
            overflow: hidden;
            border-radius: 20px;
            margin-bottom: 3rem;
            box-shadow: 0 20px 50px var(--shadow-red);
        }

        .hero-bg {
            position: absolute;
            width: 100%;
            height: 100%;
            object-fit: cover;
            filter: brightness(0.4);
            border-radius: 20px;
            transition: all 0.5s ease;
        }

        .hero-gradient-top,
        .hero-gradient-bottom {
            position: absolute;
            left: 0;
            right: 0;
            height: 120px;
            z-index: 1;
            pointer-events: none;
        }

        .hero-gradient-top {
            top: 0;
            background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
        }

        .hero-gradient-bottom {
            bottom: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
        }

        .hero-content {
            position: absolute;
            top: 0;
            left: 0;
            padding: 3rem;
            z-index: 2;
            color: white;
            max-width: 60%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 100%;
        }

        .hero-movie-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, var(--primary-red), var(--primary-red-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(220, 38, 38, 0.8);
            line-height: 1.1;
        }

        .hero-meta {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            font-weight: 500;
        }

        .hero-description {
            font-size: 1rem;
            color: var(--text-primary);
            max-width: 90%;
            margin-bottom: 2rem;
            line-height: 1.6;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .hero-buttons {
            display: flex;
            gap: 1rem;
            z-index: 3;
        }

        .hero-nav {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.6);
            border: 2px solid var(--primary-red);
            color: white;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            font-size: 1.5rem;
            z-index: 3;
        }

        .hero-nav:hover {
            background: var(--primary-red);
            border-color: var(--primary-red-light);
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 10px 25px var(--shadow-red);
        }

        .hero-nav.prev {
            left: 30px;
        }

        .hero-nav.next {
            right: 30px;
        }

        .hero-indicators {
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 12px;
            z-index: 3;
        }

        .hero-dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: rgba(255,255,255,0.4);
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }

        .hero-dot.active {
            background: var(--primary-red);
            border-color: var(--primary-red-light);
            transform: scale(1.2);
            box-shadow: 0 0 10px var(--shadow-red);
        }

        .hero-dot:hover {
            background: var(--primary-red-light);
            transform: scale(1.1);
        }

        /* Responsive hero design */
        @media (max-width: 768px) {
            .hero-content {
                max-width: 90%;
                padding: 2rem;
            }
            
            .hero-movie-title {
                font-size: 2rem;
            }
            
            .hero-nav {
                width: 50px;
                height: 50px;
                font-size: 1.2rem;
            }
            
            .hero-nav.prev {
                left: 15px;
            }
            
            .hero-nav.next {
                right: 15px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # API URL - Change this to match your FastAPI server
    API_URL = "http://localhost:8000"

    # Mock data fallback when API is not available
    MOCK_DATA = [
    {
        'pageid': 12345,
        'title': 'File:Charlie Chaplin The Gold Rush.webm',
        'canonicaltitle': 'File:Charlie Chaplin The Gold Rush.webm',
        'url': 'https://upload.wikimedia.org/wikipedia/commons/e/e3/Charlie_Chaplin_The_Gold_Rush.webm',
        'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Charlie_Chaplin_The_Gold_Rush.webm',
        'width': 1280,
        'height': 720,
        'duration': 5100.5,
        'size': 25600000,
        'thumburl': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Charlie_Chaplin_The_Gold_Rush.webm/320px--Charlie_Chaplin_The_Gold_Rush.webm.jpg'
    },
    {
        'pageid': 67890,
        'title': 'File:Nosferatu (1922).webm',
        'canonicaltitle': 'File:Nosferatu (1922).webm',
        'url': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Nosferatu_%281922%29.webm',
        'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Nosferatu_(1922).webm',
        'width': 1280,
        'height': 720,
        'duration': 5400.0,
        'size': 30720000,
        'thumburl': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Nosferatu_%281922%29.webm/320px--Nosferatu_%281922%29.webm.jpg'
    },
    {
        'pageid': 13579,
        'title': 'File:The Cabinet of Dr. Caligari (1920).ogv',
        'canonicaltitle': 'File:The Cabinet of Dr. Caligari (1920).ogv',
        'url': 'https://upload.wikimedia.org/wikipedia/commons/c/c3/The_Cabinet_of_Dr._Caligari_%281920%29.ogv',
        'descriptionurl': 'https://commons.wikimedia.org/wiki/File:The_Cabinet_of_Dr._Caligari_(1920).ogv',
        'width': 1280,
        'height': 720,
        'duration': 4500.0,
        'size': 28000000,
        'thumburl': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/The_Cabinet_of_Dr._Caligari_%281920%29.ogv/320px--The_Cabinet_of_Dr._Caligari_%281920%29.ogv.jpg'
    }
]


    # Function to simulate return_video_data() for testing
    async def get_video_data_from_function():
        """Get video data directly from the return_video_data function"""
        try:
            with st.spinner("🎬 Fetching videos from Wikimedia Commons..."):
                return await return_video_data()
        except Exception as e:
            st.error(f"Error fetching video data: {e}")

            fallback = []
            for item in MOCK_DATA:
                for page in item.get('pages', {}).values():
                    info = page.get('videoinfo', [{}])[0]
                    fallback.append({
                        'pageid': page.get('pageid'),
                        'title': page.get('title'),
                        'canonicaltitle': info.get('canonicaltitle'),
                        'url': info.get('url'),
                        'descriptionurl': info.get('descriptionurl'),
                        'width': info.get('width'),
                        'height': info.get('height'),
                        'duration': info.get('duration', 0),
                        'size': info.get('size'),
                        'thumburl': info.get('thumburl', None)
                    })

            print("Fallback data used:", len(fallback), "videos")
            return fallback  # <- MAKE SURE THIS IS RETURNED

    # Function to format duration
    def format_duration(seconds):
        """Convert seconds to human-readable format"""
        return str(timedelta(seconds=int(seconds)))

    # Function to format file size
    def format_size(size_bytes):
        """Convert bytes to MB"""
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB"

    # Function to clean video title
    def clean_title(title):
        """Remove 'File:' prefix and file extension from title"""
        clean = title.replace('File:', '')
        clean = clean.rsplit('.', 1)[0]
        return clean

    # Function to get videos from API or fallback to direct function
    async def get_videos(search_term=None):
        """Get videos directly from function"""
        raw_data = await get_video_data_from_function()
        processed_videos = []

        for video in raw_data:
            if 'canonicaltitle' in video and 'url' in video:
                if search_term:
                    if search_term.lower() in video['canonicaltitle'].lower():
                        processed_videos.append(video)
                else:
                    processed_videos.append(video)

        return processed_videos


    # Initialize session state
    if 'selected_video' not in st.session_state:
        st.session_state.selected_video = None
    if 'display_count' not in st.session_state:
        st.session_state.display_count = 100
    if 'all_videos' not in st.session_state:
        st.session_state.all_videos = []

    # Top Navigation Bar (left: title, right: search)
    top_col1, top_col2 = st.columns([1, 2])
    with top_col1:
        st.markdown("""
        <h1 style='margin-top: 0; color: var(--primary-red); text-shadow: 0 0 10px var(--shadow-red);'>
            🎬 StreamFlix
        </h1>
        """, unsafe_allow_html=True)

    with top_col2:
        st.markdown("""
        <div style='display: flex; align-items: center; gap: 10px; justify-content: flex-end;'>
        """, unsafe_allow_html=True)

        search_col1, search_col2 = st.columns([4, 1])
        with search_col1:
            search_term = st.text_input("Search", placeholder="Search movies...", label_visibility="collapsed", key="main_search")
        with search_col2:
            search_button = st.button("🔍", key="main_search_btn", help="Search videos")

        st.markdown("</div>", unsafe_allow_html=True)



    # Get videos based on search or load initial data
    if search_button or search_term or not st.session_state.all_videos:
        all_videos = await get_videos(search_term)
        st.session_state.all_videos = all_videos
        st.session_state.display_count = 100
    else:
        all_videos = st.session_state.all_videos

    # Carousel of 5 featured videos
    # Always use videos from the API (all_videos), fallback to MOCK_DATA only if empty
    carousel_source = all_videos if all_videos else MOCK_DATA
    # Ensure carousel_index is initialized
    if 'carousel_index' not in st.session_state:
        st.session_state.carousel_index = 0
    carousel_videos = random.sample(carousel_source, min(len(carousel_source), 5))
    carousel_index = st.session_state.carousel_index
    # Ensure index is in range
    if carousel_index >= len(carousel_videos):
        carousel_index = 0
        st.session_state.carousel_index = 0
    video = carousel_videos[carousel_index]

    # Generate a simple description for the video
    descriptions = [
        "A timeless classic that showcases the golden age of cinema with unforgettable performances and stunning visuals.",
        "Experience the magic of early filmmaking in this masterpiece that continues to captivate audiences worldwide.",
        "This iconic film represents a milestone in cinematic history with its groundbreaking techniques and storytelling.",
        "Discover the artistry and craftsmanship of vintage cinema in this beautifully preserved classic.",
        "Journey into the past with this remarkable film that demonstrates the enduring power of great storytelling."
    ]
    current_description = descriptions[carousel_index % len(descriptions)]

    # Carousel HTML (only once), with Watch button overlay using Streamlit
    st.markdown(f'''
    <style>
    .carousel-img-container {{
        position: relative;
        width: 100%;
        height: 100%;
    }}
    .carousel-watch-btn-container {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 30;
    }}
    </style>
    <div class="hero-carousel">
        <div class="carousel-img-container" style="min-height: 400px;">
            <img src="{video.get('thumburl', 'https://via.placeholder.com/1280x720/333/fff?text=No+Image')}" class="hero-bg" alt="Hero Background" />
            <div class="carousel-watch-btn-container" id="carousel-watch-btn"></div>
        </div>
        <div class="hero-gradient-top"></div>
        <div class="hero-gradient-bottom"></div>
        <div class="hero-content">
            <h1 class="hero-movie-title">{clean_title(video['title'])}</h1>
            <p class="hero-meta">⏱ {format_duration(video['duration'])} • {video['width']}×{video['height']} • 📁 {format_size(video['size'])}</p>
            <p class="hero-description">{current_description}</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Overlay the Watch button using Streamlit's absolute positioning (centered on thumbnail)
    watch_btn_placeholder = st.empty()
    watch_btn_html = '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);z-index:30;"></div>'
    watch_btn_placeholder.markdown(watch_btn_html, unsafe_allow_html=True)
    if watch_btn_placeholder.button("▶️ Watch", key="hero_watch", help="Watch this video", use_container_width=False):
        st.session_state.selected_video = video
        st.switch_page("pages/01_Video_Player.py")

    # Overlay navigation buttons using Streamlit columns (left and right)
    nav_cols = st.columns([1, 6, 1])
    with nav_cols[0]:
        if st.button("⬅️", key="hero_prev", help="Previous video", use_container_width=True):
            st.session_state.carousel_index = (carousel_index - 1) % len(carousel_videos)
            st.rerun()
    with nav_cols[2]:
        if st.button("➡️", key="hero_next", help="Next video", use_container_width=True):
            st.session_state.carousel_index = (carousel_index + 1) % len(carousel_videos)
            st.rerun()

    # Carousel indicator dots
    dots_html = '<div class="hero-indicators">'
    for idx in range(len(carousel_videos)):
        active_class = "active" if idx == carousel_index else ""
        dots_html += f'<div class="hero-dot {active_class}"></div>'
    dots_html += '</div>'
    st.markdown(dots_html, unsafe_allow_html=True)

    # Get the current batch of videos to display
    videos = all_videos[:st.session_state.display_count]

    if videos:
        # Stats container
        st.markdown(f"""
        <div class="stats-container">
            <h3>📊 Collection Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">{len(videos)}</span>
                    <div class="stat-label">Videos Displayed</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(all_videos)}</span>
                    <div class="stat-label">Total Available</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{sum(video['duration'] for video in videos) / 3600:.1f}h</span>
                    <div class="stat-label">Total Runtime</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{sum(video['size'] for video in videos) / (1024**3):.1f}GB</span>
                    <div class="stat-label">Total Size</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Display videos in a grid layout 🎬
        cols = st.columns(3)
        for i, video in enumerate(videos):
            col = cols[i % 3]
            with col:
                st.markdown(f"""
                <div class="video-card">
                    <div class="video-thumbnail">
                        <img src="{video.get('thumburl') or 'https://pin.it/6OUANYdb1'}" alt="Thumbnail" style="width:100%; height:100%; object-fit:cover; border-radius: 20px 20px 0 0;" />
                    </div>
                    <div class="video-info">
                        <h4 class="video-title">{clean_title(video['canonicaltitle'])}</h4>
                        <div class="video-metadata">
                            <div class="metadata-item">
                                <span class="metadata-label">⏱️ Duration:</span>
                                <span class="metadata-value">{format_duration(video['duration'])}</span>
                            </div>
                            <div class="metadata-item">
                                <span class="metadata-label">📐 Resolution:</span>
                                <span class="metadata-value">{video['width']}×{video['height']}</span>
                            </div>
                            <div class="metadata-item">
                                <span class="metadata-label">📁 Size:</span>
                                <span class="metadata-value">{format_size(video['size'])}</span>
                            </div>
                        </div>
                        <div class="button-container">
                """, unsafe_allow_html=True)
                # Only Watch button (no Details)
                if st.button("▶️ Watch", key=f"watch-{video['pageid']}-{i}", type="primary"):
                    st.session_state.selected_video = video
                    st.switch_page("pages/01_Video_Player.py")
                st.markdown("""
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
    # Load more button
    if len(all_videos) > st.session_state.display_count:
        st.markdown('<div class="load-more-container">', unsafe_allow_html=True)
        unique_key = f"load_more_{st.session_state.display_count}"
        if st.button("📥 Load More Videos", type="primary", key=unique_key):
            st.session_state.display_count += 100
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="stats-container">
            <h3>🔍 No Results Found</h3>
            <p>Try adjusting your search terms or wait for videos to load.</p>
        </div>
        """, unsafe_allow_html=True)


    # Footer
    st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <span class="footer-highlight">🎬 StreamFlix</span> • 
            Data from <span class="footer-highlight">Wikimedia Commons</span> • 
            Built with <span class="footer-highlight">Streamlit</span> • 
            <span class="footer-highlight">Open Source Films</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
import aiohttp
import asyncio
import json
import re
import os
from typing import Dict, List, Any

# You'll need to install: pip install google-generativeai
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyC2bzsTTU5br0H-P-EQReLMHiOvLZLILW8"  # Set your API key as environment variable
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def fetch_movie_details_from_wikimedia(description_url: str) -> str:
    """
    Fetch movie details from Wikimedia Commons page.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(description_url) as response:
                if response.status == 200:
                    content = await response.text()
                    # Extract basic information from the page content
                    # This is a simplified extraction - you might want to use BeautifulSoup for better parsing
                    return content[:2000]  # Limit content for API efficiency
                else:
                    return f"Unable to fetch details from {description_url}"
    except Exception as e:
        return f"Error fetching movie details: {str(e)}"

async def character_tropes_generator(movie_title: str, description_url: str) -> str:
    """
    Generate character tropes analysis for a given movie using Gemini API.
    """
    try:
        if not GEMINI_API_KEY:
            return await fallback_analysis(movie_title)
        
        # Fetch additional context from Wikimedia if available
        movie_context = ""
        if description_url:
            movie_context = await fetch_movie_details_from_wikimedia(description_url)
        
        # Create the prompt for Gemini
        prompt = f"""
        Analyze the movie "{movie_title}" and provide a detailed character tropes analysis in JSON format.
        
        Additional context from Wikimedia Commons:
        {movie_context[:1000] if movie_context else "No additional context available"}
        
        Please provide your analysis in the following JSON structure:
        {{
            "film_title": "{movie_title}",
            "estimated_year": "YYYY or Unknown",
            "estimated_genre": "Primary genre",
            "plot_available": true/false,
            "tropes_identified": [
                {{
                    "trope_name": "Name of the trope",
                    "description": "Detailed description of the trope",
                    "confidence_score": 1-10,
                    "evidence": "Why this trope applies to this movie"
                }}
            ],
            "thematic_elements": ["Theme1", "Theme2", "Theme3"],
            "analysis_summary": "Comprehensive summary of the film's storytelling elements and significance"
        }}
        
        Focus on identifying:
        1. Character archetypes and tropes
        2. Narrative patterns
        3. Genre conventions
        4. Thematic elements
        5. Historical/cultural significance
        
        Be specific about why each trope applies to this particular film. If this is a classic or public domain film, consider its historical context and influence on cinema.
        """
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            # Validate JSON
            parsed_json = json.loads(json_str)
            return json.dumps(parsed_json, indent=2)
        else:
            # If no JSON found, create structured response from text
            return await parse_gemini_text_response(movie_title, response_text)
            
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return await fallback_analysis(movie_title)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return await fallback_analysis(movie_title)

async def parse_gemini_text_response(movie_title: str, response_text: str) -> str:
    """
    Parse Gemini's text response and convert to structured JSON if JSON parsing fails.
    """
    try:
        # Extract year from title or response
        year_match = re.search(r'\((\d{4})\)|(\d{4})', movie_title + " " + response_text)
        estimated_year = year_match.group(1) or year_match.group(2) if year_match else "Unknown"
        
        # Extract genre (look for common genre keywords)
        genre_keywords = {
            'horror': 'Horror',
            'comedy': 'Comedy', 
            'drama': 'Drama',
            'romance': 'Romance',
            'action': 'Action',
            'western': 'Western',
            'thriller': 'Thriller',
            'adventure': 'Adventure',
            'musical': 'Musical',
            'documentary': 'Documentary'
        }
        
        estimated_genre = "Drama"  # Default
        response_lower = response_text.lower()
        for keyword, genre in genre_keywords.items():
            if keyword in response_lower:
                estimated_genre = genre
                break
        
        # Create a structured response based on available information
        structured_analysis = {
            "film_title": movie_title,
            "estimated_year": estimated_year,
            "estimated_genre": estimated_genre,
            "plot_available": True,
            "tropes_identified": [
                {
                    "trope_name": "AI-Generated Analysis",
                    "description": "Analysis generated using AI interpretation of the film",
                    "confidence_score": 7,
                    "evidence": response_text[:200] + "..." if len(response_text) > 200 else response_text
                }
            ],
            "thematic_elements": ["Classic Cinema", "Historical Significance", "Storytelling"],
            "analysis_summary": response_text[:500] + "..." if len(response_text) > 500 else response_text
        }
        
        return json.dumps(structured_analysis, indent=2)
        
    except Exception as e:
        return await fallback_analysis(movie_title)

async def fallback_analysis(movie_title: str) -> str:
    """
    Generate fallback analysis when Gemini API is unavailable.
    """
    # Simulate API delay
    await asyncio.sleep(1)
    
    # Extract year from title
    year_match = re.search(r'\((\d{4})\)', movie_title)
    estimated_year = year_match.group(1) if year_match else "Unknown"
    
    # Basic genre detection based on title
    title_lower = movie_title.lower()
    if any(word in title_lower for word in ['horror', 'vampire', 'monster', 'ghost', 'demon']):
        genre = "Horror"
        themes = ["Fear", "Supernatural", "Survival"]
    elif any(word in title_lower for word in ['comedy', 'funny', 'laugh', 'comic']):
        genre = "Comedy"  
        themes = ["Humor", "Entertainment", "Social Commentary"]
    elif any(word in title_lower for word in ['love', 'romantic', 'romance', 'wedding']):
        genre = "Romance"
        themes = ["Love", "Relationships", "Emotion"]
    elif any(word in title_lower for word in ['war', 'battle', 'western', 'cowboy']):
        genre = "Action/Adventure"
        themes = ["Courage", "Conflict", "Honor"]
    else:
        genre = "Drama"
        themes = ["Human Nature", "Society", "Character Development"]
    
    fallback_analysis = {
        "film_title": movie_title,
        "estimated_year": estimated_year,
        "estimated_genre": genre,
        "plot_available": False,
        "tropes_identified": [
            {
                "trope_name": "Classic Cinema Elements",
                "description": "Traditional storytelling elements typical of early filmmaking",
                "confidence_score": 6,
                "evidence": f"Based on title analysis and historical context of {genre.lower()} films from this era"
            },
            {
                "trope_name": "Period-Appropriate Narrative",
                "description": "Storytelling conventions that were popular during the film's estimated time period",
                "confidence_score": 7,
                "evidence": f"Films from {estimated_year} typically employed specific narrative structures and character types"
            }
        ],
        "thematic_elements": themes + ["Historical Significance", "Public Domain Heritage"],
        "analysis_summary": f"This {genre.lower()} film from {estimated_year} represents classic cinema from the public domain collection. While detailed analysis is limited without AI enhancement, it likely contains traditional storytelling elements and character archetypes typical of its era and genre."
    }
    
    return json.dumps(fallback_analysis, indent=2)

async def analyze_multiple_movies(movie_titles: List[str]) -> Dict[str, Any]:
    """
    Analyze multiple movies and return comparative analysis using Gemini API.
    """
    try:
        analyses = []
        for title in movie_titles:
            analysis = await character_tropes_generator(title, "")
            analyses.append(json.loads(analysis))
        
        if not GEMINI_API_KEY:
            return await fallback_multiple_analysis(analyses)
        
        # Create comparative analysis prompt for Gemini
        movies_info = "\n".join([f"- {analysis['film_title']} ({analysis['estimated_year']}) - {analysis['estimated_genre']}" 
                                for analysis in analyses])
        
        comparative_prompt = f"""
        Analyze these movies comparatively and identify common themes, tropes, and patterns:
        
        {movies_info}
        
        Provide analysis in JSON format:
        {{
            "movies_analyzed": {len(analyses)},
            "common_genres": ["list of genres"],
            "common_themes": ["shared themes across movies"],
            "recurring_tropes": ["tropes that appear in multiple films"],
            "time_period_analysis": "Analysis of the historical period these films represent",
            "cultural_significance": "What these films reveal about their era",
            "summary": "Comprehensive comparative analysis"
        }}
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(comparative_prompt)
        
        # Try to parse JSON response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            comparative_data = json.loads(json_match.group())
            comparative_data["individual_analyses"] = analyses
            return comparative_data
        else:
            return await fallback_multiple_analysis(analyses)
            
    except Exception as e:
        return await fallback_multiple_analysis(analyses if 'analyses' in locals() else [])

async def fallback_multiple_analysis(analyses: List[Dict]) -> Dict[str, Any]:
    """
    Fallback comparative analysis when Gemini API is unavailable.
    """
    all_genres = [analysis.get("estimated_genre", "Unknown") for analysis in analyses]
    all_themes = []
    for analysis in analyses:
        all_themes.extend(analysis.get("thematic_elements", []))
    
    comparative_analysis = {
        "movies_analyzed": len(analyses),
        "common_genres": list(set(all_genres)),
        "common_themes": list(set(all_themes)),
        "recurring_tropes": ["Classic Cinema", "Period Storytelling"],
        "time_period_analysis": "Collection represents various eras of early cinema",
        "cultural_significance": "These public domain films preserve important cinematic history",
        "individual_analyses": analyses,
        "summary": f"Analyzed {len(analyses)} films representing diverse genres and themes from classic cinema history."
    }
    
    return comparative_analysis

def extract_movie_info_from_url(url: str) -> Dict[str, str]:
    """
    Extract movie information from Wikimedia Commons URL.
    """
    try:
        info = {
            "source": "Wikimedia Commons",
            "url": url,
            "type": "Public Domain Film"
        }
        return info
    except Exception as e:
        return {"error": str(e)}
    

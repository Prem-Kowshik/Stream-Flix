import asyncio
from google import genai
from google.genai import types
from google.genai.types import (GenerateContentConfig,GoogleSearch,HttpOptions,Tool,)
import re
from response_testing import return_video_data
import json

API_KEY="AIzaSyC2bzsTTU5br0H-P-EQReLMHiOvLZLILW8"
client = genai.Client(api_key=API_KEY)

async def fetch_video_url_title():
    video_data = await return_video_data()
    urls = []
    title=[]
    for item in video_data:
            for page_id, page_data in item['pages'].items():
                if 'videoinfo' in page_data and page_data['videoinfo']:
                    video_info = page_data['videoinfo'][0]
                    urls.append(video_info['descriptionurl'])    
                    title.append(video_info['canonicaltitle'])
    return urls,title      

async def async_description_generator(title, url):
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Find a detailed description of the movie with the title: {title}. The movie can be found at this URL: {url}",
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
            ),
        )
        return response.text if response.text else "No description available"
    except Exception as e:
        print(f"Error in async_description_generator: {e}")
        return f"Error generating description: {str(e)}"

async def generate_movie_descriptions():
    asyncio.Semaphore(10)  # Limit concurrent requests
    titles, urls= await fetch_video_url_title()
    descriptions = {}
    
    # Create tasks for all descriptions
    tasks = [async_description_generator(titles[i], urls[i]) for i in range(len(titles))]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error generating description for {titles[i]}: {result}")
            descriptions[titles[i]] = f"Error: {str(result)}"
        else:
            descriptions[titles[i]] = result
            print(f"Description for {titles[i]}: {result[:100]}...")  # Show first 100 chars
    
    print(f"Generated {len(descriptions)} descriptions")
    return descriptions

async def character_tropes_generator(title, url):
    """Generate character tropes analysis for a movie with improved error handling"""
    try:
        # Enhanced prompt with clearer JSON formatting instructions
        prompt = f'''Analyze the movie "{title}" (URL: {url}) and identify character tropes.

IMPORTANT: Respond ONLY with valid JSON in exactly this format (no markdown, no extra text):

{{
    "film_title": "{title}",
    "estimated_year": "1940s",
    "estimated_genre": "Drama",
    "plot_available": true,
    "tropes_identified": [
        {{
            "trope_name": "The Hero",
            "description": "Main character who saves the day",
            "confidence_score": 8,
            "evidence": "Character performs heroic acts throughout the film"
        }}
    ],
    "thematic_elements": ["heroism", "sacrifice", "redemption"],
    "analysis_summary": "Brief analysis of the film's storytelling approach"
}}

If you cannot find information about this specific film, still provide the JSON structure with estimated/generic values and note the limitations in the analysis_summary.'''
        
        # Add timeout and retry logic
        for attempt in range(3):  # Try up to 3 times
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt,
                        config=GenerateContentConfig(
                            tools=[Tool(google_search=GoogleSearch())],
                        ),
                    ),
                    timeout=60.0  # 60 second timeout
                )
                
                if response and response.text:
                    return response.text
                else:
                    if attempt == 2:  # Last attempt
                        return generate_fallback_response(title)
                    await asyncio.sleep(2)  # Wait before retry
                    
            except asyncio.TimeoutError:
                print(f"Timeout on attempt {attempt + 1} for {title}")
                if attempt == 2:
                    return generate_fallback_response(title)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error on attempt {attempt + 1} for {title}: {e}")
                if attempt == 2:
                    return generate_fallback_response(title)
                await asyncio.sleep(2)
        
        return generate_fallback_response(title)
        
    except Exception as e:
        print(f"Fatal error in character_tropes_generator: {e}")
        return generate_fallback_response(title, str(e))

def generate_fallback_response(title, error_msg=None):
    """Generate a fallback JSON response when AI analysis fails"""
    return json.dumps({
        "film_title": title,
        "estimated_year": "Unknown",
        "estimated_genre": "Unknown",
        "plot_available": False,
        "tropes_identified": [
            {
                "trope_name": "Analysis Unavailable",
                "description": "Unable to analyze character tropes due to technical limitations",
                "confidence_score": 0,
                "evidence": f"Error: {error_msg}" if error_msg else "No analysis could be performed"
            }
        ],
        "thematic_elements": ["analysis_unavailable"],
        "analysis_summary": f"Analysis could not be completed. {error_msg if error_msg else 'Please try again later.'}"
    })

# Batch processing function for multiple movies
async def analyze_multiple_movies(movie_data_list, max_concurrent=5):
    """Analyze multiple movies with concurrency control"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def analyze_single_movie(movie_data):
        async with semaphore:
            title = movie_data.get('canonicaltitle', movie_data.get('title', 'Unknown'))
            url = movie_data.get('descriptionurl', '')
            return await character_tropes_generator(title, url)
    
    tasks = [analyze_single_movie(movie) for movie in movie_data_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    analysis_results = {}
    for i, result in enumerate(results):
        movie_title = movie_data_list[i].get('canonicaltitle', f'Movie_{i}')
        if isinstance(result, Exception):
            analysis_results[movie_title] = generate_fallback_response(movie_title, str(result))
        else:
            analysis_results[movie_title] = result
    
    return analysis_results
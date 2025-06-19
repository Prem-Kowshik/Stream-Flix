import asyncio
from response_testing import return_video_data
from google import genai
from google.genai import types
from google.genai.types import (GenerateContentConfig,GoogleSearch,HttpOptions,Tool)
import json
import streamlit as st
from tenacity import retry, wait_random_exponential
GEMINI_API_KEY=st.secrets["GEMINI_API_KEY"]
async def fetch_video_url_title():
    video_data = await return_video_data()
    urls = []
    titles=[]
    for item in video_data:
            urls.append(item['url'])
            title=item['canonicaltitle'].lstrip('File:')
            title2=title.rstrip('.webm')
            title3=title2.rstrip('.ogv')
            titles.append(title3)
    return urls,titles    
def clean_response(response):
    response_text = response.text
    respl=response_text.lstrip("```json")
    respr=respl.rstrip("```")
    print(respr)
    try:
        json_data = json.loads(respr)
        return json_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    

@retry(wait=wait_random_exponential(multiplier=1, max=120))
async def fetch_genre(title, url):
    sem2=asyncio.Semaphore(15)  # Limit concurrent requests
    async with sem2:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=f"""Find the genre of the movie with the title: {title}. The movie can be found at this URL: {url}
            Format the response as a JSON object with the following fields:
            {{
                "title": "{title}",
                "url": "{url}",
                "genre": "<estimated genre of the film>"
            }}""",
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
            ),
        )
        if sem2.locked():
            print("concurrency limit reached")
            await asyncio.sleep(1)
    print("task done")
    return clean_response(response)

async def main():
    sem=asyncio.Semaphore(15)  # Limit concurrent requests
    urls, titles = await fetch_video_url_title()
    print("creating tasks")
    genre_tasks = [asyncio.create_task(fetch_genre(titles[i], urls[i])) for i in range(len(titles))]
    print("tasks created")
    print("gathering tasks")
    async with sem:
        lists=await asyncio.gather(*genre_tasks)
        if sem.locked():
            print("concurrency limit reached")
            await asyncio.sleep(1)
    print("tasks gathered")
    print("processing results")
    genre={}
    try:
        for i in lists:
            if i["genre"] not in genre.keys():
                genre[i["genre"]]=[]
            genre[i["genre"]].append({"title": i["title"], "url": i["url"]})
            print("here")
        print("done")
    except TypeError:
        print("object not readable")
    return genre    

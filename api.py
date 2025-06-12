from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
from pydantic import BaseModel
import re
from response_testing import return_video_data  # Assuming this is the module where the function is defined

# Importing the function that returns video data
# from response_testing import return_video_data
app = FastAPI()

# Mock data for testing - replace with actual return_video_data() call
def get_video_data():
    """Get video data from Wikimedia Commons"""
    try:
        return return_video_data()
    except Exception as e:
        print(f"Error fetching video data: {e}")
        # Fallback to mock data or return empty list
        return []
    

# Create FastAPI app

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for video info
class VideoInfo(BaseModel):
    pageid: int
    title: str
    canonicaltitle: str
    url: str
    descriptionurl: str
    width: int
    height: int
    duration: float
    size: int




# Process raw video data into a more usable format
def process_video_data(raw_data):
    processed_videos = []
    
    for item in raw_data:
        for page_id, page_data in item['pages'].items():
            if 'videoinfo' in page_data and page_data['videoinfo']:
                video_info = page_data['videoinfo'][0]
                processed_videos.append({
                    'pageid': page_data['pageid'],
                    'title': page_data['title'],
                    'canonicaltitle': video_info['canonicaltitle'],
                    'url': video_info['url'],
                    'descriptionurl': video_info['descriptionurl'],
                    'width': video_info['width'],
                    'height': video_info['height'],
                    'duration': video_info.get('duration', 0),
                    'size': video_info['size']
                })
    
    return processed_videos

@app.get("/videos", response_model=List[VideoInfo])
async def get_videos(search: Optional[str] = Query(None, description="Search by canonical title")):
    """Get all videos or search for videos by canonical title"""
    raw_data = get_video_data()
    videos = process_video_data(raw_data)
    
    # Filter by search term if provided
    if search:
        search_lower = search.lower()
        videos = [v for v in videos if search_lower in v['canonicaltitle'].lower()]
    
    return videos

@app.get("/videos/{page_id}", response_model=VideoInfo)
async def get_video(page_id: int):
    """Get details for a specific video by page ID"""
    raw_data = get_video_data()
    videos = process_video_data(raw_data)
    
    # Find the video with the matching page_id
    for video in videos:
        if video['pageid'] == page_id:
            return video
    
    return {"error": "Video not found"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Wikimedia Commons Video API",
        "endpoints": {
            "/videos": "Get all videos or search by title",
            "/videos/{page_id}": "Get specific video by page ID",
            "/docs": "API documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

#!/usr/bin/env python3
"""
YouTube Backend API for n8n workflows
Handles YouTube operations without OAuth2 in n8n
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeBackendAPI:
    """
    Mock YouTube backend API for n8n integration.

    In production, this would use the actual YouTube Data API v3
    with proper authentication (API key or OAuth2).
    """

    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')

    def upload_video(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle video upload to YouTube.

        In production, this would:
        1. Use youtube-dl or YouTube Data API
        2. Upload the actual video file
        3. Return real video ID and URLs
        """
        # Simulate upload for testing
        video_id = f"vid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        response = {
            "success": True,
            "video_id": video_id,
            "video_url": f"https://youtube.com/watch?v={video_id}",
            "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
            "title": metadata.get("title"),
            "description": metadata.get("description"),
            "privacy": metadata.get("privacy", "private"),
            "status": "processing",
            "message": "Video upload initiated successfully"
        }

        logger.info(f"Video upload simulated: {video_id}")
        return response

    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> Dict[str, Any]:
        """
        Upload thumbnail for a video.

        In production, this would:
        1. Use YouTube Data API thumbnails.set endpoint
        2. Upload the actual image file
        """
        response = {
            "success": True,
            "video_id": video_id,
            "thumbnail_path": thumbnail_path,
            "message": "Thumbnail uploaded successfully"
        }

        logger.info(f"Thumbnail upload simulated for video: {video_id}")
        return response

    def add_to_playlist(self, video_id: str, playlist_id: str) -> Dict[str, Any]:
        """
        Add video to playlist.

        In production, this would:
        1. Use YouTube Data API playlistItems.insert endpoint
        """
        response = {
            "success": True,
            "video_id": video_id,
            "playlist_id": playlist_id,
            "message": "Video added to playlist successfully"
        }

        logger.info(f"Added video {video_id} to playlist {playlist_id}")
        return response

# FastAPI implementation (optional, for production)
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn

    app = FastAPI(title="YouTube Backend API for n8n")
    api = YouTubeBackendAPI()

    class UploadRequest(BaseModel):
        video_path: str
        title: str
        description: Optional[str] = ""
        tags: Optional[list] = []
        category_id: Optional[str] = "22"
        privacy: Optional[str] = "private"
        playlist_id: Optional[str] = None
        thumbnail_path: Optional[str] = None

    class ThumbnailRequest(BaseModel):
        video_id: str
        thumbnail_path: str

    class PlaylistRequest(BaseModel):
        video_id: str
        playlist_id: str

    @app.post("/api/youtube/upload")
    async def upload_video(request: UploadRequest):
        """Upload video to YouTube"""
        try:
            result = api.upload_video(request.dict())
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/youtube/thumbnail")
    async def upload_thumbnail(request: ThumbnailRequest):
        """Upload thumbnail for video"""
        try:
            result = api.upload_thumbnail(request.video_id, request.thumbnail_path)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/youtube/playlist/add")
    async def add_to_playlist(request: PlaylistRequest):
        """Add video to playlist"""
        try:
            result = api.add_to_playlist(request.video_id, request.playlist_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if __name__ == "__main__":
        print("Starting YouTube Backend API server...")
        print("This server handles YouTube operations for n8n workflows")
        print("Configure your n8n workflows to point to: http://localhost:8000")
        print("\nEndpoints:")
        print("  POST /api/youtube/upload - Upload video")
        print("  POST /api/youtube/thumbnail - Upload thumbnail")
        print("  POST /api/youtube/playlist/add - Add to playlist")
        uvicorn.run(app, host="0.0.0.0", port=8000)

except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    print("For testing, the YouTubeBackendAPI class can still be used directly")
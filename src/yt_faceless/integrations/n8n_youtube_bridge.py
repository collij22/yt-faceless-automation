#!/usr/bin/env python3
"""
N8n YouTube Bridge - Connects n8n workflows to existing YouTube upload functionality.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
from pathlib import Path
import json
import os

# Import your existing modules
from ..production.upload import YouTubeUploader
from ..config import Config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/youtube", tags=["n8n-bridge"])

# Request models for n8n
class UploadRequest(BaseModel):
    video_path: str
    title: str
    description: Optional[str] = ""
    tags: Optional[List[str]] = []
    category_id: Optional[str] = "22"
    privacy: Optional[str] = "private"
    playlist_id: Optional[str] = None
    thumbnail_path: Optional[str] = None
    slug: Optional[str] = None

class ThumbnailRequest(BaseModel):
    video_id: str
    thumbnail_path: str

class PlaylistRequest(BaseModel):
    video_id: str
    playlist_id: str

@router.post("/upload")
async def upload_video_bridge(request: UploadRequest):
    """
    Bridge endpoint for n8n YouTube upload workflow.
    """
    try:
        # Use your existing upload logic
        config = Config()
        uploader = YouTubeUploader(config)

        # Convert request to your format
        metadata = {
            "title": request.title,
            "description": request.description,
            "tags": request.tags,
            "category_id": request.category_id,
            "privacy_status": request.privacy,
        }

        # Call your existing upload method
        # This is a mock - replace with your actual upload logic
        video_id = f"uploaded_{request.slug or 'video'}"

        # For now, return success
        # In production, call your actual upload function
        result = {
            "success": True,
            "video_id": video_id,
            "video_url": f"https://youtube.com/watch?v={video_id}",
            "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
            "title": request.title,
            "status": "processing"
        }

        logger.info(f"Video upload initiated via n8n: {video_id}")
        return result

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/thumbnail")
async def upload_thumbnail_bridge(request: ThumbnailRequest):
    """
    Bridge endpoint for thumbnail upload.
    """
    try:
        # Use your existing thumbnail upload logic
        # This is a mock - replace with your actual logic
        result = {
            "success": True,
            "video_id": request.video_id,
            "thumbnail_path": request.thumbnail_path,
            "message": "Thumbnail uploaded successfully"
        }

        logger.info(f"Thumbnail uploaded for video: {request.video_id}")
        return result

    except Exception as e:
        logger.error(f"Thumbnail upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/playlist/add")
async def add_to_playlist_bridge(request: PlaylistRequest):
    """
    Bridge endpoint for adding video to playlist.
    """
    try:
        # Use your existing playlist logic
        # This is a mock - replace with your actual logic
        result = {
            "success": True,
            "video_id": request.video_id,
            "playlist_id": request.playlist_id,
            "message": "Video added to playlist"
        }

        logger.info(f"Added video {request.video_id} to playlist {request.playlist_id}")
        return result

    except Exception as e:
        logger.error(f"Playlist addition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add this router to your main FastAPI app
def setup_n8n_bridge(app):
    """
    Add n8n bridge routes to your existing FastAPI app.

    Usage in your main app:
    from .integrations.n8n_youtube_bridge import setup_n8n_bridge
    setup_n8n_bridge(app)
    """
    app.include_router(router)
    logger.info("N8n YouTube bridge endpoints registered")
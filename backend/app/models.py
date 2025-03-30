# backend/app/models.py
from typing import List, Optional

from pydantic import BaseModel


class Chapter(BaseModel):
    title: str
    content: str


class VideoScript(BaseModel):
    scene_description: str
    narration: str
    key_points: List[str]


class ProcessingResult(BaseModel):
    chapter: Chapter
    script: VideoScript
    audio_url: Optional[str]
    subtitles: Optional[str]

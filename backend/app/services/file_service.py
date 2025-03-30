# backend/app/services/file_service.py
import pymupdf4llm
from typing import List
from ..models import Chapter
import requests
import re

class FileProcessor:
    @staticmethod
    async def process_file(file_path: str) -> str:
        """Extract content from PDF/DOC and convert to markdown"""
        content = pymupdf4llm.to_markdown(file_path)
        return content

    @staticmethod
    async def download_image(url: str, name: str, path: str):
        """Download image from url to path/name"""
        response = requests.get(url)
        try:
            with open(f"{path}/{name}", "wb") as buffer:
                buffer.write(response.content)
                buffer.close()
        except IOError as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    @staticmethod
    def split_into_chapters(markdown_content: str) -> List[Chapter]:
        """Split markdown content into chapters"""
        chapters = []
        current_chapter = ""
        current_title = ""

        # Split by markdown headers
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('#'):
                if current_chapter:
                    chapters.append(Chapter(
                        title=current_title.strip(),
                        content=current_chapter.strip()
                    ))
                current_title = line.lstrip('#').strip()
                current_chapter = ""
            else:
                current_chapter += line + "\n"

        # Add the last chapter
        if current_chapter:
            chapters.append(Chapter(
                title=current_title.strip(),
                content=current_chapter.strip()
            ))

        return chapters

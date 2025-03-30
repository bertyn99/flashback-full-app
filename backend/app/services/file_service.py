# backend/app/services/file_service.py
import pymupdf4llm
from typing import List
from ..models import Chapter
import re

class FileProcessor:
    @staticmethod
    async def process_file(file_path: str) -> str:
        """Extract content from PDF/DOC and convert to markdown"""
        content = pymupdf4llm.to_markdown(file_path)
        return content

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
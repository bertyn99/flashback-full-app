import boto3
from botocore.config import Config
from fastapi import HTTPException
import pymupdf4llm
from typing import List
import requests
import os
from ..models import Chapter
from ..config import settings


class FileProcessor:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name="weur",
        )

    async def upload_to_r2(self, file_path: str, content_type: str = None) -> str:
        try:
            file_name = os.path.basename(file_path)

            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            self.s3_client.upload_file(
                file_path,
                settings.R2_BUCKET_NAME,
                file_name,
             
                ExtraArgs=extra_args
            )

            url = f"{settings.R2_PUBLIC_URL}/{file_name}"
            return url

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading file to R2: {str(e)}"
            )

    @staticmethod
    async def process_file(file_path: str) -> str:
        """Extract content from PDF/DOC and convert to markdown"""
        content = pymupdf4llm.to_markdown(file_path)
        return content

    async def download_and_upload_image(self, url: str, name: str, temp_path: str) -> str:
        temp_file_path = f"{temp_path}/{name}"

        response = requests.get(url)
        try:
            with open(temp_file_path, "wb") as buffer:
                buffer.write(response.content)

            content_type = response.headers.get('Content-Type')
            r2_url = await self.upload_to_r2(temp_file_path, content_type)

            os.remove(temp_file_path)

            return r2_url
        except IOError as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    @staticmethod
    def split_into_chapters(markdown_content: str) -> List[Chapter]:
        """Split markdown content into chapters"""
        chapters = []
        current_chapter = ""
        current_title = ""

        # Split by markdown headers
        lines = markdown_content.split("\n")
        for line in lines:
            if line.startswith("#"):
                if current_chapter:
                    chapters.append(
                        Chapter(
                            title=current_title.strip(), content=current_chapter.strip()
                        )
                    )
                current_title = line.lstrip("#").strip()
                current_chapter = ""
            else:
                current_chapter += line + "\n"

        # Add the last chapter
        if current_chapter:
            chapters.append(
                Chapter(title=current_title.strip(), content=current_chapter.strip())
            )

        return chapters

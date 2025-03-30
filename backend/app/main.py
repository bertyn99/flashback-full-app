import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import os
import glob

from .services.file_service import FileProcessor
from .services.ai_service import AIProcessor
from .services.video_service import VideoProcessor
from .services.db_service import db_service

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

file_processor = FileProcessor()
ai_processor = AIProcessor()
video_processor = VideoProcessor()

class ProcessingRequest(BaseModel):
    content_type: str  # "VS", "Key Moment", "Key Character", "Quiz"
    start_chapter: int
    end_chapter: int
    generate_all: bool = False

class UploadResponse(BaseModel):
    task_id: str
    chapters: List[str]

@app.get("/api/test")
async def test():
    task_path = "./artifacts/sample"
    image_prompts = []
    for filepath in glob.glob(os.path.join(task_path, "image_prompt_*.txt")):
        with open(filepath, "r") as f:
            image_prompts.append(f.read())
    # Generate image for each prompt
    for idx, prompt in enumerate(image_prompts):
        print("generating image for", idx, prompt)
        image_path = await ai_processor.generate_image(prompt, f"image_{idx}.png", task_path)
        print(image_path)

    # subtitles = open("./artifacts/sample/test.srt", "r").read()
    # srt_dict = await ai_processor.format_srt_to_dict(subtitles)
    # await export_subjects_to_image_prompts(srt_dict)

    return {"message": "ok"}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...)
):
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file name provided")

        # Check file size (optional, example limit of 100MB)
        file.file.seek(0, 2)  # Go to end of file
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file pointer

        if file_size > 100 * 1024 * 1024:  # 100 MB
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB")

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        task_path  = f"./artifacts/{task_id}"
        os.makedirs(task_path, exist_ok=True)

        # Save uploaded file temporarily

        temp_path = f"{task_path}/{file.filename}"
        try:
            with open(temp_path, "wb") as buffer:
                buffer.write(await file.read())
                buffer.close()
        except IOError as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

        # Process file and split into chapters
        try:
            content = await file_processor.process_file(temp_path)
            chapters_of_subject = await ai_processor.generact_list_of_subjects(content)
            print(chapters_of_subject)
        except Exception as e:
            # Clean up temporary file
            os.remove(temp_path)
            raise HTTPException(status_code=422, detail=f"Error processing file: {str(e)}")

        # Store task context in SQLite
        await db_service.store_task(
            task_id=task_id,
            filename=file.filename,
            chapters=[
                {"title": chapter}
                for chapter in chapters_of_subject
            ]
        )

        # Store task context (could use Redis or another state management)
        return UploadResponse(
            task_id=task_id,
            chapters=[chapter for chapter in chapters_of_subject]
        )

    except HTTPException:
        # Re-raise HTTPException to be handled by FastAPI
        raise

    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Ensure file is closed
        if 'file' in locals():
            await file.close()

        # Remove temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/api/seelab")
async def see_lab():
    task_id = str(uuid.uuid4())
    task_path  = f"./artifacts/{task_id}"
    os.makedirs(task_path, exist_ok=True)

    image_url = await ai_processor.generate_image("test", task_path)
    return {"message": image_url}


@app.websocket("/ws/process")
async def websocket_processing(
    websocket: WebSocket,
    task_id: str,
    content_type: str = "KeyMoment",
    start_chapter: int = 0,
    end_chapter: int = 3
):
    # Validate input parameters
    if not task_id:
        await websocket.close(code=4003, reason="Invalid task_id")
        return

    await websocket.accept()
    try:

        # Retrieve stored file and chapters
        chapters = await db_service.get_chapters(task_id)

        print(chapters)

        # Process selected chapters
        selected_chapters = chapters[start_chapter:end_chapter+1]

        print(selected_chapters)
        for idx, chapter in enumerate(selected_chapters):
            # Update progress
            await websocket.send_json({
                "status": "processing",
                "chapter": idx + 1,
                "total_chapters": len(selected_chapters)
            })

            # Generate script based on content type
            script = await ai_processor.generate_script(
                chapter,
                content_type=content_type
            )

            # Generate voiceover
            audio_path = await ai_processor.generate_voiceover(script)

            # Generate subtitles
            subtitles = await ai_processor.generate_subtitles(audio_path)

            # format srt to python dict of subtitles
            srt_dict = await ai_processor.format_srt_to_dict(subtitles)
            await export_subjects_to_image_prompts(srt_dict)

            # Generate image/visual
            image_prompts = []
            for filepath in glob.glob(os.path.join(task_path, "image_prompt_*.txt")):
                with open(filepath, "r") as f:
                    image_prompts.append(f.read())

            # Generate image for each prompt
            for idx, prompt in enumerate(image_prompts):
                image_path = await ai_processor.generate_image(prompt, f"image_{idx}.png", task_path)

            # Merge into video
            video_path = await video_processor.create_video(
                script,
                audio_path,
                subtitles,
                image_path
            )

            # Send video path
            await websocket.send_json({
                "status": "chapter_complete",
                "video_path": video_path,
                "chapter_title": chapter.title
            })

            # Optional: small delay between chapters
            await asyncio.sleep(1)

        # Final completion message
        await websocket.send_json({
            "status": "completed",
            "message": "All chapters processed successfully"
        })

    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()

# Helper function to retrieve task context (would be more robust with actual state management)
async def get_chapters_for_task(task_id: str):
    # In a real implementation, this would fetch from a persistent store
    # For now, we'll use a simple in-memory approach
    # You'd want to implement proper task/state management
    pass

async def export_subjects_to_image_prompts(subjects: List[str], output_dir: str = "./artifacts/sample") -> None:
    """Export each subject to an image prompt file in the specified directory"""
    for idx, subject in enumerate(subjects):
        image_prompt = await ai_processor.prepare_image_prompt(subject)
        print(image_prompt)
        filename = f"{output_dir}/image_prompt_{idx}.txt"
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(image_prompt)
        print(image_prompt)
        await asyncio.sleep(3)

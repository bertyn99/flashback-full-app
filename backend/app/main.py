# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .services.file_service import FileProcessor
from .services.ai_service import AIProcessor
from .models import ProcessingResult
import tempfile
import os

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

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    """     # Process in background
    background_tasks.add_task(process_document, temp_path) 
    """
    
    
    return {"message": "Processing started", "status": "pending"}

async def process_document(file_path: str):
    try:
        # Extract content
        content = await file_processor.process_file(file_path)
        chapters = file_processor.split_into_chapters(content)
        
        results = []
        for chapter in chapters:
            # Generate script
            script = await ai_processor.generate_script(chapter)
            
            # Generate voice over
            audio_path = await ai_processor.generate_voiceover(script)
            
            # Generate subtitles
            subtitles = await ai_processor.generate_subtitles(audio_path)
            
            results.append(ProcessingResult(
                chapter=chapter,
                script=script,
                audio_url=audio_path,
                subtitles=subtitles
            ))
            
        # Clean up temporary file
        os.unlink(file_path)
        
        # Store results or emit via WebSocket
        return results
        
    except Exception as e:
        print(f"Error processing document: {e}")
        raise

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    # Implement status checking logic
    pass
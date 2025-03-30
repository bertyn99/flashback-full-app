from pydantic_ai import Agent  
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider
from elevenlabs import ElevenLabs, save
import httpx
import os
import uuid
from typing import Any, Dict
from ..config import settings

class AIProcessor:
    def __init__(self):
        # Initialize Mistral model with PydanticAI
        self.mistral_model = MistralModel(
            'mistral-large-latest',
            provider=MistralProvider(api_key=settings.MISTRAL_API_KEY)
        )
        self.agent = Agent(self.mistral_model)
        
        self.elevenlabs_client =  ElevenLabs(
    api_key=os.getenv(settings.ELEVEN_API_KEY),
)
        # Gladia API configuration
        self.gladia_api_key = settings.GLADIA_API_KEY
        self.gladia_base_url = "https://api.gladia.io/v2/"
        
    async def generate_script(self, chapter_title: str, chapter_content: str) -> Dict[str, Any]:
        """Generate content using Mistral AI through PydanticAI"""
        prompt = f"""
        Create engaging content for:
        Title: {chapter_title}
        Content: {chapter_content}
        
        Please structure the response with natural sections for scene descriptions, 
        narration points, and key elements to emphasize.
        """
        
        result = await self.agent.run(prompt)
        return result.data  # Returns parsed response from Mistral
    
    async def generate_voiceover(self, text: str) -> str:
        """Generate voice over using Eleven Labs"""
        audio = self.elevenlabs_client.text_to_speech.convert(
            text=text,
            voice="Josh",
            model="eleven_multilingual_v2"
        )
        
        # Save audio file and return path
        audio_path = f"audio_{uuid.uuid4()}.mp3"
        save(audio, audio_path)
        return audio_path
    
    async def generate_subtitles(self, audio_path: str) -> Dict[str, Any]:
        """Generate subtitles using Gladia API via HTTP"""
        async with httpx.AsyncClient() as client:
            # Prepare the audio file for upload
            with open(audio_path, "rb") as audio_file:
                files = {"audio": ("audio.mp3", audio_file, "audio/mpeg")}
                
                headers = {
                    "X-API-Key": self.gladia_api_key
                }
                
                # Make the transcription request
                response = await client.post(
                    f"{self.gladia_base_url}transcription",
                    headers=headers,
                    files=files
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    # Handle error cases
                    response.raise_for_status()
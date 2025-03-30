from pydantic_ai import Agent  
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider
from elevenlabs import ElevenLabs, save
import httpx
import os
import uuid
from typing import Any, Dict
from ..models import Chapter
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
        
    async def generate_script(
        self, 
        chapter: Chapter, 
        content_type: str
    ) -> str:
        """Generate script based on content type"""
        prompt_templates = {
            "VS": self._generate_vs_script,
            "KeyMoment": self._generate_key_moment_script,
            "KeyCharacter": self._generate_character_script,
            "Quiz": self._generate_quiz_script
        }
        
        # Select appropriate prompt generator
        generator = prompt_templates.get(content_type, self._generate_default_script)
        
        return await generator(chapter)
    
    async def generate_voiceover(self, text: str) -> str:
        """Generate voice over using Eleven Labs"""
        audio = self.elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id="Chris",
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
                    
   
    
    async def _generate_vs_script(self, chapter):
        # VS-specific script generation logic
        agent=Agent(model="mistral-large-latest",  system_prompt="Generate a list of subjects from the given content.")
        list_of_subject = await agent.run(chapter)
        return list_of_subject
    
    async def _generate_key_moment_script(self, chapter):
        # Key Moment specific script generation
        pass
    
    async def _generate_character_script(self, chapter):
        # Character focus script generation
        pass
    
    async def _generate_quiz_script(self, chapter):
        # Quiz script generation
        pass
    
    async def _generate_default_script(self, chapter):
        # Fallback script generation
        agent=Agent(model="mistral-large-latest",  system_prompt="Generate a list of subjects from the given content.")
        default_scrypt = await agent.run(chapter)
        return default_scrypt
    
    async def generate_image(self, script: str, content_type: str) -> str:
        """Generate image based on script and content type"""
        # Use an image generation service like DALL-E, Midjourney, etc.
        pass
    
    async def generact_list_of_subject(self, content:str):
        """
        Generate a list of subjects from the given content using Mistral AI.
        """
        agent=Agent(model="mistral-large-latest",  system_prompt="Generate a list of subjects from the given content.")
        list_of_subject = await agent.run(content)
        return list_of_subject
  
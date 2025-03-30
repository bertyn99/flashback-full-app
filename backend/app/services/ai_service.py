from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider
from elevenlabs import ElevenLabs, save
import httpx
import requests
import os
import uuid
from typing import Any, Dict, List
from ..models import Chapter
from ..config import settings
from .file_service import FileProcessor

file_processor = FileProcessor()

class AIProcessor:
    def __init__(self):
        # Initialize Mistral model with PydanticAI
        self.mistral_model = MistralModel(
            'mistral-small-latest',
            provider=MistralProvider(api_key=settings.MISTRAL_API_KEY)
        )
        self.agent = Agent(self.mistral_model)
        self.elevenlabs_client =  ElevenLabs(api_key=settings.ELEVEN_API_KEY)
        # Gladia API configuration
        self.gladia_api_key = settings.GLADIA_API_KEY
        self.gladia_base_url = "https://api.gladia.io/v2/"

        self.seelab_api_key = settings.SEELAB_API_KEY

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
            voice_id="iP95p4xoKVk53GoZ742B",
            model_id="eleven_multilingual_v2"
        )

        # Save audio file and return path
        audio_path = f"/videos/audio/audio_{uuid.uuid4()}.mp3"
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
        agent=Agent(
            model="mistral-large-latest",
            system_prompt="Generate a list of subjects from the given content."
        )
        list_of_subject = await agent.run(chapter)
        return list_of_subject

    async def _generate_key_moment_script(self, chapter):
        agent=Agent(self.mistral_model, system_prompt= f"""
enrich the content and create a short script for a Short Video to explain the subject in a fun way.
The complete vocal script must not have more than 300 words. Always include a date. Additionally, include important people or events.
Keep the content in French.

The output must be a simple text containing the paragraphs, without sections.
For this historical subject:""")
        default_scrypt = await agent.run(chapter)
        return default_scrypt.data

    async def _generate_character_script(self, chapter):
        # Character focus script generation
        pass

    async def _generate_quiz_script(self, chapter):
        # Quiz script generation
        pass

    async def _generate_default_script(self, chapter):
        # Fallback script generation
        agent=Agent(self.mistral_model, system_prompt= f"""
enrich the content and create a short script for a Short Video to explain the subject in a fun way.
The complete vocal script must not have more than 300 words. Always include a date. Additionally, include important people or events.
Keep the content in French.

The output must be a simple text containing the paragraphs, without sections.
For this historical subject:""")
        default_scrypt = await agent.run(chapter)
        return default_scrypt

    async def generate_image(self, script: str, task_path: str) -> str:
        """Generate image based on script and content type"""
        # Use an image generation service like Seelab, DALL-E, Midjourney, etc.
        url = "https://app.seelab.ai/api/predict/text-to-image"
        payload = {
            "async": False,
            "styleId": 1003,
            "params": {
                "prompt": script,
                "samples": "1",
                "seed": 0,
                "aspectRatio": "1:1"
            }
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Token {self.seelab_api_key}"
        }
        response = requests.post(url, json=payload, headers=headers)
        json_response = response.json()
        image_url = json_response["result"]["image"][0]["url"]

        await file_processor.download_image(image_url, "image.png", task_path)

        return image_url


    async def generact_list_of_subject(self, content:str):
        """
        Generate a list of subjects from the given content using Mistral AI.
        """
        agent=Agent(
            self.mistral_model,
            result_type=List[str],
            system_prompt= f"""
Generate a list of key subjects from the given content give enough info about the subject and dont repeat key subject
each need to be unique in the list.The need subject need to have at least 2 word and need to be enough comprehensible
if we need to generate a short video about it. Gave just the list of subject.""")
        list_of_subject = await agent.run(content)
        return list_of_subject.data

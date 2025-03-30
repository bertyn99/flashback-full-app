from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider
from mistralai import Mistral
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
        self.mistral_model = MistralModel(
            "mistral-small-latest",
            provider=MistralProvider(api_key=settings.MISTRAL_API_KEY)
        )
        self.agent = Agent(self.mistral_model)
        self.mistral_client = Mistral(api_key=settings.MISTRAL_API_KEY)

        self.elevenlabs_client =  ElevenLabs(api_key=settings.ELEVEN_API_KEY)
        self.elevenlabs_voice_id = settings.ELEVEN_VOICE_ID
        self.elevenlabs_model = "eleven_multilingual_v2"

        self.gladia_api_key = settings.GLADIA_API_KEY
        self.gladia_base_url = "https://api.gladia.io/v2/"

        self.seelab_api_key = settings.SEELAB_API_KEY
        self.seelab_style_id = 1003 # Flux HD

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
            voice_id=self.eleven_voice_id,
            model_id=self.elevenlabs_model
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

    async def format_srt_to_dict(self, subtitles: str) -> Dict[str, Any]:
        """Format subtitles from SRT format to a dictionary"""
        agent=Agent(self.mistral_model, system_prompt= f"""
Extract all the sentences from the given content.
Ignore timecodes, index numbers, and formatting tags.
Output only a Python list of strings, where each string is a sentence from the subtitles.
Return only the list, no explanation or extra text.

the content of the srt file:""")
        default_scrypt = await agent.run(subtitles)
        return default_scrypt.data

    async def prepare_image_prompt(self, subject: str) -> Dict[str, Any]:
        print("preparing image prompt for subject:", subject)
        """Prepare image prompt for the given subject"""
        chatResponse = await self.mistral_client.agents.complete_async(messages=[
            {
                "content": subject,
                "role": "user",
            },
        ], agent_id=settings.MISTRAL_AGENT_IMAGE_PROMPT)
        return chatResponse.choices[0].message.content

    async def _generate_vs_script(self, chapter):
        # VS-specific script generation logic
        agent=Agent(self.mistral_model, system_prompt="Generate a list of subjects from the given content.")
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
        agent=Agent(model=self.mistral_model, system_prompt= f"""
enrich the content and create a short script for a Short Video to explain the subject in a fun way.
The complete vocal script must not have more than 300 words. Always include a date. Additionally, include important people or events.
Keep the content in French.

The output must be a simple text containing the paragraphs, without sections.
For this historical subject:""")
        default_scrypt = await agent.run(chapter)
        return default_scrypt

    async def generate_image(self, script: str, filename: str, task_path: str) -> str:
        """Generate image based on script and content type"""
        # Use an image generation service like Seelab, DALL-E, Midjourney, etc.
        url = "https://app.seelab.ai/api/predict/text-to-image"
        payload = {
            "async": False,
            "styleId": self.seelab_style_id,
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

        await file_processor.download_image(image_url, filename, task_path)

        return image_url


    async def generact_list_of_subject(self, content:str):
        """
        Generate a list of subjects from the given content using Mistral AI.
        """
        agent=Agent(self.mistral_model, result_type=List[str], system_prompt= f"""
Generate a list of key subjects from the given content, give enough info about the subject and don't repeat key subjects.
Every subject has to be unique in the list.
The subject needs to have at least 2 words and should be understandable.
If we need to generate a short video about it.
Give just the list of subjects.""")
        list_of_subject = await agent.run(content)
        return list_of_subject.data

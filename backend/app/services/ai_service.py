import asyncio
import json
import mimetypes
from google import genai
from google.genai import types
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
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

class Scene(BaseModel):
    prompt: str
    segment: str

class Scenes(BaseModel):
    scenes: List[Scene]
    


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

        self.geminiClient = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )
        self.gemini_api_key = settings.GEMINI_API_KEY

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
        generator = self._generate_key_moment_script#prompt_templates.get(content_type, self._generate_default_script)

        return await self._generate_key_moment_script(chapter)

    async def generate_voiceover(self, text: str,task_id: str, idx: int = 0) -> str:
        """Generate voice over using Eleven Labs"""
        audio = self.elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id=self.elevenlabs_voice_id,
            model_id=self.elevenlabs_model
        )
        
        # Ensure directory exists
        audio_path = f"./artifacts/{task_id}/audio"
        os.makedirs(audio_path, exist_ok=True)
        # Save audio file and return path
        audio_path = f"{audio_path}/audio_{idx}.mp3"
        save(audio, audio_path)
        
        # Upload to R2
        r2_url = await file_processor.upload_to_r2(
                audio_path,
                content_type="audio/mpeg"
            )
        return r2_url

    async def generate_subtitles(self, audio_path: str) -> Dict[str, Any]:
        """Generate subtitles using Gladia API via HTTP"""
    
        try:
        # Prepare the audio file for upload
            # Upload the file
            headers = {
                "Content-Type": "application/json",
                "x-gladia-key": self.gladia_api_key
            }
            
            # Additional parameters for transcription if needed
            data = {
                "audio_url": audio_path,
                "language": "fr",  # Assuming French based on your script generation
                # "sentences": True
            }
            
            print(data)
    
            # Make the transcription request
            response = requests.post(
                f"{self.gladia_base_url}pre-recorded",
                headers=headers,
                json=data
            )
            
            print(f"Gladia API response status: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                transcription_id = result.get("id")
                return await self._poll_transcription_status(transcription_id, headers)
          
            else:
                print(f"Error response: {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as e:
            print(f"Unexpected error: {e}")

            if response.status_code == 200:
                return response.json()
            else:
                    # Handle error cases
                response.raise_for_status()
                
    async def _poll_transcription_status(self, transcription_id: str, headers: dict|None = None) -> Dict[str, Any]:
        """Poll for transcription status"""
        max_attempts = 30  # Maximum number of polling attempts
        poll_interval = 2  # Seconds between polls
        
        for attempt in range(max_attempts):
            try:
                if headers is None:
                    baseHeader = {
                        "Content-Type": "application/json",
                        "x-gladia-key": self.gladia_api_key
                    }
                else:
                    baseHeader = headers
                
                response = requests.get(
                    f"{self.gladia_base_url}pre-recorded/{transcription_id}",
                    headers=baseHeader
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "done":
                        return result
                    elif status == "error":
                        raise Exception(f"Transcription failed: {result.get('error')}")
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Error polling transcription status: {e}")
                raise
        
        raise Exception("Transcription timed out")

    async def format_srt_to_dict(self, subtitles: List[Dict[str, Any]]) -> List[str]:
        """Extract text from subtitles array
        
        Args:
            subtitles: List of subtitle objects with 'text' field obtained from gladia
            
        Returns:
            List of extracted text strings
        """
        return [subtitle["text"] for subtitle in subtitles]

    # TODO : 
    async def prepare_scene_prompt(self, subject: str) -> any:
        
        """Prepare image prompt for the given subject"""
        chatResponse = await self.mistral_client.agents.complete_async(messages=[
            {
                "role": "user",
                "content": subject,
               
            },
        ],response_format={"type": "json_object"}
          , agent_id=settings.MISTRAL_AGENT_IMAGE_PROMPT)
        
        # Get the response content and parse it as JSON
        response_content = chatResponse.choices[0].message.content
        if isinstance(response_content, str):
            scenes = json.loads(response_content)
        else:
            scenes = response_content # If it's already a dict/list
        return scenes

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
For this  subject:""")
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
For this subject:""")
        default_scrypt = await agent.run(chapter)
        return default_scrypt

    async def generate_image(self, script: str, filename: str, task_path: str) -> str:
        """Generate image based on script and content type"""
        # Use an image generation service like Gemini, Seelab, DALL-E, Midjourney, etc.
        model = "gemini-2.0-flash-exp"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=script),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "image",
                "text",
            ],
            response_mime_type="text/plain",
        )

        pathImge=""
        for chunk in self.geminiClient.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):  
            if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                continue
            if chunk.candidates[0].content.parts[0].inline_data:
        
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)

                pathImge = f"{task_path}/{filename}{file_extension}"
                f = open(pathImge, "wb")
                f.write(inline_data.data)
                f.close()
                print(
                    "File of mime type"
                    f" {inline_data.mime_type} saved"
                    f"to: {filename}"
                )
            else:
                print(chunk.text)
            
        return pathImge
      

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

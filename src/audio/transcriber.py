import os
from groq import Groq
from src.config import STT_MODEL


class AudioTranscriber:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def transcribe(self, file_path, glossary: str = "") -> str:
        file_path = str(file_path)
        with open(file_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(os.path.basename(file_path), file.read()),
                model=STT_MODEL,
                language="uk",          # без автовизначення мови
                prompt=glossary,        # імена та назви проєктів
                temperature=0,
            )
        return transcription.text

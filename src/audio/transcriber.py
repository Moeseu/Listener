import os
from groq import Groq

class AudioTranscriber:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def transcribe(self, file_path: str) -> str:
        with open(file_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
              file=(file_path, file.read()),
              model="whisper-large-v3",
            )
        return transcription.text
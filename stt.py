# stt.py - UPDATED FOR AvalAI
import tempfile
import os
from openai import OpenAI
from config import AVALAIGPT_API_KEY  # ✅ تغییر نام

client = OpenAI(
    api_key=AVALAIGPT_API_KEY,  # ✅ تغییر نام
    base_url="https://api.avalai.ir/v1"  # ✅ آدرس جدید
)

async def voice_to_text(voice_file) -> str:
    """
    Download telegram voice file and convert to text via Whisper
    """

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
        temp_path = temp_audio.name

    # ✅ async download
    await voice_file.download_to_drive(temp_path)

    try:
        with open(temp_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        return transcription.text.strip()

    except Exception as e:
        print("STT ERROR:", e)
        return ""

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

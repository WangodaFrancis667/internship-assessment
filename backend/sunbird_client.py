"""
Thin wrapper around Sunbird AI API endpoints.
Handles authentication, request formatting, and error propagation.
"""

import os
import requests
from typing import Optional

SUNBIRD_BASE_URL = "https://api.sunbird.ai"

SPEAKER_IDS = {
    "lug": 248,   # Luganda - Female
    "nyn": 243,   # Runyankole - Female
    "teo": 242,   # Ateso - Female
    "lgg": 245,   # Lugbara - Female
    "ach": 241,   # Acholi - Female
}

LANGUAGE_NAMES = {
    "lug": "Luganda",
    "nyn": "Runyankole",
    "teo": "Ateso",
    "lgg": "Lugbara",
    "ach": "Acholi",
}


def _get_headers(content_type: Optional[str] = "application/json") -> dict:
    token = os.environ.get("SUNBIRD_API_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribe an audio file to text using Sunbird STT.
    Returns the transcribed text string.
    Raises RuntimeError on API failure.
    """
    url = f"{SUNBIRD_BASE_URL}/tasks/stt"
    files = {"audio": (filename, audio_bytes)}
    headers = _get_headers(content_type=None)  # multipart, no content-type header

    response = requests.post(url, files=files, headers=headers, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"STT failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    text = data.get("output", {}).get("text", "")
    if not text:
        raise RuntimeError("STT returned empty transcript.")
    return text


def summarise_text(text: str) -> str:
    """
    Summarise text using the Sunbird summarisation endpoint.
    Returns the summary string.
    """
    url = f"{SUNBIRD_BASE_URL}/tasks/summarise"
    payload = {"text": text}
    response = requests.post(url, json=payload, headers=_get_headers(), timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Summarisation failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    summary = data.get("output", {}).get("summary", "")
    if not summary:
        raise RuntimeError("Summarisation returned empty result.")
    return summary


def translate_text(text: str, target_language: str) -> str:
    """
    Translate text into a target Ugandan language using Sunflower LLM.
    target_language: one of 'lug', 'nyn', 'teo', 'lgg', 'ach'
    Returns translated text.
    """
    lang_name = LANGUAGE_NAMES.get(target_language, target_language)
    url = f"{SUNBIRD_BASE_URL}/tasks/sunflower_simple"
    instruction = (
        f"Translate the following English text into {lang_name}. "
        f"Return ONLY the translated text, nothing else.\n\n"
        f"Text: {text}"
    )
    payload = {"instruction": instruction, "model_type": "qwen", "temperature": 0.2}
    response = requests.post(url, json=payload, headers=_get_headers(), timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"Translation failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    # Response shape: {"output": {"role": "assistant", "content": "..."}}
    output = data.get("output", {})
    if isinstance(output, dict):
        translated = output.get("content", "")
    else:
        translated = str(output)

    if not translated:
        raise RuntimeError("Translation returned empty result.")
    return translated.strip()


def synthesise_speech(text: str, language_code: str) -> str:
    """
    Convert text to speech in the given language.
    Returns the audio_url from Sunbird TTS.
    """
    speaker_id = SPEAKER_IDS.get(language_code)
    if speaker_id is None:
        raise ValueError(f"No speaker ID found for language: {language_code}")

    url = f"{SUNBIRD_BASE_URL}/tasks/tts"
    payload = {"text": text, "speaker_id": speaker_id}
    response = requests.post(url, json=payload, headers=_get_headers(), timeout=120)

    if response.status_code != 200:
        raise RuntimeError(
            f"TTS failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    audio_url = data.get("output", {}).get("audio_url", "")
    if not audio_url:
        raise RuntimeError("TTS returned no audio URL.")
    return audio_url
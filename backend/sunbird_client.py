"""
Sunbird AI API client with retry logic and comprehensive error handling.
Properly handles all endpoint response formats.
"""

import os
import json
import time
import requests
from pathlib import Path

BASE_URL = "https://api.sunbird.ai"

# Timeout configuration
TIMEOUT_STT = 600  # 10 minutes for audio transcription
TIMEOUT_DEFAULT = 300  # 5 minutes for other endpoints

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds

# TTS speaker IDs per language (using language names as keys)
SPEAKER_IDS = {
    "Luganda": 248,
    "Acholi": 241,
    "Ateso": 242,
    "Runyankole": 243,
    "Lugbara": 245,
}

# Language code to name mapping for STT results
LANGUAGE_NAMES = {
    "lug": "Luganda",
    "ach": "Acholi",
    "teo": "Ateso",
    "nyn": "Runyankole",
    "lgg": "Lugbara",
    "eng": "English",
}


def _headers_json() -> dict:
    """Return headers for JSON requests."""
    token = os.environ.get("SUNBIRD_API_TOKEN", "")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _headers_auth() -> dict:
    """Return headers for multipart/file uploads."""
    token = os.environ.get("SUNBIRD_API_TOKEN", "")
    return {"Authorization": f"Bearer {token}"}


def _request_with_retry(
    method: str, url: str, timeout: int, headers: dict, **kwargs
) -> requests.Response:
    """
    Make HTTP request with exponential backoff retry on transient errors.

    Args:
        method: HTTP method ('post', 'get', etc.)
        url: Request URL
        timeout: Timeout in seconds
        headers: Request headers
        **kwargs: Additional arguments for requests (json, files, data, etc.)

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    backoff = INITIAL_BACKOFF
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            print(
                f"[RETRY] Attempt {attempt + 1}/{MAX_RETRIES} to {method.upper()} {url}"
            )
            response = requests.request(
                method=method, url=url, timeout=timeout, headers=headers, **kwargs
            )

            # Don't raise on non-200 status codes yet; let caller handle
            if response.status_code >= 500:
                # Server error; might be transient, retry
                if attempt < MAX_RETRIES - 1:
                    print(
                        f"[RETRY] Server error {response.status_code}. Retrying in {backoff}s..."
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

            return response

        except (requests.Timeout, requests.ConnectionError) as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                print(f"[RETRY] {type(e).__name__}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
            else:
                raise
        except requests.RequestException as e:
            raise

    if last_exception:
        raise last_exception


def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe an audio file using Sunbird STT.

    Args:
        audio_path: Path to audio file

    Returns:
        {"text": str, "language_code": str, "language_name": str}

    Raises:
        RuntimeError or requests.RequestException on error
    """
    url = f"{BASE_URL}/tasks/stt"
    print(f"[STT] Transcribing audio from: {audio_path}")

    try:
        with open(audio_path, "rb") as f:
            files = {"audio": (Path(audio_path).name, f)}
            response = _request_with_retry(
                method="post",
                url=url,
                timeout=TIMEOUT_STT,
                headers=_headers_auth(),
                files=files,
            )
    except Exception as e:
        raise RuntimeError(f"STT API request failed: {str(e)}")

    if response.status_code != 200:
        raise RuntimeError(f"STT failed ({response.status_code}): {response.text}")

    data = response.json()
    print(f"[STT] Response: {json.dumps(data, indent=2)}")

    output = data.get("output", {})
    lang_code = output.get("language", "")
    text = output.get("text", "")

    if not text:
        raise RuntimeError(
            f"STT returned empty transcript. Response: {json.dumps(data, indent=2)}"
        )

    return {
        "text": text,
        "language_code": lang_code,
        "language_name": LANGUAGE_NAMES.get(lang_code, lang_code),
    }


def summarise_text(text: str) -> str:
    """
    Summarise text using the Sunbird summarisation endpoint.

    Args:
        text: Text to summarise

    Returns:
        Summary string

    Raises:
        RuntimeError or requests.RequestException on error
    """
    url = f"{BASE_URL}/tasks/summarise"
    payload = {"text": text}
    print(f"[SUMMARISE] Summarising {len(text)} chars...")

    try:
        response = _request_with_retry(
            method="post",
            url=url,
            timeout=TIMEOUT_DEFAULT,
            headers=_headers_json(),
            json=payload,
        )
    except Exception as e:
        raise RuntimeError(f"Summarisation API request failed: {str(e)}")

    if response.status_code != 200:
        raise RuntimeError(
            f"Summarisation failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    print(f"[SUMMARISE] Response: {json.dumps(data, indent=2)}")

    # Try multiple response formats based on API documentation
    summary = None

    if "summarized_text" in data:
        summary = data.get("summarized_text", "").strip()
    elif "output" in data and "summary" in data["output"]:
        summary = data["output"]["summary"].strip()
    elif "summary" in data:
        summary = data.get("summary", "").strip()
    elif "output" in data and isinstance(data["output"], str):
        summary = data["output"].strip()

    if not summary:
        raise RuntimeError(
            f"Summarisation returned empty result. Response: {json.dumps(data, indent=2)}"
        )

    return summary


def translate_text(text: str, target_language: str) -> str:
    """
    Translate text into a Ugandan local language using Sunflower Chat.

    Args:
        text: Text to translate
        target_language: Target language name (e.g., "Luganda")

    Returns:
        Translated text string

    Raises:
        RuntimeError or requests.RequestException on error
    """
    url = f"{BASE_URL}/tasks/sunflower_inference"
    print(f"[TRANSLATE] Translating {len(text)} chars to {target_language}...")

    system_prompt = (
        f"You are a professional translator. Translate the following text into {target_language}. "
        f"Return ONLY the translated text, with no explanations or extra commentary."
    )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
    }

    try:
        response = _request_with_retry(
            method="post",
            url=url,
            timeout=TIMEOUT_DEFAULT,
            headers=_headers_json(),
            json=payload,
        )
    except Exception as e:
        raise RuntimeError(f"Translation API request failed: {str(e)}")

    if response.status_code != 200:
        raise RuntimeError(
            f"Translation failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    print(f"[TRANSLATE] Response: {json.dumps(data, indent=2)}")

    # Try multiple response formats for Chat Inference
    content = None

    if "output" in data and isinstance(data["output"], dict):
        content = data["output"].get("content", "").strip()
    elif "content" in data:
        content = data.get("content", "").strip()
    elif "generated_text" in data:
        content = data.get("generated_text", "").strip()
    elif "output" in data and isinstance(data["output"], str):
        content = data["output"].strip()

    if not content:
        raise RuntimeError(
            f"Translation returned empty result. Response: {json.dumps(data, indent=2)}"
        )

    return content


def synthesise_speech(text: str, language: str) -> str:
    """
    Convert text to speech using the Sunbird TTS endpoint.

    Args:
        text: Text to synthesise
        language: Language name (e.g., "Luganda")

    Returns:
        Audio URL string

    Raises:
        ValueError if language not supported
        RuntimeError or requests.RequestException on error
    """
    speaker_id = SPEAKER_IDS.get(language)
    if speaker_id is None:
        raise ValueError(f"No TTS speaker available for language: {language}")

    url = f"{BASE_URL}/tasks/tts"
    payload = {"text": text, "speaker_id": speaker_id}
    print(f"[TTS] Synthesising {len(text)} chars with speaker {speaker_id}...")

    try:
        response = _request_with_retry(
            method="post",
            url=url,
            timeout=TIMEOUT_DEFAULT,
            headers=_headers_json(),
            json=payload,
        )
    except Exception as e:
        raise RuntimeError(f"TTS API request failed: {str(e)}")

    if response.status_code != 200:
        raise RuntimeError(f"TTS failed ({response.status_code}): {response.text}")

    data = response.json()
    print(f"[TTS] Response: {json.dumps(data, indent=2)}")

    # Try multiple response formats
    audio_url = None

    if "output" in data and isinstance(data["output"], dict):
        audio_url = data["output"].get("audio_url", "").strip()
    elif "audio_url" in data:
        audio_url = data.get("audio_url", "").strip()
    elif "output" in data and isinstance(data["output"], str):
        audio_url = data["output"].strip()

    if not audio_url:
        raise RuntimeError(
            f"TTS returned empty audio URL. Response: {json.dumps(data, indent=2)}"
        )

    return audio_url

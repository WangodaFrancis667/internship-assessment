"""
Pipeline orchestrator: STT → Summarise → Translate → TTS
Each step is a discrete function so the API can process step-by-step.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from backend.sunbird_client import (
    transcribe_audio,
    summarise_text,
    translate_text,
    synthesise_speech,
)

# 5-minute audio limit in seconds
AUDIO_MAX_SECONDS = 5 * 60


def get_audio_duration(audio_path: str) -> float:
    """Return audio duration in seconds using mutagen (lightweight, no ffmpeg needed)."""
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(audio_path)
        if audio is not None and audio.info is not None:
            return audio.info.length
    except Exception:
        pass
    # Fallback: accept the file (duration check best-effort)
    return 0.0


def run_pipeline(
    input_text: Optional[str] = None,
    audio_path: Optional[str] = None,
    target_language: str = "Luganda",
    story_format: str = "News Bulletin",
) -> dict:
    """
    Run the full pipeline. Provide either input_text or audio_path (not both).

    Args:
        input_text: Text to process (optional if audio_path provided)
        audio_path: Path to audio file (optional if input_text provided)
        target_language: Target language for translation (e.g., "Luganda")
        story_format: Format hint for summarisation ("News Bulletin" or "Community Announcement")

    Returns a dict with keys:
      - transcript (str | None): Transcribed text from audio (None if text input)
      - detected_language (str | None): Detected language from STT
      - summary (str): Summary of the text
      - translation (str): Summary translated to target language
      - audio_url (str): URL to generated audio
      - error (str | None): Error message if any step failed
    """
    result = {
        "transcript": None,
        "detected_language": None,
        "summary": None,
        "translation": None,
        "audio_url": None,
        "error": None,
    }

    try:
        # ── Step 1: Get source text ────────────────────────────────
        if audio_path:
            duration = get_audio_duration(audio_path)
            if duration > AUDIO_MAX_SECONDS:
                raise ValueError(
                    f"Audio is {duration:.0f}s long. Maximum allowed is 5 minutes (300s). "
                    "Please upload a shorter recording."
                )
            stt_result = transcribe_audio(audio_path)
            source_text = stt_result["text"]
            result["transcript"] = source_text
            result["detected_language"] = (
                f"{stt_result['language_name']} ({stt_result['language_code']})"
            )
        elif input_text and input_text.strip():
            source_text = input_text.strip()
        else:
            raise ValueError("Please provide either text input or an audio file.")

        if not source_text.strip():
            raise ValueError(
                "Could not extract any text from the audio. Please try a clearer recording."
            )

        # ── Step 2: Summarise ──────────────────────────────────────
        try:
            summary = summarise_text(source_text)
            result["summary"] = summary
        except Exception as e:
            raise Exception(f"Summarisation step failed: {str(e)}")

        # ── Step 3: Translate ──────────────────────────────────────
        try:
            translation = translate_text(summary, target_language)
            result["translation"] = translation
        except Exception as e:
            raise Exception(f"Translation step failed: {str(e)}")

        # ── Step 4: TTS ────────────────────────────────────────────
        try:
            audio_url = synthesise_speech(translation, target_language)
            result["audio_url"] = audio_url
        except Exception as e:
            raise Exception(f"Text-to-speech step failed: {str(e)}")

    except ValueError as e:
        # Validation errors (e.g., audio too long)
        result["error"] = str(e)
    except Exception as e:
        # API or other errors
        msg = str(e)
        if "timed out" in msg.lower() or "timeout" in msg.lower():
            result["error"] = (
                "The Sunbird API took too long to respond. "
                "This happens occasionally on the free tier — please wait a moment and try again."
            )
        elif "connectionerror" in type(e).__name__.lower():
            result["error"] = (
                "Could not reach the Sunbird API. Please check your internet connection."
            )
        else:
            result["error"] = f"API error: {msg}"

    return result

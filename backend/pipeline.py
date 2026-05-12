"""
Pipeline orchestrator: STT → Summarise → Translate → TTS
Each step is a discrete function so the API can stream results step-by-step.
"""

import io
from typing import Optional
from backend.sunbird_client import (
    transcribe_audio,
    summarise_text,
    translate_text,
    synthesise_speech,
)

MAX_AUDIO_DURATION_SECONDS = 5 * 60  # 5 minutes


def validate_audio_duration(audio_bytes: bytes) -> None:
    """
    Check that the uploaded audio does not exceed MAX_AUDIO_DURATION_SECONDS.
    Uses mutagen if available, otherwise silently skips.
    """
    try:
        from mutagen import File as MutagenFile

        audio_file = MutagenFile(io.BytesIO(audio_bytes))
        if audio_file is not None and hasattr(audio_file, "info"):
            duration = audio_file.info.length
            if duration > MAX_AUDIO_DURATION_SECONDS:
                raise ValueError(
                    f"Audio is {duration / 60:.1f} minutes long. "
                    f"Please upload a file under 5 minutes."
                )
    except ImportError:
        pass  # mutagen not available; skip duration check


def run_pipeline(
    text_input: Optional[str],
    audio_bytes: Optional[bytes],
    audio_filename: Optional[str],
    target_language: str,
) -> dict:
    """
    Runs the full pipeline and returns a dict with all intermediate and final results.
    Either text_input or audio_bytes must be provided, not both.

    Returns:
        {
            "transcript": str | None,
            "source_text": str,
            "summary": str,
            "translation": str,
            "audio_url": str,
        }
    """
    result = {
        "transcript": None,
        "source_text": "",
        "summary": "",
        "translation": "",
        "audio_url": "",
    }

    # ── Step 1: Input ────────────────────────────────────────────
    if audio_bytes:
        validate_audio_duration(audio_bytes)
        transcript = transcribe_audio(audio_bytes, filename=audio_filename or "audio.wav")
        result["transcript"] = transcript
        result["source_text"] = transcript
    elif text_input:
        result["source_text"] = text_input.strip()
    else:
        raise ValueError("Provide either text or an audio file.")

    # ── Step 2: Summarise ────────────────────────────────────────
    summary = summarise_text(result["source_text"])
    result["summary"] = summary

    # ── Step 3: Translate ────────────────────────────────────────
    translation = translate_text(summary, target_language)
    result["translation"] = translation

    # ── Step 4: TTS ──────────────────────────────────────────────
    audio_url = synthesise_speech(translation, target_language)
    result["audio_url"] = audio_url

    return result
"""
Text-to-speech with three pluggable backends, selected via config.TTS_PROVIDER:

- "offline"    : pyttsx3 -- zero setup, no internet, no API key. Robotic
                 voice but guarantees the pipeline always works, including
                 as a fallback during a live demo with no wifi.
- "gtts"       : Google Translate TTS -- decent quality, wide language
                 support, no API key needed, requires internet.
- "elevenlabs" : Best quality + natural multilingual voices. Requires
                 ELEVENLABS_API_KEY.

All three expose the same synthesize(text, language, out_path) -> path signature.
"""
from __future__ import annotations
import os
import config

# Common language-name -> code mapping used by gTTS / ElevenLabs multilingual models
LANGUAGE_CODES = {
    "english": "en", "hindi": "hi", "hinglish": "hi", "marathi": "mr",
    "tamil": "ta", "telugu": "te", "bengali": "bn", "gujarati": "gu",
    "kannada": "kn", "malayalam": "ml", "punjabi": "pa", "urdu": "ur",
    "spanish": "es", "french": "fr", "german": "de",
}


def _lang_code(language: str) -> str:
    return LANGUAGE_CODES.get(language.strip().lower(), "en")


def synthesize(text: str, language: str, out_path: str) -> str:
    provider = config.TTS_PROVIDER
    if provider == "offline":
        return _synthesize_offline(text, out_path)
    elif provider == "gtts":
        return _synthesize_gtts(text, language, out_path)
    elif provider == "elevenlabs":
        return _synthesize_elevenlabs(text, language, out_path)
    raise ValueError(f"Unknown TTS_PROVIDER: {provider}")


def _synthesize_offline(text: str, out_path: str) -> str:
    import pyttsx3
    engine = pyttsx3.init()
    engine.save_to_file(text, out_path)
    engine.runAndWait()
    return out_path


def _synthesize_gtts(text: str, language: str, out_path: str) -> str:
    from gtts import gTTS
    tts = gTTS(text=text, lang=_lang_code(language))
    tts.save(out_path)
    return out_path


def _synthesize_elevenlabs(text: str, language: str, out_path: str) -> str:
    if not config.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not set. Add it to your .env file, "
                            "or set TTS_PROVIDER=gtts / offline instead.")
    import requests
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path

"""
Central configuration for the AI Teacher app.
All API keys are read from environment variables (set them in a .env file
in this folder, or export them in your shell before running).

Nothing in this file is a secret itself -- it just wires up which
provider to use and reads keys from the environment.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---- LLM provider -----------------------------------------------------
# Choose "anthropic", "openai", or "gemini". This drives lesson planning,
# script generation, and answer evaluation.
# "gemini" is the free option -- Google AI Studio gives a no-card-required
# free tier (Flash models), good enough for hackathon testing/demo.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---- Text-to-Speech -----------------------------------------------------
# "offline"  -> pyttsx3, works with no internet / no API key (robotic but reliable demo fallback)
# "gtts"     -> Google Translate TTS, needs internet, no API key, better quality
# "elevenlabs" -> best quality + multilingual, needs ELEVENLABS_API_KEY
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "gtts")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # default demo voice

# ---- Avatar video -----------------------------------------------------
# "slides"  -> no external service: renders narrated slide video (works offline, always available)
# "did"     -> D-ID talking-avatar API, needs DID_API_KEY
# "heygen"  -> HeyGen API, needs HEYGEN_API_KEY
AVATAR_PROVIDER = os.getenv("AVATAR_PROVIDER", "slides")
DID_API_KEY = os.getenv("DID_API_KEY", "")
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
AVATAR_IMAGE_PATH = os.getenv("AVATAR_IMAGE_PATH", "assets/default_avatar.png")

# ---- Storage -----------------------------------------------------
DATA_DIR = os.getenv("DATA_DIR", "data")
PROFILE_STORE_PATH = os.path.join(DATA_DIR, "learner_profiles.json")
MEDIA_DIR = os.path.join(DATA_DIR, "media")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

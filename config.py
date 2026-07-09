import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SAMPLE_RATE = 16000
VAD_FRAME_SAMPLES = 480          # 30ms @ 16kHz
SILENCE_FRAMES_TRIGGER = 20      # 20 × 30ms = 600ms silence → flush
SILENCE_THRESHOLD = 0.004        # RMS energy threshold
MAX_CHUNK_SECONDS = 12
MIN_CHUNK_SECONDS = 0.4

TTS_VOICE_INCOMING = "nova"      # Ukrainian voice (other person → UA)
TTS_VOICE_OUTGOING = "onyx"      # Target-lang voice (user UA → other lang)
TTS_SAMPLE_RATE = 24000          # OpenAI TTS PCM output rate

LANG_NAMES = {
    "en": "English", "de": "German", "fr": "French",
    "pl": "Polish",  "es": "Spanish", "it": "Italian",
    "ja": "Japanese", "zh": "Chinese", "ko": "Korean",
    "pt": "Portuguese", "nl": "Dutch", "uk": "Ukrainian",
}

from __future__ import annotations
import io
import queue
import threading
import wave
import numpy as np
import sounddevice as sd
from openai import OpenAI
from config import (OPENAI_API_KEY, SAMPLE_RATE, LANG_NAMES,
                    TTS_VOICE_INCOMING, TTS_VOICE_OUTGOING, TTS_SAMPLE_RATE)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# ── Per-device playback queues so concurrent TTS on different devices don't clash ──
_play_queues: dict[str, queue.Queue] = {}
_play_queue_lock = threading.Lock()


def _ensure_player(device_key: str, device):
    with _play_queue_lock:
        if device_key in _play_queues:
            return
        q: queue.Queue = queue.Queue()
        _play_queues[device_key] = q

        def _player():
            while True:
                item = q.get()
                if item is None:
                    return
                audio_data, dev = item
                try:
                    sd.play(audio_data, samplerate=TTS_SAMPLE_RATE, device=dev)
                    sd.wait()
                except Exception as exc:
                    print(f"[Playback error] {exc}")

        threading.Thread(target=_player, daemon=True, name=f"Player-{device_key}").start()


def _audio_to_wav(audio: np.ndarray) -> io.BytesIO:
    buf = io.BytesIO()
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    buf.seek(0)
    buf.name = "audio.wav"
    return buf


def transcribe(audio: np.ndarray, language: str | None = None) -> tuple[str, str]:
    """Returns (transcript, detected_language). language=None → Whisper auto-detects."""
    wav = _audio_to_wav(audio)
    kwargs: dict = {"model": "whisper-1", "file": wav, "response_format": "verbose_json"}
    if language and language != "auto":
        kwargs["language"] = language
    try:
        result = _get_client().audio.transcriptions.create(**kwargs)
        return result.text.strip(), result.language or ""
    except Exception as exc:
        print(f"[Whisper error] {exc}")
        return "", ""


def translate(text: str, to_lang: str) -> str:
    if not text:
        return ""
    lang_name = LANG_NAMES.get(to_lang, to_lang)
    try:
        resp = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": f"Translate to {lang_name}. Output only the translation, nothing else."},
                {"role": "user", "content": text},
            ],
            max_tokens=500,
            temperature=0.1,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[GPT error] {exc}")
        return ""


def speak(text: str, voice: str = TTS_VOICE_INCOMING, device=None):
    """Non-blocking TTS playback queued per device."""
    if not text:
        return
    device_key = str(device)
    _ensure_player(device_key, device)
    try:
        resp = _get_client().audio.speech.create(
            model="tts-1", voice=voice, input=text, response_format="pcm"
        )
        audio = np.frombuffer(resp.content, dtype=np.int16).astype(np.float32) / 32768.0
        _play_queues[device_key].put((audio, device))
    except Exception as exc:
        print(f"[TTS error] {exc}")

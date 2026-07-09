from __future__ import annotations
import threading
import numpy as np
import sounddevice as sd
from typing import Callable, Optional
from config import (SAMPLE_RATE, VAD_FRAME_SAMPLES, SILENCE_FRAMES_TRIGGER,
                    SILENCE_THRESHOLD, MAX_CHUNK_SECONDS, MIN_CHUNK_SECONDS)


class VoiceCapture:
    """Captures audio with energy-based VAD; fires callback with speech chunks."""

    def __init__(self, callback: Callable[[np.ndarray], None], device: Optional[int] = None):
        self.callback = callback
        self.device = device
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="VoiceCapture")
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _loop(self):
        max_samples = int(SAMPLE_RATE * MAX_CHUNK_SECONDS)
        min_samples = int(SAMPLE_RATE * MIN_CHUNK_SECONDS)

        speech_buffer: list[float] = []
        silence_count = 0
        in_speech = False

        def _flush():
            nonlocal speech_buffer, silence_count, in_speech
            chunk = np.array(speech_buffer[:max_samples], dtype=np.float32)
            speech_buffer = []
            silence_count = 0
            in_speech = False
            if len(chunk) >= min_samples:
                self.callback(chunk)

        def audio_cb(indata, frames, time_info, status):
            nonlocal speech_buffer, silence_count, in_speech
            frame = indata[:, 0]
            rms = float(np.sqrt(np.mean(frame ** 2)))
            is_speech = rms > SILENCE_THRESHOLD

            if is_speech:
                in_speech = True
                silence_count = 0
                speech_buffer.extend(frame.tolist())
            elif in_speech:
                speech_buffer.extend(frame.tolist())
                silence_count += 1
                if silence_count >= SILENCE_FRAMES_TRIGGER or len(speech_buffer) >= max_samples:
                    _flush()

        try:
            with sd.InputStream(
                device=self.device,
                samplerate=SAMPLE_RATE,
                channels=1,
                blocksize=VAD_FRAME_SAMPLES,
                dtype="float32",
                callback=audio_cb,
            ):
                while self.running:
                    sd.sleep(200)
        except Exception as exc:
            print(f"[Capture error] {exc}")

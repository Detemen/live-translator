#!/usr/bin/env python3
from __future__ import annotations
"""
Live Translator — real-time bidirectional translation for meetings.

Requires:
  - OPENAI_API_KEY environment variable
  - BlackHole-2ch for system audio capture  (brew install blackhole-2ch)
  - sounddevice, numpy, openai  (pip install -r requirements.txt)
"""

import os
import sys
import threading
import numpy as np
import sounddevice as sd
import tkinter as tk
from tkinter import ttk, messagebox

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: set OPENAI_API_KEY environment variable first")
    sys.exit(1)

from config import LANG_NAMES, TTS_VOICE_INCOMING, TTS_VOICE_OUTGOING
from capture import VoiceCapture
from pipeline import transcribe, translate, speak
from gui import FloatingWindow


# ── Device selection dialog ──────────────────────────────────────────────────

class SetupDialog:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Translator — Setup")
        self.root.geometry("520x340")
        self.root.resizable(False, False)

        self.system_device: int | None = None
        self.mic_device: int | None = None
        self.output_device: int | None = None
        self.vmic_device: int | None = None
        self.target_lang = "en"
        self.confirmed = False

        self._build()

    def _build(self):
        devices = sd.query_devices()
        inputs  = [(i, d["name"]) for i, d in enumerate(devices) if d["max_input_channels"] > 0]
        outputs = [(i, d["name"]) for i, d in enumerate(devices) if d["max_output_channels"] > 0]
        in_opts  = [f"{i}: {n}" for i, n in inputs]
        out_opts = [f"{i}: {n}" for i, n in outputs]
        lang_opts = [f"{k} — {v}" for k, v in LANG_NAMES.items() if k != "uk"]

        tk.Label(self.root, text="Live Translator", font=("Helvetica Neue", 15, "bold")).pack(pady=10)

        frm = tk.Frame(self.root, padx=20)
        frm.pack(fill="x")

        self._vars: dict[str, tk.StringVar] = {}

        def row(label: str, key: str, options: list[str], default_hint: str = ""):
            f = tk.Frame(frm)
            f.pack(fill="x", pady=3)
            tk.Label(f, text=label, width=26, anchor="w").pack(side="left")
            v = tk.StringVar()
            cb = ttk.Combobox(f, textvariable=v, values=options, state="readonly", width=30)
            cb.pack(side="left")
            self._vars[key] = v
            # auto-select by hint
            if default_hint:
                match = next((o for o in options if default_hint.lower() in o.lower()), None)
                if match:
                    v.set(match)
            return v

        row("System audio (BlackHole ↓):", "sys",  in_opts,  "blackhole")
        row("Microphone (твій голос):",    "mic",  in_opts,  "")
        row("Навушники / динаміки:",        "out",  out_opts, "")
        row("Virtual mic (BlackHole ↑):",  "vmic", out_opts, "blackhole")
        row("Мова співрозмовника:",         "lang", lang_opts,"en —")

        note = ("Virtual mic → встанови BlackHole як мікрофон у Zoom/Meet,\n"
                "щоб співрозмовник чув твій голос у перекладі.")
        tk.Label(self.root, text=note, fg="#666", font=("Helvetica Neue", 9),
                 justify="left").pack(padx=20, pady=4, anchor="w")

        tk.Button(self.root, text="▶  Start", command=self._confirm,
                  font=("Helvetica Neue", 13, "bold"),
                  bg="#238636", fg="white", relief="flat",
                  padx=20, pady=6).pack(pady=8)

    def _parse(self, key: str) -> int | None:
        val = self._vars[key].get()
        if not val:
            return None
        try:
            return int(val.split(":")[0])
        except ValueError:
            return None

    def _confirm(self):
        self.system_device = self._parse("sys")
        self.mic_device    = self._parse("mic")
        self.output_device = self._parse("out")
        self.vmic_device   = self._parse("vmic")
        raw_lang = self._vars["lang"].get()
        self.target_lang   = raw_lang.split(" ")[0] if raw_lang else "en"
        self.confirmed = True
        self.root.destroy()

    def run(self) -> bool:
        self.root.mainloop()
        return self.confirmed


# ── Main translation loop ────────────────────────────────────────────────────

def run(setup: SetupDialog):
    gui = FloatingWindow()

    def handle_incoming(audio: np.ndarray):
        """System audio (other person) → Ukrainian TTS in headphones."""
        gui.set_status("⏳ Розпізнаю…")
        text, lang = transcribe(audio)
        if not text:
            gui.set_status("● Ready")
            return
        print(f"[IN]  [{lang}] {text}")

        gui.set_status("⏳ Перекладаю…")
        translation = translate(text, "uk")
        print(f"[→UA] {translation}")

        label = f"[{lang.upper()}] {text}"
        gui.update_incoming(label, translation)
        gui.set_status("🔊 Говорю…")
        speak(translation, voice=TTS_VOICE_INCOMING, device=setup.output_device)
        gui.set_status("● Ready")

    def handle_outgoing(audio: np.ndarray):
        """Microphone (user Ukrainian) → target language TTS on virtual mic."""
        gui.set_status("⏳ Розпізнаю тебе…")
        text, _ = transcribe(audio, language="uk")
        if not text:
            gui.set_status("● Ready")
            return
        print(f"[OUT] [uk] {text}")

        gui.set_status(f"⏳ Перекладаю → {setup.target_lang}…")
        translation = translate(text, setup.target_lang)
        print(f"[→{setup.target_lang.upper()}] {translation}")

        gui.update_outgoing(text, translation)
        if setup.vmic_device is not None:
            gui.set_status("🔊 Передаю…")
            speak(translation, voice=TTS_VOICE_OUTGOING, device=setup.vmic_device)
        gui.set_status("● Ready")

    def spawn(fn, audio):
        threading.Thread(target=fn, args=(audio,), daemon=True).start()

    sys_cap = VoiceCapture(lambda a: spawn(handle_incoming, a), device=setup.system_device)
    mic_cap = VoiceCapture(lambda a: spawn(handle_outgoing, a), device=setup.mic_device)

    sys_cap.start()
    mic_cap.start()
    print("[Translator] Running — close window to stop.")

    gui.run()

    sys_cap.stop()
    mic_cap.stop()


if __name__ == "__main__":
    setup = SetupDialog()
    if setup.run():
        run(setup)

# live-translator

Real-time bidirectional audio translation for meetings — captures system audio (via BlackHole on macOS), transcribes and translates on the fly, and shows both languages in a small desktop GUI.

## How it works

- `capture.py` — system audio capture (BlackHole virtual audio device)
- `pipeline.py` — streaming transcription + translation (OpenAI)
- `gui.py` — Tkinter window showing live original/translated text
- `main.py` — entrypoint wiring capture → pipeline → GUI

See `SETUP.md` for the macOS audio-routing setup (BlackHole + Audio MIDI Setup).

## Stack

Python, `sounddevice`, OpenAI API, Tkinter.

## Running

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python main.py
```

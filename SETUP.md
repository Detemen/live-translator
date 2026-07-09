# Live Translator — Налаштування на Mac

## 1. Залежності

```bash
# Python 3.10+
pip install -r requirements.txt

# BlackHole — безкоштовний віртуальний аудіо-драйвер
brew install blackhole-2ch
```

## 2. Налаштування Audio MIDI Setup

Відкрий **Audio MIDI Setup** (Spotlight → "Audio MIDI Setup"):

### Для перехоплення голосу співрозмовника:
1. Натисни `+` → **Create Multi-Output Device**
2. Постав галочки на: `BlackHole 2ch` + твої навушники/динаміки
3. Назви його "Translator Output"
4. У **System Preferences → Sound → Output** вибери "Translator Output"

> Тепер Zoom виводить звук і на навушники (ти чуєш), і в BlackHole (наш застосунок перехоплює).

### Для відправки перекладеного голосу:
У **Zoom / Google Meet / Teams**:
- Мікрофон → вибери **BlackHole 2ch**

> Наш застосунок буде виводити перекладений голос у BlackHole, і Zoom передасть його співрозмоннику.

## 3. Запуск

```bash
export OPENAI_API_KEY="sk-..."
python main.py
```

У вікні налаштувань вибери:
- **System audio (BlackHole ↓)** → `BlackHole 2ch` (вхідний)
- **Мікрофон** → свій мікрофон
- **Навушники** → свої навушники
- **Virtual mic (BlackHole ↑)** → `BlackHole 2ch` (вихідний)
- **Мова співрозмовника** → наприклад `en — English`

## 4. Вартість API

| Операція | Ціна | ~1 год розмови |
|----------|------|----------------|
| Whisper STT | $0.006/хв | $0.36 |
| GPT-4o-mini | ~$0.01/хв | $0.60 |
| TTS tts-1 | $15/1M chars | ~$0.40 |
| **Разом** | | **~$1.40/год** |

З $9 на балансі → ~6-7 годин реальних розмов.

## 5. Як це працює

```
Zoom/Meet → системний аудіо → BlackHole (вхід)
  → VoiceCapture (VAD) → Whisper API → GPT-4o-mini → TTS nova
  → навушники  +  плаваюче вікно з субтитрами

Твій мікрофон → VoiceCapture (VAD) → Whisper API (uk)
  → GPT-4o-mini → TTS onyx → BlackHole (вихід)
  → Zoom/Meet передає співрозмоннику
```

## Troubleshooting

**Не чую перекладу:** Перевір що "Translator Output" вибраний як системний вивід звуку.

**Співрозмовник не чує перекладу:** Перевір що в Zoom/Meet мікрофон = BlackHole 2ch.

**Затримка велика:** Нормальна затримка 2-4 секунди (Whisper + GPT + TTS). Це не баг.

**Тиша не розпізнається як кінець фрази:** Відрегулюй `SILENCE_THRESHOLD` у `config.py` (за замовчуванням 0.008).

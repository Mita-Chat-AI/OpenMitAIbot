from io import BytesIO
import numpy as np
from pedalboard import Pedalboard, Reverb
from pedalboard.io import AudioFile

def apply_effects(audio_bytes: bytes) -> bytes:
    # BytesIO для чтения WAV
    audio_file = BytesIO(audio_bytes)
    
    # Читаем WAV в NumPy массив
    with AudioFile(audio_file, 'r') as f:
        audio = f.read(f.frames)          # shape=(samples, channels)
        samplerate = f.samplerate

    # Добавляем тихий белый шум
    noise = np.random.normal(0, 0.0001, audio.shape).astype(np.float32)
    audio_noisy = audio + noise

    # Применяем эффекты
    board = Pedalboard([
        Reverb(room_size=0.01, damping=0.8, wet_level=0.1)
    ])
    processed = board(audio_noisy, samplerate)  # samplerate позиционно

    # Сохраняем обратно в WAV байты
    output_buffer = BytesIO()
    with AudioFile(output_buffer, 'w', samplerate, processed.shape[0], format='wav') as f:
        f.write(processed)
    output_buffer.seek(0)
    return output_buffer.read()

# Использование
with open("test.wav", "rb") as f:
    audio_bytes = f.read()

result_bytes = apply_effects(audio_bytes)

with open("live.wav", "wb") as f:
    f.write(result_bytes)

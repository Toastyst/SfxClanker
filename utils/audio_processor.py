import os
from pydub import AudioSegment
import pygame

def process_audio(input_path: str, output_path: str, normalize_flag: bool, trim: bool) -> bool | str:
    try:
        # Load MP3 using pydub with ffmpeg backend
        audio = AudioSegment.from_file(input_path, format="mp3")
        # Set to 44.1kHz mono
        audio = audio.set_frame_rate(44100).set_channels(1)
        # Normalize to -3 dB peak
        if normalize_flag:
            peak_dBFS = audio.max_dBFS
            gain = -3 - peak_dBFS
            audio = audio.apply_gain(gain)
        # Trim silence if enabled
        if trim:
            audio = audio.silenceremove(silence_len=1000, silence_thresh=-50, padding=500)
        # Export to WAV
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        return str(e)

def preview_audio(path: str) -> None:
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Preview failed: {e}")

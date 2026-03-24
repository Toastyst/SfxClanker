import os
import math
from pydub import AudioSegment
import pygame
from typing import Optional

def process_audio(input_path: str, output_path: str, normalize_flag: bool, trim: bool,
                  vol_gain: float = 1.0, max_len: Optional[float] = None,
                  rms_target: float = -14.0, strict_length: bool = False, vol_factor: Optional[float] = None) -> bool | str:
    try:
        # Load MP3 using pydub with ffmpeg backend
        audio = AudioSegment.from_file(input_path, format="mp3")
        # Set to 44.1kHz mono
        audio = audio.set_frame_rate(44100).set_channels(1)
        # Trim silence if enabled
        if trim:
            audio = audio.silenceremove(silence_len=1000, silence_thresh=-50, padding=500)
        # Trim to length
        if max_len is not None:
            audio = trim_to_length(audio, max_len, strict_length)
        # Apply volume and loudness
        audio = apply_volume_loudness(audio, vol_gain, rms_target)
        # Apply per-sound volume factor
        if vol_factor is not None:
            audio = apply_per_sound_volume(audio, vol_factor)
        # Normalize to -3 dB peak
        if normalize_flag:
            peak_dBFS = audio.max_dBFS
            gain = -3 - peak_dBFS
            audio = audio.apply_gain(gain)
        # Export to WAV
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        return str(e)

def preview_audio(path: str, vol_factor: float = 1.0, blocking: bool = False) -> None:
    try:
        pygame.mixer.init()
        pygame.mixer.music.stop()  # Stop previous sound
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(vol_factor)
        pygame.mixer.music.play()
        if blocking:
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.remove(path)  # Remove after play
    except Exception as e:
        print(f"Preview failed: {e}")
        if blocking:
            try:
                os.remove(path)
            except:
                pass

def apply_volume_loudness(audio: AudioSegment, global_vol: float, rms_target: float) -> AudioSegment:
    # RMS normalize: approximate LUFS with RMS dB
    rms_db = 20 * math.log10(audio.rms / 32768) if audio.rms > 0 else -60
    gain_db = rms_target - rms_db
    audio = audio.apply_gain(gain_db)
    # Global volume multiplier (linear 0-2.0 -> dB)
    vol_db = 20 * math.log10(global_vol) if global_vol > 0 else -60
    return audio.apply_gain(vol_db)

def trim_to_length(audio: AudioSegment, max_len: float, strict: bool) -> AudioSegment:
    if len(audio) / 1000.0 > max_len:
        trim_ms = int(max_len * 1000)
        audio = audio[:trim_ms]
        if strict:
            audio = audio.fade_out(200)  # 200ms fade
    return audio

def apply_per_sound_volume(audio: AudioSegment, vol_factor: float) -> AudioSegment:
    vol_db = 20 * math.log10(vol_factor) if vol_factor > 0 else -60
    return audio.apply_gain(vol_db)

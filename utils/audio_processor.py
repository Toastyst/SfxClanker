import os
import subprocess
import shutil
import winsound

def get_ffmpeg_path():
    path = shutil.which('ffmpeg')
    if path:
        return path
    hardcoded = 'ffmpeg\\ffmpeg-8.1-essentials_build\\bin\\ffmpeg.exe'
    if os.path.exists(hardcoded):
        return hardcoded
    return None

def process_audio(input_path: str, output_path: str, normalize_flag: bool, trim: bool) -> bool | str:
    try:
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            return "ffmpeg binary not found in PATH or bundle"
        cmd = [ffmpeg_path, '-y', '-i', input_path, '-ar', '44100', '-ac', '1']
        if trim and normalize_flag:
            cmd += ['-af', 'silenceremove=1:0:-50dB,loudnorm=I=-16:LRA=11:TP=-1.5']
        elif trim:
            cmd += ['-af', 'silenceremove=1:0:-50dB']
        elif normalize_flag:
            cmd += ['-af', 'loudnorm=I=-16:LRA=11:TP=-1.5']
        cmd.append(output_path)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            err = result.stderr.strip()
            if err:
                return f"ffmpeg error: {err}"
            else:
                return "ffmpeg failed with unknown error"
    except Exception as e:
        return str(e)

def preview_audio(path: str, volume: float = 0.5) -> None:
    # winsound can't control volume, so just play
    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)

import pytest
import sys
from utils.audio_processor import process_audio, preview_audio

def test_process_audio_normalize_trim(mocker):
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.returncode = 0
    mocker.patch('utils.audio_processor.get_ffmpeg_path', return_value='ffmpeg')

    result = process_audio('input.mp3', 'output.wav', True, True)
    assert result is True
    mock_run.assert_called_once()

def test_process_audio_no_normalize_no_trim(mocker):
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.returncode = 0
    mocker.patch('utils.audio_processor.get_ffmpeg_path', return_value='ffmpeg')

    result = process_audio('input.mp3', 'output.wav', False, False)
    assert result is True
    mock_run.assert_called_once()

def test_process_audio_ffmpeg_error(mocker):
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "ffmpeg error"
    mocker.patch('utils.audio_processor.get_ffmpeg_path', return_value='ffmpeg')

    result = process_audio('input.mp3', 'output.wav', True, True)
    assert "ffmpeg error" in result

def test_process_audio_no_ffmpeg(mocker):
    mocker.patch('utils.audio_processor.get_ffmpeg_path', return_value=None)

    result = process_audio('input.mp3', 'output.wav', True, True)
    assert "ffmpeg binary not found" in result

@pytest.mark.skipif(sys.platform != 'win32', reason="winsound Windows only")
def test_preview_audio(mocker):
    mock_play = mocker.patch('winsound.PlaySound')
    preview_audio('test.wav')
    mock_play.assert_called_with('test.wav', mocker.ANY)

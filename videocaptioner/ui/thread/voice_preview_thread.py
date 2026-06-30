"""配音声音预览后台线程"""

import subprocess
import tempfile
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

from videocaptioner.config import ASSETS_PATH, CACHE_PATH, RESOURCE_PATH
from videocaptioner.core.dubbing.config_builder import build_dubbing_config
from videocaptioner.core.dubbing.presets import get_dubbing_preset
from videocaptioner.core.speech.models import SpeechProviderConfig, SynthesisRequest
from videocaptioner.core.speech.providers import create_speech_synthesizer
from videocaptioner.core.utils.logger import setup_logger
from videocaptioner.ui.common.config import cfg

logger = setup_logger("voice_preview_thread")

SAMPLE_TEXT = "你好，欢迎使用 VideoCaptioner 字幕助手。这是一段配音声音预览。"


def bundled_voice_preview(preset_name: str) -> Path | None:
    """查找预先打包的配音声音预览文件"""
    search_dirs = [
        ASSETS_PATH / "voice-previews",
        RESOURCE_PATH / "assets" / "voice-previews",
        CACHE_PATH / "voice-previews",
    ]
    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
        for ext in (".mp3", ".wav", ".flac"):
            candidate = base_dir / f"{preset_name}{ext}"
            if candidate.exists():
                return candidate
    return None


def playable_voice_preview(path: Path) -> Path:
    """规范化预览音频为可播放格式"""
    if path.suffix == ".wav":
        return path
    target = CACHE_PATH / "voice-previews" / f"{path.stem}.wav"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return target
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(path),
             "-ar", "24000", "-ac", "1", str(target)],
            capture_output=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return path
    return target


class VoicePreviewThread(QThread):
    """配音声音预览线程"""

    finished = pyqtSignal(str)  # 输出音频路径
    error = pyqtSignal(str)

    def __init__(self, preset_name: str, text: str = "",
                 clone_audio_path: str = "", clone_audio_text: str = ""):
        super().__init__()
        self.preset_name = preset_name
        self.text = text
        self.clone_audio_path = clone_audio_path
        self.clone_audio_text = clone_audio_text

    def run(self):
        try:
            # 如果有预置的预览音频文件，直接使用
            if not self.text and not self.clone_audio_path:
                bundled = bundled_voice_preview(self.preset_name)
                if bundled:
                    playable = playable_voice_preview(bundled)
                    self.finished.emit(str(playable))
                    return

            # 否则实时生成
            preview_text = self.text or SAMPLE_TEXT
            provider_key = cfg.dubbing_provider.value

            dubbing_config = build_dubbing_config(
                provider=provider_key,
                preset=self.preset_name,
                api_key=cfg.dubbing_api_key.value,
                api_base=cfg.dubbing_api_base.value,
                model=cfg.dubbing_model.value,
                voice=cfg.dubbing_voice.value,
                style_prompt=cfg.dubbing_style_prompt.value,
            )

            speech_config = SpeechProviderConfig(
                provider=dubbing_config.provider,
                api_key=dubbing_config.api_key,
                model=dubbing_config.model,
                base_url=dubbing_config.base_url,
                default_voice=dubbing_config.voice,
                style_prompt=dubbing_config.style_prompt,
            )
            synthesizer = create_speech_synthesizer(speech_config)

            output_dir = Path(tempfile.mkdtemp(prefix="vc-preview-"))
            output_path = output_dir / "preview.mp3"
            if dubbing_config.provider == "gemini":
                output_path = output_dir / "preview.wav"

            request = SynthesisRequest(
                text=preview_text,
                output_path=str(output_path),
                voice=dubbing_config.voice,
                style_prompt=dubbing_config.style_prompt,
                clone_audio_path=self.clone_audio_path or None,
                clone_audio_text=self.clone_audio_text or None,
            )

            result = synthesizer.synthesize(request)
            playable = playable_voice_preview(Path(result.output_path))
            self.finished.emit(str(playable))

        except Exception as e:
            logger.warning(f"语音预览生成失败: {e}")
            self.error.emit(str(e))

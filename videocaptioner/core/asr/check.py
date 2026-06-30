"""转录服务连通性检查：所有提供商统一入口。

用内置短音频跑一次真实转录（B 接口 / J 接口 / Whisper API / 百炼
Fun-ASR / whisper-cpp / faster-whisper 全部走生产路径），供设置页的
「测试转录」按钮与 CLI doctor 命令共用。

强制禁用缓存，确保坏掉的 Key/服务不会被缓存误报为成功。
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from videocaptioner.config import ASSETS_PATH
from videocaptioner.core.asr.transcribe import transcribe
from videocaptioner.core.entities import SubtitleLayoutEnum, TranscribeConfig
from videocaptioner.core.utils import cache as cache_utils
from videocaptioner.core.utils.video_utils import video2audio

TEST_AUDIO_PATH = ASSETS_PATH / "en.mp3"


@dataclass(frozen=True)
class TranscribeCheckResult:
    """转录检查结果

    Attributes:
        success: 转录是否成功
        detail: 成功时是识别出的文本，失败时是错误信息
    """

    success: bool
    detail: str


def check_transcribe(
    config: TranscribeConfig, audio_path: str | Path | None = None
) -> TranscribeCheckResult:
    """用短音频真实转录一次，验证当前转录服务可用。

    Args:
        config: 转录配置（指定模型、API Key、语言等）
        audio_path: 可选的测试音频路径，默认使用内置 en.mp3

    Returns:
        TranscribeCheckResult: 检查结果
    """
    path = Path(audio_path) if audio_path else TEST_AUDIO_PATH
    if not path.exists():
        return TranscribeCheckResult(False, f"测试音频不存在: {path}")

    work_dir = Path(tempfile.mkdtemp(prefix="videocaptioner-asr-check-"))
    try:
        # 与生产链路一致：先抽 16kHz 单声道 WAV 再转录
        wav_path = work_dir / "check.wav"
        if not video2audio(str(path), output=str(wav_path)):
            return TranscribeCheckResult(False, "ffmpeg 提取测试音频失败")

        # 禁用缓存以确保测到真实服务状态
        was_cached = cache_utils.is_cache_enabled()
        if was_cached:
            cache_utils.disable_cache()
        try:
            asr_data = transcribe(str(wav_path), config)
        except Exception as exc:  # noqa: BLE001
            # 各提供商抛错类型不一，统一收敛为结果
            return TranscribeCheckResult(False, str(exc) or type(exc).__name__)
        finally:
            if was_cached:
                cache_utils.enable_cache()

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    text = " ".join(
        asr_data.to_txt(layout=SubtitleLayoutEnum.ONLY_ORIGINAL).split()
    ).strip()
    if not text:
        return TranscribeCheckResult(False, "转录请求成功但结果为空")
    return TranscribeCheckResult(True, text)

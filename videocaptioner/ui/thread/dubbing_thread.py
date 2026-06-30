"""配音处理后台线程"""

import datetime
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

from videocaptioner.core.dubbing import (
    DubbingPipeline,
    SpeakerProfile,
    build_dubbing_config,
)
from videocaptioner.core.entities import SynthesisTask
from videocaptioner.core.utils.logger import setup_logger

logger = setup_logger("dubbing_thread")


class DubbingThread(QThread):
    """配音处理线程，异步执行配音流水线"""

    finished = pyqtSignal(SynthesisTask)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)

    def __init__(self, task: SynthesisTask):
        super().__init__()
        self.task = task
        self._cancel_requested = False

    def run(self):
        try:
            self.task.started_at = datetime.datetime.now()
            config = self.task.synthesis_config

            subtitle_path = self.task.subtitle_path
            video_path = self.task.video_path
            if not subtitle_path:
                raise ValueError("字幕路径为空")
            if not video_path:
                raise ValueError("视频路径为空")

            output_audio = Path(self.task.output_path) if self.task.output_path else None
            if not output_audio:
                raise ValueError("输出路径为空")

            # 构建配音配置
            self.progress.emit(5, "准备配音配置")
            dubbing_config = build_dubbing_config(
                provider=config.dubbing_provider or "edge",
                preset=config.dubbing_preset or "",
                api_key=config.dubbing_api_key or "",
                api_base=config.dubbing_api_base or "",
                model=config.dubbing_model or "",
                voice=config.dubbing_voice or "",
                style_prompt=config.dubbing_style_prompt or "",
                tts_workers=config.dubbing_tts_workers or 5,
                use_cache=config.dubbing_use_cache if hasattr(config, 'dubbing_use_cache') else True,
                timing=config.dubbing_timing if hasattr(config, 'dubbing_timing') else "balanced",
                audio_mode=config.dubbing_audio_mode if hasattr(config, 'dubbing_audio_mode') else "replace",
            )

            # 执行配音
            self.progress.emit(10, "开始配音")
            pipeline = DubbingPipeline(dubbing_config)

            def progress_callback(value, message):
                if self._cancel_requested:
                    raise InterruptedError("配音已取消")
                self.progress.emit(value, message)

            result = pipeline.run(
                subtitle_path=str(subtitle_path),
                video_path=str(video_path),
                output_audio_path=str(output_audio),
                callback=progress_callback,
            )

            self.task.completed_at = datetime.datetime.now()
            self.progress.emit(100, "配音完成")
            self.finished.emit(self.task)

        except InterruptedError:
            logger.info("配音已取消")
            self.progress.emit(0, "已取消")
        except Exception as e:
            logger.exception("配音处理失败")
            self.error.emit(str(e))

    def request_cancel(self):
        """请求取消配音"""
        self._cancel_requested = True

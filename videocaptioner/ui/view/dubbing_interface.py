# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    Action,
    BodyLabel,
    CardWidget,
    CommandBar,
    ComboBox,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    RoundMenu,
    SettingCardGroup,
    SwitchButton,
    ToolTipFilter,
    ToolTipPosition,
    TransparentDropDownPushButton,
)
from qfluentwidgets import FluentIcon as FIF

from videocaptioner.core.constant import (
    INFOBAR_DURATION_ERROR,
    INFOBAR_DURATION_SUCCESS,
    INFOBAR_DURATION_WARNING,
)
from videocaptioner.core.entities import (
    SupportedAudioFormats,
    SupportedSubtitleFormats,
    SupportedVideoFormats,
    SynthesisConfig,
    SynthesisTask,
)
from videocaptioner.core.utils.platform_utils import open_folder
from videocaptioner.ui.common.config import cfg
from videocaptioner.ui.common.dubbing_options import (
    DUBBING_PROVIDERS,
    get_provider_option,
    get_provider_voices,
)
from videocaptioner.ui.thread.dubbing_thread import DubbingThread
from videocaptioner.ui.thread.voice_preview_thread import VoicePreviewThread


class DubbingInterface(QWidget):
    """配音界面"""

    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DubbingInterface")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)

        self.task: Optional[SynthesisTask] = None
        self.dubbing_thread: Optional[DubbingThread] = None
        self.preview_thread: Optional[VoicePreviewThread] = None
        self.player = QMediaPlayer(self)

        self.setup_ui()
        self.set_value()
        self.setup_signals()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)

        # 顶部：命令栏 + 开始配音按钮
        top_layout = QHBoxLayout()
        self.command_bar = CommandBar(self)
        self.command_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._setup_command_bar()
        top_layout.addWidget(self.command_bar, 1)

        self.dub_button = PrimaryPushButton(self.tr("开始配音"), self, icon=FIF.PLAY)
        self.dub_button.setFixedHeight(34)
        top_layout.addWidget(self.dub_button)
        self.main_layout.addLayout(top_layout)

        # 配置卡片
        self.config_card = CardWidget(self)
        self.config_layout = QVBoxLayout(self.config_card)
        self.config_layout.setContentsMargins(20, 20, 20, 20)
        self.config_layout.setSpacing(15)

        # ── 提供商选择 ──
        provider_layout = QHBoxLayout()
        provider_layout.setSpacing(15)
        provider_layout.addWidget(BodyLabel(self.tr("配音服务"), self))
        self.provider_combo = ComboBox(self)
        self.provider_combo.setMinimumWidth(200)
        for p in DUBBING_PROVIDERS:
            self.provider_combo.addItem(p.title, userData=p.key)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch(1)
        self.config_layout.addLayout(provider_layout)

        # ── 声音选择 ──
        voice_layout = QHBoxLayout()
        voice_layout.setSpacing(15)
        voice_layout.addWidget(BodyLabel(self.tr("配音声音"), self))
        self.voice_combo = ComboBox(self)
        self.voice_combo.setMinimumWidth(250)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch(1)
        self.config_layout.addLayout(voice_layout)

        # ── 预览文本 ──
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(15)
        preview_layout.addWidget(BodyLabel(self.tr("试听文本"), self))
        self.preview_input = LineEdit(self)
        self.preview_input.setPlaceholderText(self.tr("输入试听文本，留空则使用默认文本"))
        self.preview_button = PushButton(self.tr("试听"), self, icon=FIF.MUSIC)
        preview_layout.addWidget(self.preview_input, 1)
        preview_layout.addWidget(self.preview_button)
        self.config_layout.addLayout(preview_layout)

        # ── API 配置（根据提供商动态显示） ──
        self.api_key_layout = QHBoxLayout()
        self.api_key_layout.setSpacing(15)
        self.api_key_label = BodyLabel(self.tr("API Key"), self)
        self.api_key_input = LineEdit(self)
        self.api_key_input.setPlaceholderText(self.tr("输入 API Key"))
        self.api_key_input.setEchoMode(LineEdit.Password)
        self.api_key_layout.addWidget(self.api_key_label)
        self.api_key_layout.addWidget(self.api_key_input, 1)
        self.config_layout.addLayout(self.api_key_layout)

        self.api_base_layout = QHBoxLayout()
        self.api_base_layout.setSpacing(15)
        self.api_base_label = BodyLabel(self.tr("API Base URL"), self)
        self.api_base_input = LineEdit(self)
        self.api_base_input.setPlaceholderText(self.tr("输入 API Base URL"))
        self.api_base_layout.addWidget(self.api_base_label)
        self.api_base_layout.addWidget(self.api_base_input, 1)
        self.config_layout.addLayout(self.api_base_layout)

        self.clone_layout = QHBoxLayout()
        self.clone_layout.setSpacing(15)
        self.clone_label = BodyLabel(self.tr("克隆音频"), self)
        self.clone_input = LineEdit(self)
        self.clone_input.setPlaceholderText(self.tr("选择参考音频文件（用于声音克隆）"))
        self.clone_button = PushButton(self.tr("浏览"))
        self.clone_play_button = PushButton(self.tr("试听"), icon=FIF.MUSIC)
        self.clone_clear_button = PushButton(self.tr("清除"), icon=FIF.DELETE)
        self.clone_layout.addWidget(self.clone_label)
        self.clone_layout.addWidget(self.clone_input, 1)
        self.clone_layout.addWidget(self.clone_button)
        self.clone_layout.addWidget(self.clone_play_button)
        self.clone_layout.addWidget(self.clone_clear_button)
        self.config_layout.addLayout(self.clone_layout)

        self.clone_text_layout = QHBoxLayout()
        self.clone_text_layout.setSpacing(15)
        self.clone_text_label = BodyLabel(self.tr("克隆文本"), self)
        self.clone_text_input = LineEdit(self)
        self.clone_text_input.setPlaceholderText(self.tr("输入克隆参考音频对应的文本（可选，可提高克隆质量）"))
        self.clone_text_layout.addWidget(self.clone_text_label)
        self.clone_text_layout.addWidget(self.clone_text_input, 1)
        self.config_layout.addLayout(self.clone_text_layout)

        # ── 配音高级设置 ──
        self.timing_layout = QHBoxLayout()
        self.timing_layout.setSpacing(15)
        self.timing_label = BodyLabel(self.tr("时间对齐"), self)
        self.timing_combo = ComboBox(self)
        self.timing_combo.setMinimumWidth(180)
        self.timing_combo.addItem(self.tr("平衡模式"), userData="balanced")
        self.timing_combo.addItem(self.tr("自然模式"), userData="natural")
        self.timing_combo.addItem(self.tr("严格模式"), userData="strict")
        self.timing_combo.addItem(self.tr("不对齐"), userData="none")
        self.timing_combo.setToolTip(self.tr("配音与原始音频的时间对齐方式"))
        self.timing_layout.addWidget(self.timing_label)
        self.timing_layout.addWidget(self.timing_combo)
        self.timing_layout.addStretch(1)
        self.config_layout.addLayout(self.timing_layout)

        self.audio_mode_layout = QHBoxLayout()
        self.audio_mode_layout.setSpacing(15)
        self.audio_mode_label = BodyLabel(self.tr("原声处理"), self)
        self.audio_mode_combo = ComboBox(self)
        self.audio_mode_combo.setMinimumWidth(180)
        self.audio_mode_combo.addItem(self.tr("替换原声"), userData="replace")
        self.audio_mode_combo.addItem(self.tr("混合原声"), userData="mix")
        self.audio_mode_combo.addItem(self.tr("压低原声"), userData="duck")
        self.audio_mode_combo.setToolTip(self.tr("配音音频与原声的混合方式"))
        self.audio_mode_layout.addWidget(self.audio_mode_label)
        self.audio_mode_layout.addWidget(self.audio_mode_combo)
        self.audio_mode_layout.addStretch(1)
        self.config_layout.addLayout(self.audio_mode_layout)

        self.text_track_layout = QHBoxLayout()
        self.text_track_layout.setSpacing(15)
        self.text_track_label = BodyLabel(self.tr("配音文本"), self)
        self.text_track_combo = ComboBox(self)
        self.text_track_combo.setMinimumWidth(180)
        self.text_track_combo.addItem(self.tr("自动选择"), userData="auto")
        self.text_track_combo.addItem(self.tr("第一行"), userData="first")
        self.text_track_combo.addItem(self.tr("第二行"), userData="second")
        self.text_track_combo.setToolTip(self.tr("用于配音的字幕文本来源"))
        self.text_track_layout.addWidget(self.text_track_label)
        self.text_track_layout.addWidget(self.text_track_combo)
        self.text_track_layout.addStretch(1)
        self.config_layout.addLayout(self.text_track_layout)

        self.main_layout.addWidget(self.config_card)

        # ── 字幕/视频文件选择 ──
        self.file_card = CardWidget(self)
        self.file_layout = QVBoxLayout(self.file_card)
        self.file_layout.setContentsMargins(20, 20, 20, 20)
        self.file_layout.setSpacing(15)

        subtitle_layout = QHBoxLayout()
        subtitle_layout.setSpacing(15)
        self.subtitle_label = BodyLabel(self.tr("字幕文件"), self)
        self.subtitle_input = LineEdit(self)
        self.subtitle_input.setPlaceholderText(self.tr("选择或拖入字幕文件"))
        self.subtitle_input.setAcceptDrops(True)
        self.subtitle_button = PushButton(self.tr("浏览"))
        subtitle_layout.addWidget(self.subtitle_label)
        subtitle_layout.addWidget(self.subtitle_input, 1)
        subtitle_layout.addWidget(self.subtitle_button)
        self.file_layout.addLayout(subtitle_layout)

        video_layout = QHBoxLayout()
        video_layout.setSpacing(15)
        self.video_label = BodyLabel(self.tr("视频文件"), self)
        self.video_input = LineEdit(self)
        self.video_input.setPlaceholderText(self.tr("选择或拖入视频文件（可选）"))
        self.video_input.setAcceptDrops(True)
        self.video_button = PushButton(self.tr("浏览"))
        video_layout.addWidget(self.video_label)
        video_layout.addWidget(self.video_input, 1)
        video_layout.addWidget(self.video_button)
        self.file_layout.addLayout(video_layout)

        self.main_layout.addWidget(self.file_card)

        self.main_layout.addStretch(1)

        # 底部进度条
        self.bottom_layout = QHBoxLayout()
        self.progress_bar = ProgressBar(self)
        self.status_label = BodyLabel(self.tr("就绪"), self)
        self.status_label.setMinimumWidth(100)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.bottom_layout.addWidget(self.progress_bar, 1)
        self.bottom_layout.addWidget(self.status_label)
        self.main_layout.addLayout(self.bottom_layout)

    def _setup_command_bar(self):
        """设置命令栏"""
        # 缓存开关
        self.cache_action = Action(
            FIF.HISTORY,
            self.tr("启用缓存"),
            checkable=True,
            checked=cfg.dubbing_use_cache.value,
        )
        self.cache_action.setToolTip(self.tr("相同配音文本使用缓存结果"))
        self.command_bar.addAction(self.cache_action)

        self.command_bar.addSeparator()

        # 打开文件夹按钮
        folder_action = Action(FIF.FOLDER, "", triggered=self.open_output_folder)
        folder_action.setToolTip(self.tr("打开输出文件夹"))
        self.command_bar.addAction(folder_action)

    def setup_signals(self):
        """设置信号连接"""
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self.timing_combo.currentIndexChanged.connect(self._on_timing_changed)
        self.audio_mode_combo.currentIndexChanged.connect(self._on_audio_mode_changed)
        self.text_track_combo.currentIndexChanged.connect(self._on_text_track_changed)
        self.dub_button.clicked.connect(self.start_dubbing)
        self.preview_button.clicked.connect(self.preview_voice)
        self.subtitle_button.clicked.connect(self.choose_subtitle_file)
        self.video_button.clicked.connect(self.choose_video_file)
        self.clone_button.clicked.connect(self.choose_clone_audio)
        self.clone_play_button.clicked.connect(self.play_clone_audio)
        self.clone_clear_button.clicked.connect(self.clear_clone_audio)
        self.player.stateChanged.connect(self._on_player_state_changed)
        self.player.error.connect(self._on_player_error)

    def set_value(self):
        """设置初始值"""
        # 设置当前提供商
        provider = cfg.dubbing_provider.value
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == provider:
                self.provider_combo.setCurrentIndex(i)
                break
        else:
            self.provider_combo.setCurrentIndex(0)

        # 设置 API 配置
        self.api_key_input.setText(cfg.dubbing_api_key.value)
        self.api_base_input.setText(cfg.dubbing_api_base.value)
        self.clone_input.setText(cfg.dubbing_clone_audio.value)
        self.clone_text_input.setText(cfg.dubbing_clone_text.value)
        self._set_combo_by_data(self.timing_combo, cfg.dubbing_timing.value)
        self._set_combo_by_data(self.audio_mode_combo, cfg.dubbing_audio_mode.value)
        self._set_combo_by_data(self.text_track_combo, cfg.dubbing_text_track.value)
        self.cache_action.setChecked(cfg.dubbing_use_cache.value)

        # 刷新声音列表
        self._refresh_voices()
        self._update_provider_visibility()

    def _on_provider_changed(self, index: int):
        """提供商切换"""
        provider_key = self.provider_combo.itemData(index)
        cfg.set(cfg.dubbing_provider, provider_key)

        provider = get_provider_option(provider_key)
        self.api_base_input.setText(provider.default_base)

        # 重置声音列表
        self._refresh_voices()
        self._update_provider_visibility()

    def _refresh_voices(self):
        """刷新声音列表"""
        provider_key = self.provider_combo.itemData(self.provider_combo.currentIndex())
        self.voice_combo.clear()
        voices = get_provider_voices(provider_key)
        for v in voices:
            self.voice_combo.addItem(f"{v.title} - {v.description}", userData=v.preset)

        # 尝试恢复上次选择的声音
        saved_preset = cfg.dubbing_preset.value
        for i in range(self.voice_combo.count()):
            if self.voice_combo.itemData(i) == saved_preset:
                self.voice_combo.setCurrentIndex(i)
                break

    def _set_combo_by_data(self, combo: ComboBox, data: str):
        """根据 userData 设置 ComboBox 当前选项"""
        for i in range(combo.count()):
            if combo.itemData(i) == data:
                combo.setCurrentIndex(i)
                break

    def _on_timing_changed(self, index: int):
        cfg.set(cfg.dubbing_timing, self.timing_combo.itemData(index))

    def _on_audio_mode_changed(self, index: int):
        cfg.set(cfg.dubbing_audio_mode, self.audio_mode_combo.itemData(index))

    def _on_text_track_changed(self, index: int):
        cfg.set(cfg.dubbing_text_track, self.text_track_combo.itemData(index))

    def _update_provider_visibility(self):
        """根据提供商显示/隐藏配置项"""
        provider_key = self.provider_combo.itemData(self.provider_combo.currentIndex())
        provider = get_provider_option(provider_key)

        # API Key / Base URL
        needs_key = provider.needs_api_key
        self.api_key_label.setVisible(needs_key)
        self.api_key_input.setVisible(needs_key)
        self.api_base_label.setVisible(needs_key)
        self.api_base_input.setVisible(needs_key)

        # 克隆相关
        supports_clone = provider.supports_clone
        self.clone_label.setVisible(supports_clone)
        self.clone_input.setVisible(supports_clone)
        self.clone_button.setVisible(supports_clone)
        self.clone_play_button.setVisible(supports_clone)
        self.clone_clear_button.setVisible(supports_clone)
        self.clone_text_label.setVisible(supports_clone)
        self.clone_text_input.setVisible(supports_clone)

    def preview_voice(self):
        """试听配音声音"""
        if self.preview_thread and self.preview_thread.isRunning():
            return

        preset = self.voice_combo.itemData(self.voice_combo.currentIndex())
        if not preset:
            InfoBar.warning(
                self.tr("提示"),
                self.tr("请先选择一个配音声音"),
                duration=INFOBAR_DURATION_WARNING,
                parent=self,
            )
            return

        # 保存当前声音配置
        self._save_current_voice()

        text = self.preview_input.text().strip()
        self.preview_button.setEnabled(False)
        self.preview_button.setText(self.tr("正在试听..."))

        self.preview_thread = VoicePreviewThread(
            preset_name=preset,
            text=text,
            clone_audio_path=cfg.dubbing_clone_audio.value,
            clone_audio_text=cfg.dubbing_clone_text.value,
        )
        self.preview_thread.finished.connect(self._on_preview_finished)
        self.preview_thread.error.connect(self._on_preview_error)
        self.preview_thread.start()

    def _on_preview_finished(self, path: str):
        """试听完成"""
        self.preview_button.setEnabled(True)
        self.preview_button.setText(self.tr("试听"))

        if Path(path).exists():
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            self.player.play()
            self.status_label.setText(self.tr("正在播放试听..."))

    def _on_preview_error(self, message: str):
        """试听失败"""
        self.preview_button.setEnabled(True)
        self.preview_button.setText(self.tr("试听"))
        InfoBar.error(
            self.tr("试听失败"),
            message,
            duration=INFOBAR_DURATION_ERROR,
            parent=self,
        )

    def _on_player_state_changed(self, state):
        """播放器状态变更"""
        if state == QMediaPlayer.StoppedState:
            self.status_label.setText(self.tr("就绪"))

    def _on_player_error(self, error):
        """播放器错误"""
        self.status_label.setText(self.tr("播放错误"))

    def _save_current_voice(self):
        """保存当前声音配置到 cfg"""
        voice_data = self.voice_combo.itemData(self.voice_combo.currentIndex())
        if voice_data:
            cfg.set(cfg.dubbing_preset, voice_data)
        cfg.set(cfg.dubbing_api_key, self.api_key_input.text())
        cfg.set(cfg.dubbing_api_base, self.api_base_input.text())
        cfg.set(cfg.dubbing_clone_audio, self.clone_input.text())
        cfg.set(cfg.dubbing_clone_text, self.clone_text_input.text())
        cfg.set(cfg.dubbing_use_cache, self.cache_action.isChecked())

    def create_task(self) -> Optional[SynthesisTask]:
        """创建配音任务"""
        subtitle_file = self.subtitle_input.text()
        video_file = self.video_input.text()

        if not subtitle_file:
            InfoBar.error(
                self.tr("错误"),
                self.tr("请选择字幕文件"),
                duration=INFOBAR_DURATION_ERROR,
                position=InfoBarPosition.TOP,
                parent=self,
            )
            return None

        self._save_current_voice()

        # 构建输出路径
        output_dir = Path(subtitle_file).parent
        output_path = str(output_dir / f"{Path(subtitle_file).stem}_dubbed.mp4")

        # 从 cfg 读取当前配音配置
        provider_key = self.provider_combo.itemData(self.provider_combo.currentIndex())

        config = SynthesisConfig(
            need_video=True,
            soft_subtitle=False,
            dubbing_provider=provider_key,
            dubbing_preset=self.voice_combo.itemData(self.voice_combo.currentIndex()),
            dubbing_api_key=self.api_key_input.text(),
            dubbing_api_base=self.api_base_input.text(),
            dubbing_voice=cfg.dubbing_voice.value,
            dubbing_style_prompt=cfg.dubbing_style_prompt.value,
            dubbing_tts_workers=cfg.dubbing_tts_workers.value,
            dubbing_use_cache=self.cache_action.isChecked(),
        )

        task = SynthesisTask(
            video_path=video_file if video_file else None,
            subtitle_path=subtitle_file,
            output_path=output_path,
            synthesis_config=config,
        )
        return task

    def start_dubbing(self):
        """开始配音"""
        if self.dubbing_thread and self.dubbing_thread.isRunning():
            InfoBar.warning(
                self.tr("提示"),
                self.tr("正在进行配音，请等待完成"),
                duration=INFOBAR_DURATION_WARNING,
                parent=self,
            )
            return

        self.dub_button.setEnabled(False)
        self.progress_bar.resume()
        self.progress_bar.reset()
        self.status_label.setText(self.tr("准备中..."))

        self.task = self.create_task()
        if not self.task:
            self.dub_button.setEnabled(True)
            return

        self.dubbing_thread = DubbingThread(self.task)
        self.dubbing_thread.finished.connect(self._on_dubbing_finished)
        self.dubbing_thread.progress.connect(self._on_dubbing_progress)
        self.dubbing_thread.error.connect(self._on_dubbing_error)
        self.dubbing_thread.start()

    def _on_dubbing_progress(self, value: int, message: str):
        """配音进度更新"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def _on_dubbing_finished(self, task):
        """配音完成"""
        self.dub_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(self.tr("配音完成"))

        InfoBar.success(
            self.tr("完成"),
            self.tr("配音已生成"),
            duration=INFOBAR_DURATION_SUCCESS,
            position=InfoBarPosition.TOP,
            parent=self,
        )
        self.finished.emit()

    def _on_dubbing_error(self, error_msg: str):
        """配音失败"""
        self.dub_button.setEnabled(True)
        self.progress_bar.error()
        self.status_label.setText(self.tr("配音失败"))

        InfoBar.error(
            self.tr("错误"),
            error_msg,
            duration=INFOBAR_DURATION_ERROR,
            position=InfoBarPosition.TOP,
            parent=self,
        )

    def choose_subtitle_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("选择字幕文件"), "",
            self.tr("字幕文件 (*.srt *.ass *.vtt *.json)"),
        )
        if file_path:
            self.subtitle_input.setText(file_path)

    def choose_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("选择视频文件"), "",
            self.tr("视频文件 (*.mp4 *.mkv *.avi *.mov *.webm)"),
        )
        if file_path:
            self.video_input.setText(file_path)

    def choose_clone_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("选择克隆参考音频"), "",
            self.tr("音频文件 (*.mp3 *.wav *.flac *.m4a *.ogg)"),
        )
        if file_path:
            self.clone_input.setText(file_path)
            cfg.set(cfg.dubbing_clone_audio, file_path)

    def play_clone_audio(self):
        """播放克隆参考音频"""
        path = self.clone_input.text()
        if not path or not Path(path).exists():
            InfoBar.warning(
                self.tr("提示"),
                self.tr("请先选择克隆参考音频"),
                duration=INFOBAR_DURATION_WARNING,
                parent=self,
            )
            return
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.player.play()

    def clear_clone_audio(self):
        self.clone_input.clear()
        self.clone_text_input.clear()
        cfg.set(cfg.dubbing_clone_audio, "")
        cfg.set(cfg.dubbing_clone_text, "")

    def open_output_folder(self):
        if self.task and self.task.output_path:
            target_dir = str(Path(self.task.output_path).parent)
            open_folder(target_dir)

    def closeEvent(self, event):
        if self.player.state() != QMediaPlayer.StoppedState:
            self.player.stop()
        super().closeEvent(event)

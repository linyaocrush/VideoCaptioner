"""FunASR (阿里云百炼) 转录设置组件"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    ComboBoxSettingCard,
    SettingCardGroup,
    SingleDirectionScrollArea,
)
from qfluentwidgets import FluentIcon as FIF

from videocaptioner.core.entities import TranscribeLanguageEnum

from ..common.config import cfg
from .EditComboBoxSettingCard import EditComboBoxSettingCard
from .LineEditSettingCard import LineEditSettingCard


class FunASRSettingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # 创建单向滚动区域和容器
        self.scrollArea = SingleDirectionScrollArea(orient=Qt.Vertical, parent=self)  # type: ignore
        self.scrollArea.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )

        self.container = QWidget(self)
        self.container.setStyleSheet("QWidget{background: transparent}")
        self.containerLayout = QVBoxLayout(self.container)

        self.setting_group = SettingCardGroup(self.tr("阿里云百炼 FunASR 设置"), self)

        # API Key
        self.api_key_card = LineEditSettingCard(
            cfg.fun_asr_api_key,
            FIF.FINGERPRINT,
            self.tr("API Key"),
            self.tr("输入阿里云百炼 API Key（也支持 DASHSCOPE_API_KEY 环境变量）"),
            "sk-",
            self.setting_group,
        )

        # API Base URL
        self.base_url_card = LineEditSettingCard(
            cfg.fun_asr_api_base,
            FIF.LINK,
            self.tr("API Base URL"),
            self.tr("输入阿里云百炼 API Base URL"),
            "https://dashscope.aliyuncs.com",
            self.setting_group,
        )

        # Model
        self.model_card = EditComboBoxSettingCard(
            cfg.fun_asr_model,
            FIF.ROBOT,  # type: ignore
            self.tr("FunASR 模型"),
            self.tr("选择或输入 FunASR 模型名称"),
            ["fun-asr", "fun-asr-v2"],
            self.setting_group,
        )

        # Language
        self.language_card = ComboBoxSettingCard(
            cfg.transcribe_language,
            FIF.LANGUAGE,
            self.tr("源语言"),
            self.tr("音视频中说话的语言，留空则自动检测"),
            [lang.value for lang in TranscribeLanguageEnum],
            self.setting_group,
        )

        # 设置最小宽度
        self.api_key_card.lineEdit.setMinimumWidth(200)
        self.base_url_card.lineEdit.setMinimumWidth(200)
        self.model_card.comboBox.setMinimumWidth(200)
        self.language_card.comboBox.setMinimumWidth(200)

        # 添加所有卡片到组
        self.setting_group.addSettingCard(self.api_key_card)
        self.setting_group.addSettingCard(self.base_url_card)
        self.setting_group.addSettingCard(self.model_card)
        self.setting_group.addSettingCard(self.language_card)

        # 将设置组添加到容器布局
        self.containerLayout.addWidget(self.setting_group)
        self.containerLayout.addStretch(1)

        # 设置滚动区域
        self.scrollArea.setWidget(self.container)
        self.scrollArea.setWidgetResizable(True)

        # 将滚动区域添加到主布局
        self.main_layout.addWidget(self.scrollArea)

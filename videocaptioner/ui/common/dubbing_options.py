"""配音提供商/声音选项定义

供配音界面 UI 使用，定义可选的提供商和声音列表。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DubbingProviderOption:
    """配音提供商选项"""
    key: str
    title: str
    description: str
    needs_api_key: bool
    supports_clone: bool
    default_base: str
    models: tuple[str, ...]


@dataclass(frozen=True)
class DubbingVoiceOption:
    """配音声音选项"""
    preset: str
    title: str
    description: str
    tags: tuple[str, ...] = ()


DUBBING_PROVIDERS: tuple[DubbingProviderOption, ...] = (
    DubbingProviderOption(
        key="edge",
        title="Edge TTS",
        description="免费，无需 API Key，支持多种中文和英语声音",
        needs_api_key=False,
        supports_clone=False,
        default_base="",
        models=("edge-tts",),
    ),
    DubbingProviderOption(
        key="gemini",
        title="Gemini TTS",
        description="Google Gemini TTS，需要 API Key，仅英语",
        needs_api_key=True,
        supports_clone=False,
        default_base="https://generativelanguage.googleapis.com/v1beta",
        models=("gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"),
    ),
    DubbingProviderOption(
        key="siliconflow",
        title="SiliconFlow CosyVoice",
        description="硅基流动 CosyVoice TTS，需要 API Key，支持声音克隆",
        needs_api_key=True,
        supports_clone=True,
        default_base="https://api.siliconflow.cn/v1",
        models=("FunAudioLLM/CosyVoice2-0.5B",),
    ),
)


def get_provider_option(provider: str) -> DubbingProviderOption:
    for opt in DUBBING_PROVIDERS:
        if opt.key == provider:
            return opt
    return DUBBING_PROVIDERS[0]


def get_provider_voices(provider: str) -> tuple[DubbingVoiceOption, ...]:
    """获取指定提供商的声音列表"""
    from videocaptioner.core.dubbing.presets import PRESETS, EDGE_VOICE_ALIASES, SILICONFLOW_VOICE_ALIASES, GEMINI_VOICES

    if provider == "edge":
        # Female voice aliases (matched against the alias key, not the full voice ID)
        _edge_female_aliases = {
            "xiaoxiao", "xiaoyi", "xiaochen", "xiaohan", "xiaomeng",
            "xiaomo", "xiaoqiu", "xiaorui", "xiaoshuang",
            "xiaoyan", "xiaozhen", "jenny", "aria", "sara",
        }
        voices = []
        for alias, full_id in EDGE_VOICE_ALIASES.items():
            gender = "女声" if alias in _edge_female_aliases else "男声"
            lang = "中文" if "CN" in full_id else "英语" if "US" in full_id else "其他"
            lang_prefix = "cn" if "CN" in full_id else "en" if "US" in full_id else "xx"
            voices.append(DubbingVoiceOption(
                preset=f"edge-{lang_prefix}-{alias}",
                title=full_id,
                description=f"Edge TTS - {lang} {gender}",
                tags=(lang, gender, "免费"),
            ))
        return tuple(voices)

    elif provider == "siliconflow":
        voices = []
        for alias in SILICONFLOW_VOICE_ALIASES:
            gender = "女声" if alias in ("anna", "bella", "claire", "diana") else "男声"
            voices.append(DubbingVoiceOption(
                preset=f"siliconflow-cn-{alias}",
                title=alias.capitalize(),
                description=f"SiliconFlow CosyVoice - 中文 {gender}",
                tags=("中文", gender, "支持克隆"),
            ))
        return tuple(voices)

    elif provider == "gemini":
        voices = []
        for voice in sorted(GEMINI_VOICES):
            voices.append(DubbingVoiceOption(
                preset=f"gemini-en-{voice.lower()}",
                title=voice,
                description=f"Gemini TTS - 英语",
                tags=("英语", "需 API Key"),
            ))
        return tuple(voices)

    return ()

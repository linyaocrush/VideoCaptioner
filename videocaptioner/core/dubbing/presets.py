"""Dubbing provider/model/voice presets."""

from __future__ import annotations

from dataclasses import dataclass

SILICONFLOW_COSYVOICE2_MODEL = "FunAudioLLM/CosyVoice2-0.5B"

SILICONFLOW_VOICE_ALIASES = {
    "anna": f"{SILICONFLOW_COSYVOICE2_MODEL}:anna",
    "alex": f"{SILICONFLOW_COSYVOICE2_MODEL}:alex",
    "bella": f"{SILICONFLOW_COSYVOICE2_MODEL}:bella",
    "benjamin": f"{SILICONFLOW_COSYVOICE2_MODEL}:benjamin",
    "charles": f"{SILICONFLOW_COSYVOICE2_MODEL}:charles",
    "claire": f"{SILICONFLOW_COSYVOICE2_MODEL}:claire",
    "david": f"{SILICONFLOW_COSYVOICE2_MODEL}:david",
    "diana": f"{SILICONFLOW_COSYVOICE2_MODEL}:diana",
}

GEMINI_VOICES = {
    "Achernar", "Achird", "Aoede", "Autonoe", "Callirrhoe",
    "Charon", "Despina", "Enceladus", "Erinome", "Fenrir",
    "Gacrux", "Iapetus", "Kore", "Laomedeia", "Leda",
    "Orus", "Puck", "Pulcherrima", "Rasalgethi", "Sadachbia",
    "Sadaltager", "Schedar", "Sulafat", "Umbriel",
    "Vindemiatrix", "Zephyr", "Zubenelgenubi",
}

EDGE_VOICE_ALIASES = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi": "zh-CN-XiaoyiNeural",
    "yunjian": "zh-CN-YunjianNeural",
    "yunxi": "zh-CN-YunxiNeural",
    "yunyang": "zh-CN-YunyangNeural",
    "xiaochen": "zh-CN-XiaochenNeural",
    "xiaohan": "zh-CN-XiaohanNeural",
    "xiaomeng": "zh-CN-XiaomengNeural",
    "xiaomo": "zh-CN-XiaomoNeural",
    "xiaoqiu": "zh-CN-XiaoqiuNeural",
    "xiaorui": "zh-CN-XiaoruiNeural",
    "xiaoshuang": "zh-CN-XiaoshuangNeural",
    "xiaoyan": "zh-CN-XiaoyanNeural",
    "xiaozhen": "zh-CN-XiaozhenNeural",
    "yunfeng": "zh-CN-YunfengNeural",
    "yunhao": "zh-CN-YunhaoNeural",
    "yunxia": "zh-CN-YunxiaNeural",
    "yunya": "zh-CN-YunyaNeural",
    "jenny": "en-US-JennyNeural",
    "guy": "en-US-GuyNeural",
    "aria": "en-US-AriaNeural",
    "tony": "en-US-TonyNeural",
    "sara": "en-US-SaraNeural",
}


@dataclass(frozen=True)
class DubbingPreset:
    name: str
    provider: str
    api_base: str
    model: str
    voice: str
    style_prompt: str = ""


def _build_siliconflow_presets() -> dict[str, DubbingPreset]:
    base = "https://api.siliconflow.cn/v1"
    prompts = {
        "anna": "请用自然、清晰、适合视频配音的中文语气朗读。",
        "alex": "请用自然、清晰、适合视频配音的中文语气朗读。",
        "bella": "请用温柔、亲切、适合视频配音的中文语气朗读。",
        "benjamin": "请用沉稳、清晰、适合视频配音的中文语气朗读。",
        "charles": "请用沉稳、清晰、适合视频配音的中文语气朗读。",
        "claire": "请用温暖、自然、适合视频配音的中文语气朗读。",
        "david": "请用稳重、清晰、适合视频配音的中文语气朗读。",
        "diana": "请用优雅、自然、适合视频配音的中文语气朗读。",
    }
    presets = {}
    for alias, prompt in prompts.items():
        presets[f"siliconflow-cn-{alias}"] = DubbingPreset(
            name=f"siliconflow-cn-{alias}",
            provider="siliconflow",
            api_base=base,
            model=SILICONFLOW_COSYVOICE2_MODEL,
            voice=SILICONFLOW_VOICE_ALIASES[alias],
            style_prompt=prompt,
        )
    return presets


def _build_gemini_presets() -> dict[str, DubbingPreset]:
    base = "https://generativelanguage.googleapis.com/v1beta"
    model = "gemini-3.1-flash-tts-preview"
    style_map = {
        "neutral": "Read naturally and clearly for a video dubbing track.",
        "friendly": "Read in a friendly, natural, conversational voice for a video dubbing track.",
        "upbeat": "Read in an upbeat, clear, energetic voice for a video dubbing track.",
    }
    voice_by_style = {
        "neutral": ["Kore", "Enceladus", "Schedar", "Umbriel"],
        "friendly": ["Achird", "Charon", "Puck", "Laomedeia"],
        "upbeat": ["Puck", "Zephyr", "Aoede", "Fenrir"],
    }
    presets = {}
    for style, voices in voice_by_style.items():
        for voice in voices[:2]:
            name = f"gemini-en-{style}-{voice.lower()}"
            presets[name] = DubbingPreset(
                name=name, provider="gemini", api_base=base,
                model=model, voice=voice, style_prompt=style_map[style],
            )
    return presets


def _build_edge_presets() -> dict[str, DubbingPreset]:
    cn_female = ["xiaoxiao", "xiaoyi", "xiaochen", "xiaohan", "xiaomeng", "xiaomo",
                 "xiaoqiu", "xiaorui", "xiaoshuang", "xiaoyan", "xiaozhen"]
    cn_male = ["yunjian", "yunxi", "yunyang", "yunfeng", "yunhao", "yunxia", "yunya"]
    en_female = ["jenny", "aria", "sara"]
    en_male = ["guy", "tony"]

    presets = {}
    for alias in cn_female:
        presets[f"edge-cn-{alias}"] = DubbingPreset(
            name=f"edge-cn-{alias}", provider="edge",
            api_base="", model="edge-tts", voice=EDGE_VOICE_ALIASES[alias],
        )
    for alias in cn_male:
        presets[f"edge-cn-{alias}"] = DubbingPreset(
            name=f"edge-cn-{alias}", provider="edge",
            api_base="", model="edge-tts", voice=EDGE_VOICE_ALIASES[alias],
        )
    for alias in en_female:
        presets[f"edge-en-{alias}"] = DubbingPreset(
            name=f"edge-en-{alias}", provider="edge",
            api_base="", model="edge-tts", voice=EDGE_VOICE_ALIASES[alias],
        )
    for alias in en_male:
        presets[f"edge-en-{alias}"] = DubbingPreset(
            name=f"edge-en-{alias}", provider="edge",
            api_base="", model="edge-tts", voice=EDGE_VOICE_ALIASES[alias],
        )
    return presets


PRESETS: dict[str, DubbingPreset] = {}
PRESETS.update(_build_siliconflow_presets())
PRESETS.update(_build_gemini_presets())
PRESETS.update(_build_edge_presets())


def get_dubbing_preset(name: str) -> DubbingPreset:
    try:
        return PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(PRESETS))
        raise ValueError(f"Unknown dubbing preset: {name}. Available presets: {available}") from exc


def available_dubbing_presets() -> list[str]:
    return sorted(PRESETS)


def normalize_dubbing_voice(provider: str, model: str, voice: str) -> str:
    """Convert user-facing voice names to provider-native voice IDs."""
    if not voice:
        return voice
    if provider == "siliconflow":
        lowered = voice.lower()
        if lowered in SILICONFLOW_VOICE_ALIASES:
            return SILICONFLOW_VOICE_ALIASES[lowered]
        if ":" not in voice and "/" not in voice:
            return f"{model}:{voice}"
        return voice
    if provider == "gemini":
        for known in GEMINI_VOICES:
            if voice.lower() == known.lower():
                return known
        return voice
    if provider == "edge":
        lowered = voice.lower()
        if lowered in EDGE_VOICE_ALIASES:
            return EDGE_VOICE_ALIASES[lowered]
        return voice
    return voice


def validate_dubbing_voice(provider: str, voice: str) -> str | None:
    """Return an error message when a voice does not match provider constraints."""
    if not voice:
        return None
    if provider == "gemini" and voice not in GEMINI_VOICES:
        available = ", ".join(sorted(GEMINI_VOICES))
        return f"Unknown Gemini voice: {voice}. Available voices: {available}"
    if provider == "siliconflow" and ":" not in voice:
        return "SiliconFlow voice must be a built-in alias or a provider voice ID like model:voice"
    if provider == "edge":
        normalized = normalize_dubbing_voice(provider, "", voice)
        if normalized in EDGE_VOICE_ALIASES.values():
            return None
        if not normalized.endswith("Neural") or normalized.count("-") < 2:
            aliases = ", ".join(sorted(EDGE_VOICE_ALIASES))
            return f"Edge TTS voice must be a short alias ({aliases}) or a full voice ID like zh-CN-XiaoxiaoNeural"
    return None

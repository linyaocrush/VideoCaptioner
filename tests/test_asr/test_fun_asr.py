"""Tests for Bailian FunAudio-ASR (阿里云百炼 FunASR) integration.

Test strategy:
1. Unit tests for segment parsing (_make_segments) using mock responses
2. Unit tests for helper methods (_get_key, _language_hint, _format_http_error)
3. API error handling tests
4. Integration tests (skipped without env vars)
5. TranscribeConfig integration tests
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from videocaptioner.core.asr.asr_data import ASRDataSeg
from videocaptioner.core.asr.fun_asr import (
    BailianFunASR,
    FunASRTranscriptionResult,
)
from videocaptioner.core.entities import TranscribeConfig, TranscribeModelEnum

# ============================================================================
# 模拟响应数据
# ============================================================================

SAMPLE_SENTENCE_RESPONSE: FunASRTranscriptionResult = {
    "file_url": "oss://example/audio.mp3",
    "properties": {"audio_duration": 12.0},
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 12000,
            "text": "今天天气真好。我们去公园吧。",
            "sentences": [
                {
                    "begin_time": 0,
                    "end_time": 3000,
                    "text": "今天天气真好。",
                    "sentence_id": 0,
                    "speaker_id": 0,
                },
                {
                    "begin_time": 3000,
                    "end_time": 6000,
                    "text": "我们去公园吧。",
                    "sentence_id": 1,
                    "speaker_id": 0,
                },
            ],
        }
    ],
}

SAMPLE_WORD_RESPONSE: FunASRTranscriptionResult = {
    "file_url": "oss://example/audio.mp3",
    "properties": {"audio_duration": 5.0},
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 5000,
            "text": "hello world",
            "sentences": [
                {
                    "begin_time": 0,
                    "end_time": 2500,
                    "text": "hello world",
                    "sentence_id": 0,
                    "speaker_id": 0,
                    "words": [
                        {"begin_time": 0, "end_time": 1000, "text": "hello", "punctuation": ""},
                        {"begin_time": 1000, "end_time": 2500, "text": "world", "punctuation": ""},
                    ],
                }
            ],
        }
    ],
}

SAMPLE_WORD_RESPONSE_WITH_PUNCTUATION: FunASRTranscriptionResult = {
    "file_url": "oss://example/audio.mp3",
    "properties": {"audio_duration": 5.0},
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 5000,
            "text": "Hello! How are you?",
            "sentences": [
                {
                    "begin_time": 0,
                    "end_time": 5000,
                    "text": "Hello! How are you?",
                    "sentence_id": 0,
                    "speaker_id": 0,
                    "words": [
                        {"begin_time": 0, "end_time": 1000, "text": "Hello", "punctuation": "!"},
                        {"begin_time": 1500, "end_time": 2500, "text": "How", "punctuation": ""},
                        {"begin_time": 2500, "end_time": 3500, "text": "are", "punctuation": ""},
                        {"begin_time": 3500, "end_time": 5000, "text": "you", "punctuation": "?"},
                    ],
                }
            ],
        }
    ],
}

SAMPLE_MULTI_CHANNEL_RESPONSE: FunASRTranscriptionResult = {
    "file_url": "oss://example/audio.mp3",
    "properties": {"audio_duration": 3.0},
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 3000,
            "text": "Speaker A says hello",
            "sentences": [
                {
                    "begin_time": 0,
                    "end_time": 3000,
                    "text": "Speaker A says hello",
                    "sentence_id": 0,
                    "speaker_id": 0,
                }
            ],
        },
        {
            "channel_id": 1,
            "content_duration_in_milliseconds": 3000,
            "text": "Speaker B says hi",
            "sentences": [
                {
                    "begin_time": 0,
                    "end_time": 3000,
                    "text": "Speaker B says hi",
                    "sentence_id": 0,
                    "speaker_id": 1,
                }
            ],
        },
    ],
}

EMPTY_SENTENCES_RESPONSE: FunASRTranscriptionResult = {
    "file_url": "oss://example/audio.mp3",
    "properties": {"audio_duration": 0},
    "transcripts": [
        {
            "channel_id": 0,
            "content_duration_in_milliseconds": 0,
            "text": "",
            "sentences": [],
        }
    ],
}

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def asr_instance(test_audio_path: Path) -> BailianFunASR:
    """Create a basic FunASR instance for testing.

    Args:
        test_audio_path: Path to test audio file

    Returns:
        BailianFunASR instance
    """
    return BailianFunASR(
        audio_input=str(test_audio_path),
        use_cache=False,
        api_key="test-key",
        api_base="https://dashscope.aliyuncs.com",
        model="fun-asr",
        language="zh",
    )


@pytest.fixture
def asr_instance_en() -> BailianFunASR:
    """Create FunASR instance for English, without a real file (for unit tests).

    Uses a minimal byte input for BaseASR initialization.
    """
    return BailianFunASR(
        audio_input=b"\x00\x01\x02\x03",
        use_cache=False,
        api_key="test-key-en",
        api_base="https://dashscope.aliyuncs.com",
        model="fun-asr-v2",
        language="en",
    )


@pytest.fixture
def asr_instance_en_word() -> BailianFunASR:
    """Create FunASR with word-level timestamp enabled."""
    return BailianFunASR(
        audio_input=b"\x00\x01\x02\x03",
        use_cache=False,
        api_key="test-key-en",
        api_base="https://dashscope.aliyuncs.com",
        model="fun-asr-v2",
        language="en",
        need_word_time_stamp=True,
    )


# ============================================================================
# Unit Tests: 参数 & 初始化
# ============================================================================


class TestFunASRInit:
    """Test FunASR initialization and parameter handling."""

    def test_default_api_base(self, test_audio_path: Path) -> None:
        """Test that default API base URL is used when none provided."""
        asr = BailianFunASR(audio_input=str(test_audio_path), use_cache=False)
        assert asr.api_base == "https://dashscope.aliyuncs.com"

    def test_default_model(self, test_audio_path: Path) -> None:
        """Test that default model name is used when none provided."""
        asr = BailianFunASR(audio_input=str(test_audio_path), use_cache=False)
        assert asr.model == "fun-asr"

    def test_custom_parameters(self, test_audio_path: Path) -> None:
        """Test custom parameter overrides."""
        asr = BailianFunASR(
            audio_input=str(test_audio_path),
            api_key="custom-key",
            api_base="https://custom.example.com",
            model="fun-asr-v2",
            language="ja",
            poll_interval=5.0,
            timeout=3600,
        )
        assert asr.api_key == "custom-key"
        assert asr.api_base == "https://custom.example.com"
        assert asr.model == "fun-asr-v2"
        assert asr.language == "ja"
        assert asr.poll_interval == 5.0
        assert asr.timeout == 3600

    def test_api_base_strips_trailing_slash(self, test_audio_path: Path) -> None:
        """Test that trailing slash is stripped from API base URL."""
        asr = BailianFunASR(
            audio_input=str(test_audio_path),
            api_base="https://dashscope.aliyuncs.com/",
        )
        assert not asr.api_base.endswith("/")


# ============================================================================
# Unit Tests: 缓存键 (cache key)
# ============================================================================


class TestFunASRCacheKey:
    """Test cache key generation."""

    def test_cache_key_includes_model_and_language(self, asr_instance: BailianFunASR) -> None:
        """Test that cache key includes model and language parameters."""
        key = asr_instance._get_key()
        assert "fun-asr" in key
        assert "zh" in key

    def test_cache_key_different_for_different_params(self, test_audio_path: Path) -> None:
        """Test that different parameters produce different cache keys."""
        asr1 = BailianFunASR(
            audio_input=str(test_audio_path), model="fun-asr", language="zh"
        )
        asr2 = BailianFunASR(
            audio_input=str(test_audio_path), model="fun-asr-v2", language="en"
        )
        assert asr1._get_key() != asr2._get_key()


# ============================================================================
# Unit Tests: 语言提示
# ============================================================================


class TestFunASRLanguageHint:
    """Test language hint generation."""

    def test_supported_language(self, asr_instance: BailianFunASR) -> None:
        """Test supported language returns the language code."""
        assert asr_instance._language_hint() == "zh"

    def test_unsupported_language_returns_empty(self) -> None:
        """Test unsupported language returns empty string (auto-detect)."""
        asr = BailianFunASR(audio_input=b"\x00", language="xx")
        assert asr._language_hint() == ""

    def test_empty_language_returns_empty(self) -> None:
        """Test empty language returns empty string (auto-detect)."""
        asr = BailianFunASR(audio_input=b"\x00", language="")
        assert asr._language_hint() == ""

    def test_language_case_insensitive(self) -> None:
        """Test language hint is case-insensitive."""
        asr_upper = BailianFunASR(audio_input=b"\x00", language="ZH")
        asr_mixed = BailianFunASR(audio_input=b"\x00", language="Zh")
        assert asr_upper._language_hint() == "zh"
        assert asr_mixed._language_hint() == "zh"


# ============================================================================
# Unit Tests: HTTP 错误格式化
# ============================================================================


class TestFunASRErrorFormatting:
    """Test HTTP error message formatting."""

    def test_format_http_error_with_json(self, asr_instance_en: BailianFunASR) -> None:
        """Test formatting error from JSON response."""
        mock_response = _MockResponse(
            status_code=400,
            json_data={"message": "Invalid parameter", "code": "BadRequest"},
        )
        error_msg = asr_instance_en._format_http_error(mock_response)
        assert "400" in error_msg
        assert "Invalid parameter" in error_msg

    def test_format_http_error_without_json(self, asr_instance_en: BailianFunASR) -> None:
        """Test formatting error from non-JSON response."""
        mock_response = _MockResponse(status_code=500, text_body="Internal Server Error")
        error_msg = asr_instance_en._format_http_error(mock_response)
        assert "500" in error_msg
        assert "Internal Server Error" in error_msg

    def test_format_http_error_empty(self, asr_instance_en: BailianFunASR) -> None:
        """Test formatting error with minimal data."""
        mock_response = _MockResponse(status_code=502, json_data={})
        error_msg = asr_instance_en._format_http_error(mock_response)
        assert "502" in error_msg


# ============================================================================
# Unit Tests: 段落解析 (_make_segments)
# ============================================================================


class TestFunASRSegmentParsing:
    """Test segment parsing from FunASR API responses."""

    def test_sentence_level_parsing(self, asr_instance: BailianFunASR) -> None:
        """Test sentence-level timestamp parsing."""
        segments = asr_instance._make_segments(SAMPLE_SENTENCE_RESPONSE)
        assert len(segments) == 2
        assert segments[0].text == "今天天气真好。"
        assert segments[0].start_time == 0
        assert segments[0].end_time == 3000
        assert segments[1].text == "我们去公园吧。"

    def test_word_level_parsing(self, asr_instance_en_word: BailianFunASR) -> None:
        """Test word-level timestamp parsing."""
        segments = asr_instance_en_word._make_segments(SAMPLE_WORD_RESPONSE)
        assert len(segments) == 2
        assert segments[0].text == "hello"
        assert segments[0].start_time == 0
        assert segments[0].end_time == 1000
        assert segments[1].text == "world"

    def test_word_level_with_punctuation(self, asr_instance_en_word: BailianFunASR) -> None:
        """Test that punctuation is appended to word text."""
        segments = asr_instance_en_word._make_segments(SAMPLE_WORD_RESPONSE_WITH_PUNCTUATION)
        assert len(segments) == 4
        assert segments[0].text == "Hello!"
        assert segments[1].text == "How"
        assert segments[2].text == "are"
        assert segments[3].text == "you?"

    def test_multi_channel_merging(self, asr_instance_en: BailianFunASR) -> None:
        """Test that multi-channel transcripts are merged into one segment list."""
        segments = asr_instance_en._make_segments(SAMPLE_MULTI_CHANNEL_RESPONSE)
        assert len(segments) == 2
        texts = [s.text for s in segments]
        assert "Speaker A says hello" in texts
        assert "Speaker B says hi" in texts

    def test_empty_sentences(self, asr_instance_en: BailianFunASR) -> None:
        """Test handling of empty sentences list."""
        segments = asr_instance_en._make_segments(EMPTY_SENTENCES_RESPONSE)
        assert len(segments) == 0

    def test_empty_transcripts(self, asr_instance_en: BailianFunASR) -> None:
        """Test handling of empty transcripts list."""
        segments = asr_instance_en._make_segments({"file_url": "", "transcripts": []})
        assert len(segments) == 0

    def test_missing_transcripts_key(self, asr_instance_en: BailianFunASR) -> None:
        """Test handling of response without transcripts key."""
        segments = asr_instance_en._make_segments({})
        assert len(segments) == 0

    def test_segment_types(self, asr_instance: BailianFunASR) -> None:
        """Test that all segments are ASRDataSeg instances."""
        segments = asr_instance._make_segments(SAMPLE_SENTENCE_RESPONSE)
        for seg in segments:
            assert isinstance(seg, ASRDataSeg)


class TestFunASRWordSegments:
    """Test word-level segment parsing edge cases."""

    def test_sentence_without_words_falls_back_to_sentence(self, asr_instance_en_word: BailianFunASR) -> None:
        """Test that a sentence without words[] uses sentence-level bounds."""
        response: FunASRTranscriptionResult = {
            "file_url": "oss://example/a.mp3",
            "transcripts": [{
                "channel_id": 0,
                "content_duration_in_milliseconds": 3000,
                "text": "hello",
                "sentences": [
                    {
                        "begin_time": 100,
                        "end_time": 2000,
                        "text": "hello",
                        "sentence_id": 0,
                        "speaker_id": 0,
                        "words": [],  # empty words list triggers fallback
                    }
                ],
            }],
        }
        segments = asr_instance_en_word._make_segments(response)
        assert len(segments) == 1
        assert segments[0].text == "hello"
        assert segments[0].start_time == 100
        assert segments[0].end_time == 2000

    def test_sentence_with_none_words(self, asr_instance_en_word: BailianFunASR) -> None:
        """Test that sentences with None words are handled gracefully."""
        response: FunASRTranscriptionResult = {
            "file_url": "oss://example/a.mp3",
            "transcripts": [{
                "channel_id": 0,
                "content_duration_in_milliseconds": 1000,
                "text": "hi",
                "sentences": [
                    {
                        "begin_time": 0,
                        "end_time": 1000,
                        "text": "hi",
                        "sentence_id": 0,
                        "speaker_id": 0,
                        # missing "words" key entirely
                    }
                ],
            }],
        }
        segments = asr_instance_en_word._make_segments(response)
        assert len(segments) == 1
        assert segments[0].text == "hi"


# ============================================================================
# Unit Tests: 任务失败消息格式化
# ============================================================================


class TestFunASRTaskFailure:
    """Test task failure message formatting."""

    def test_failure_with_code_and_message(self, asr_instance_en: BailianFunASR) -> None:
        """Test failure message with code and message."""
        output: Any = {
            "task_status": "FAILED",
            "results": [
                {"code": "ModelError", "message": "Model not available", "subtask_status": "FAILED"}
            ],
        }
        msg = asr_instance_en._format_task_failure(output)
        assert "ModelError" in msg
        assert "Model not available" in msg

    def test_failure_with_message_only(self, asr_instance_en: BailianFunASR) -> None:
        """Test failure message with message only."""
        output: Any = {
            "task_status": "FAILED",
            "results": [
                {"message": "Timeout", "subtask_status": "FAILED"}
            ],
        }
        msg = asr_instance_en._format_task_failure(output)
        assert "Timeout" in msg

    def test_failure_with_status_only(self, asr_instance_en: BailianFunASR) -> None:
        """Test fallback when no results detail available."""
        output: Any = {"task_status": "FAILED", "results": []}
        msg = asr_instance_en._format_task_failure(output)
        assert "FAILED" in msg

    def test_pick_transcription_url(self, asr_instance_en: BailianFunASR) -> None:
        """Test picking the successful transcription URL from results."""
        output: Any = {
            "task_status": "SUCCEEDED",
            "results": [
                {"subtask_status": "FAILED", "code": "err"},
                {"subtask_status": "SUCCEEDED", "transcription_url": "https://example.com/result.json"},
            ],
        }
        url = asr_instance_en._pick_transcription_url(output)
        assert url == "https://example.com/result.json"

    def test_pick_transcription_url_no_success(self, asr_instance_en: BailianFunASR) -> None:
        """Test exception when no successful transcription URL found."""
        output: Any = {
            "task_status": "FAILED",
            "results": [{"subtask_status": "FAILED"}],
        }
        with pytest.raises(RuntimeError):
            asr_instance_en._pick_transcription_url(output)


# ============================================================================
# 辅助 Mock 类
# ============================================================================


class _MockResponse:
    """模拟 requests.Response 用于测试 _format_http_error"""

    def __init__(self, status_code: int, json_data: dict | None = None, text_body: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self._text = text_body

    def json(self) -> dict:
        if self._json_data is not None:
            return self._json_data
        raise ValueError("No JSON data")

    @property
    def text(self) -> str:
        return self._text


# ============================================================================
# Integration Tests: 需要环境变量
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestFunASRIntegration:
    """Integration tests for FunASR (requires DASHSCOPE_API_KEY or similar).

    These tests are skipped unless the required environment variable is set.
    """

    @pytest.fixture(autouse=True)
    def skip_if_no_env(self, check_env_vars) -> None:
        """Skip integration tests if no FunASR API key is configured."""
        check_env_vars("DASHSCOPE_API_KEY", "FUN_ASR_API_KEY")

    def test_sentence_level(self, test_audio_path_zh: Path) -> None:
        """Test sentence-level transcription with real API.

        Args:
            test_audio_path_zh: Path to Chinese test audio
        """
        import os

        asr = BailianFunASR(
            audio_input=str(test_audio_path_zh),
            api_key=os.getenv("FUN_ASR_API_KEY") or os.getenv("DASHSCOPE_API_KEY", ""),
            language="zh",
            need_word_time_stamp=False,
        )
        result = asr.run()
        assert result is not None
        assert len(result.segments) > 0
        assert not result.is_word_timestamp()


# ============================================================================
# Tests: TranscribeConfig 整合
# ============================================================================


class TestFunASRTranscribeConfig:
    """Test FunASR fields in TranscribeConfig."""

    def test_fun_asr_config_creation(self) -> None:
        """Test creating a TranscribeConfig with FunASR settings."""
        config = TranscribeConfig(
            transcribe_model=TranscribeModelEnum.FUN_ASR,
            fun_asr_api_key="test-key",
            fun_asr_api_base="https://dashscope.aliyuncs.com",
            fun_asr_model="fun-asr",
        )
        assert config.transcribe_model == TranscribeModelEnum.FUN_ASR
        assert config.fun_asr_api_key == "test-key"
        assert config.fun_asr_api_base == "https://dashscope.aliyuncs.com"
        assert config.fun_asr_model == "fun-asr"

    def test_fun_asr_config_print(self) -> None:
        """Test print_config() includes FunASR info."""
        config = TranscribeConfig(
            transcribe_model=TranscribeModelEnum.FUN_ASR,
            fun_asr_api_key="sk-test-key-12345",
            fun_asr_api_base="https://dashscope.aliyuncs.com",
            fun_asr_model="fun-asr",
            transcribe_language="zh",
        )
        output = config.print_config()
        assert "FunASR" in output or "百炼" in output
        assert config.fun_asr_api_base in output
        assert config.fun_asr_model in output

    def test_fun_asr_config_mask_key(self) -> None:
        """Test that API key is masked in print_config()."""
        config = TranscribeConfig(
            transcribe_model=TranscribeModelEnum.FUN_ASR,
            fun_asr_api_key="sk-test-key-12345",
            fun_asr_api_base="https://dashscope.aliyuncs.com",
            fun_asr_model="fun-asr",
        )
        output = config.print_config()
        assert "sk-test-key-12345" not in output, "Full API key should not appear in log"
        # _mask_key returns "sk-t...2345" for keys longer than 8 chars
        # Just verify the original key isn't leaked
        assert "sk-test-key" not in output


# ============================================================================
# Tests: ASR 语言能力
# ============================================================================


class TestFunASRLanguageCapability:
    """Test FunASR language capability configuration."""

    def test_language_capability_exists(self) -> None:
        """Test that FunASR has language capability entry."""
        from videocaptioner.core.entities import ASR_LANGUAGE_CAPABILITIES

        assert TranscribeModelEnum.FUN_ASR in ASR_LANGUAGE_CAPABILITIES

    def test_supports_auto_detect(self) -> None:
        """Test that FunASR supports auto-detection."""
        from videocaptioner.core.entities import ASR_LANGUAGE_CAPABILITIES, get_asr_language_capability

        capability = get_asr_language_capability(TranscribeModelEnum.FUN_ASR)
        assert capability.supports_auto

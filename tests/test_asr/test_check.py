"""Tests for the ASR diagnostic check module (core.asr.check).

Tests are structured as unit tests using mocks, plus integration tests
that require environment variables.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from videocaptioner.core.asr.check import (
    TEST_AUDIO_PATH,
    TranscribeCheckResult,
    check_transcribe,
)
from videocaptioner.core.asr.asr_data import ASRData, ASRDataSeg
from videocaptioner.core.entities import TranscribeConfig, TranscribeModelEnum


# ============================================================================
# 单元测试：TranscribeCheckResult
# ============================================================================


class TestTranscribeCheckResult:
    """Test the TranscribeCheckResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a success result."""
        result = TranscribeCheckResult(success=True, detail="Hello world")
        assert result.success
        assert result.detail == "Hello world"

    def test_failure_result(self) -> None:
        """Test creating a failure result."""
        result = TranscribeCheckResult(success=False, detail="API Key invalid")
        assert not result.success
        assert result.detail == "API Key invalid"

    def test_result_is_frozen(self) -> None:
        """Test that TranscribeCheckResult is frozen (immutable)."""
        result = TranscribeCheckResult(success=True, detail="test")
        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]


# ============================================================================
# 单元测试：音频文件缺失
# ============================================================================


class TestCheckTranscribeNoAudio:
    """Test check_transcribe when audio file is missing."""

    def test_audio_file_not_found(self) -> None:
        """Test that a non-existent audio path returns failure."""
        config = TranscribeConfig(
            transcribe_model=TranscribeModelEnum.BIJIAN,
        )
        result = check_transcribe(config, audio_path="/nonexistent/file.wav")
        assert not result.success
        assert "不存在" in result.detail


# ============================================================================
# 单元测试：Mock 化 ASR 调用
# ============================================================================


class TestCheckTranscribeWithMock:
    """Test check_transcribe with mocked transcribe() and video2audio()."""

    def _make_sample_asr_data(self, text: str = "Hello world") -> ASRData:
        segments = [ASRDataSeg(start_time=0, end_time=1000, text=text)]
        return ASRData(segments)

    def test_successful_check(self, test_audio_path: Path) -> None:
        """Test successful transcription check."""
        with (
            patch("videocaptioner.core.asr.check.video2audio", return_value=True),
            patch("videocaptioner.core.asr.check.transcribe") as mock_transcribe,
        ):
            mock_transcribe.return_value = self._make_sample_asr_data(
                "Welcome to VideoCaptioner"
            )

            config = TranscribeConfig(
                transcribe_model=TranscribeModelEnum.BIJIAN,
            )
            result = check_transcribe(config, audio_path=str(test_audio_path))

        assert result.success
        assert "Welcome to VideoCaptioner" in result.detail

    def test_empty_transcript(self, test_audio_path: Path) -> None:
        """Test that an empty transcript returns failure."""
        with (
            patch("videocaptioner.core.asr.check.video2audio", return_value=True),
            patch("videocaptioner.core.asr.check.transcribe") as mock_transcribe,
        ):
            mock_transcribe.return_value = self._make_sample_asr_data("  ")

            config = TranscribeConfig(
                transcribe_model=TranscribeModelEnum.BIJIAN,
            )
            result = check_transcribe(config, audio_path=str(test_audio_path))

        assert not result.success
        assert "结果为空" in result.detail

    def test_transcribe_raises_exception(self, test_audio_path: Path) -> None:
        """Test that exceptions from transcribe() are caught."""
        with (
            patch("videocaptioner.core.asr.check.video2audio", return_value=True),
            patch(
                "videocaptioner.core.asr.check.transcribe",
                side_effect=ValueError("Connection refused"),
            ),
        ):
            config = TranscribeConfig(
                transcribe_model=TranscribeModelEnum.WHISPER_API,
            )
            result = check_transcribe(config, audio_path=str(test_audio_path))

        assert not result.success
        assert "Connection refused" in result.detail

    def test_video2audio_fails(self, test_audio_path: Path) -> None:
        """Test that video2audio failure returns appropriate error."""
        with patch("videocaptioner.core.asr.check.video2audio", return_value=False):
            config = TranscribeConfig(
                transcribe_model=TranscribeModelEnum.BIJIAN,
            )
            result = check_transcribe(config, audio_path=str(test_audio_path))

        assert not result.success
        # 可能是 ffmpeg 或 提取 相关的中文错误信息
        assert not result.success

    def test_cache_disabled_during_check(self, test_audio_path: Path) -> None:
        """Test that cache is disabled during the check."""
        from videocaptioner.core.utils import cache as cache_utils

        # Enable cache first
        cache_utils.enable_cache()
        assert cache_utils.is_cache_enabled()

        with (
            patch("videocaptioner.core.asr.check.video2audio", return_value=True),
            patch("videocaptioner.core.asr.check.transcribe") as mock_transcribe,
        ):
            mock_transcribe.return_value = self._make_sample_asr_data("test")

            config = TranscribeConfig(
                transcribe_model=TranscribeModelEnum.BIJIAN,
            )
            check_transcribe(config, audio_path=str(test_audio_path))

        # Cache should have been restored after check
        assert cache_utils.is_cache_enabled()


# ============================================================================
# 真实集成测试（使用真实音频文件路径，但 mock ASR 调用）
# ============================================================================


@pytest.mark.slow
class TestCheckTranscribeRealAudio:
    """Test check_transcribe with real audio file (still mocks the ASR call)."""

    def test_with_real_audio_path(self, test_audio_path: Path) -> None:
        """Test that real audio path is processed correctly."""
        with (
            patch("videocaptioner.core.asr.check.transcribe") as mock_transcribe,
        ):
            mock_transcribe.return_value = ASRData([
                ASRDataSeg(start_time=0, end_time=500, text="Hello test"),
            ])

            config = TranscribeConfig(
                transcribe_model=TranscribeModelEnum.WHISPER_API,
                whisper_api_key="test-key",
                whisper_api_base="https://api.openai.com/v1",
            )
            result = check_transcribe(config, audio_path=str(test_audio_path))

        assert result.success
        assert "Hello test" in result.detail

    def test_builtin_test_audio_exists(self) -> None:
        """Test that the built-in test audio file exists."""
        assert (
            TEST_AUDIO_PATH.exists()
        ), f"Built-in test audio not found: {TEST_AUDIO_PATH}"

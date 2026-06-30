"""本地 ASR 运行程序的检测与安装方案。

检测口径与 ``core/asr`` 保持一致：先查 PATH，再查应用 bin 目录。
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from videocaptioner.core.download.models import KIND_FASTER_WHISPER, KIND_WHISPER_CPP, ModelFile

WHISPER_CPP_EXECUTABLES = ("whisper-cli", "whisper-cpp", "whisper", "whisper-cpp-main")
FASTER_WHISPER_EXECUTABLES = (
    "faster-whisper-xxl", "faster-whisper", "whisper-faster", "faster_whisper",
)

_EXECUTABLES = {
    KIND_WHISPER_CPP: WHISPER_CPP_EXECUTABLES,
    KIND_FASTER_WHISPER: FASTER_WHISPER_EXECUTABLES,
}

WHISPER_CPP_RELEASES_URL = "https://github.com/ggerganov/whisper.cpp/releases"
FASTER_WHISPER_XXL_7Z_URL = (
    "https://modelscope.cn/models/bkfengg/whisper-cpp/resolve/master/"
    "Faster-Whisper-XXL_r245.2_windows.7z"
)

_FASTER_WHISPER_CPU_EXE = ModelFile(
    name="whisper-faster.exe",
    urls=("https://modelscope.cn/models/bkfengg/whisper-cpp/resolve/master/whisper-faster.exe",),
    size_bytes=88_436_526,
)


@dataclass(frozen=True)
class ProgramStatus:
    installed: bool
    name: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class ProgramVariant:
    key: str
    title: str
    description_missing: str
    description_ready: str
    executables: tuple[str, ...]
    command: str | None = None
    download: ModelFile | None = None
    link: str | None = None

    def detect(self, extra_dirs: tuple[Path, ...] | None = None) -> ProgramStatus:
        return _detect_executables(self.executables, extra_dirs)


@dataclass(frozen=True)
class ProgramInstallPlan:
    summary: str
    command: str | None = None
    download: ModelFile | None = None
    link: str | None = None
    supported: bool = True


def detect_program(kind: str, extra_dirs: tuple[Path, ...] | None = None) -> ProgramStatus:
    return _detect_executables(_EXECUTABLES.get(kind, ()), extra_dirs)


def _detect_executables(
    names: tuple[str, ...], extra_dirs: tuple[Path, ...] | None = None
) -> ProgramStatus:
    dirs = extra_dirs if extra_dirs is not None else _default_bin_dirs()
    for name in names:
        path = shutil.which(name)
        if path:
            return ProgramStatus(True, name, path)
        for directory in dirs:
            for candidate in (directory / name, directory / f"{name}.exe"):
                if candidate.exists():
                    return ProgramStatus(True, name, str(candidate))
    return ProgramStatus(False)


def _default_bin_dirs() -> tuple[Path, ...]:
    from videocaptioner.config import BIN_PATH, FASTER_WHISPER_PATH

    return (Path(BIN_PATH), Path(FASTER_WHISPER_PATH))


def program_variants(kind: str, platform: str | None = None) -> tuple[ProgramVariant, ...]:
    plat = platform or sys.platform
    if kind == KIND_WHISPER_CPP:
        if plat == "darwin":
            return (
                ProgramVariant(
                    key="default", title="Whisper CPP 程序",
                    description_missing="未找到本地运行程序",
                    description_ready="可执行文件已找到",
                    executables=WHISPER_CPP_EXECUTABLES,
                    command="brew install whisper-cpp",
                    link=WHISPER_CPP_RELEASES_URL,
                ),
            )
        return (
            ProgramVariant(
                key="default", title="Whisper CPP 程序",
                description_missing="未找到本地运行程序，可从官方页面下载",
                description_ready="可执行文件已找到",
                executables=WHISPER_CPP_EXECUTABLES,
                link=WHISPER_CPP_RELEASES_URL,
            ),
        )
    if kind == KIND_FASTER_WHISPER:
        if not plat.startswith("win"):
            return ()
        return (
            ProgramVariant(
                key="cpu", title="CPU 版",
                description_missing="没有独立显卡也能用",
                description_ready="可执行文件已找到",
                executables=("whisper-faster",),
                download=_FASTER_WHISPER_CPU_EXE,
            ),
            ProgramVariant(
                key="gpu", title="GPU 版",
                description_missing="有 NVIDIA 显卡时选择，长视频更快",
                description_ready="可执行文件已找到",
                executables=("faster-whisper-xxl", "faster-whisper", "faster_whisper"),
                link=FASTER_WHISPER_XXL_7Z_URL,
            ),
        )
    raise ValueError(f"unknown program kind: {kind}")


def program_install_plan(kind: str, platform: str | None = None) -> ProgramInstallPlan:
    plat = platform or sys.platform
    if kind == KIND_WHISPER_CPP:
        if plat == "darwin":
            return ProgramInstallPlan(
                summary="用 Homebrew 安装 whisper.cpp，完成后点重新检测。",
                command="brew install whisper-cpp", link=WHISPER_CPP_RELEASES_URL,
            )
        if plat.startswith("win"):
            return ProgramInstallPlan(
                summary="下载官方预编译包，解压到任意 PATH 目录或应用 bin 目录。",
                link=WHISPER_CPP_RELEASES_URL,
            )
        return ProgramInstallPlan(
            summary="用系统包管理器安装 whisper.cpp（或自行编译），完成后点重新检测。",
            link=WHISPER_CPP_RELEASES_URL,
        )
    if kind == KIND_FASTER_WHISPER:
        if plat.startswith("win"):
            return ProgramInstallPlan(
                summary="可直接下载 CPU 版程序；需要 GPU 加速请手动下载 XXL 完整包。",
                download=_FASTER_WHISPER_CPU_EXE, link=FASTER_WHISPER_XXL_7Z_URL,
            )
        return ProgramInstallPlan(
            summary="Faster Whisper 独立程序仅支持 Windows，当前系统请改用 WhisperCpp。",
            supported=False,
        )
    raise ValueError(f"unknown program kind: {kind}")

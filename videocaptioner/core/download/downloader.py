"""通用文件下载器。

设计要点：
- 一个文件可配多个镜像 URL，按顺序兜底（连接失败/超时/4xx/5xx 都切下一个）；
- 下载写入 ``<dest>.part``，完成并通过校验后原子替换到目标路径；
- 同一 URL 重试时用 HTTP Range 续传 ``.part``，服务器不支持就从头来；
- 进度通过回调上报，取消通过回调轮询。
"""

from __future__ import annotations

import hashlib
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
CHUNK_SIZE = 256 * 1024


class DownloadError(Exception):
    """所有镜像都下载失败。"""
    pass


class DownloadCancelled(Exception):
    """下载被调用方取消。"""
    pass


CancelCheck = Callable[[], bool]


@dataclass(frozen=True)
class DownloadProgress:
    received: int


def download_file(
    urls: tuple[str, ...],
    dest: Path,
    *,
    sha1: str | None = None,
    on_progress: Callable[[DownloadProgress], None] | None = None,
    should_cancel: CancelCheck | None = None,
) -> Path:
    """从镜像 URL 列表下载文件到目标路径，支持断点续传和 SHA1 校验。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    existing = part.stat().st_size if part.exists() else 0

    for url in urls:
        if should_cancel and should_cancel():
            raise DownloadCancelled()
        try:
            _download_one(url, part, existing=existing, on_progress=on_progress)
            break
        except (requests.RequestException, OSError) as exc:
            logger.warning("下载失败 %s: %s", url, exc)
            existing = part.stat().st_size if part.exists() else 0
            continue
    else:
        raise DownloadError(f"所有镜像下载失败: {urls[0]}")

    if sha1:
        _verify_sha1(part, sha1)

    part.rename(dest)
    return dest


def _download_one(
    url: str,
    dest: Path,
    *,
    existing: int = 0,
    on_progress: Callable[[DownloadProgress], None] | None = None,
) -> None:
    headers = {}
    if existing:
        headers["Range"] = f"bytes={existing}-"
    resp = requests.get(url, headers=headers, stream=True, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
    if resp.status_code in (416,):
        # Range not satisfiable — file is complete
        return
    if resp.status_code == 200 and existing:
        existing = 0
    elif resp.status_code == 206:
        pass
    elif resp.status_code == 200:
        existing = 0
    else:
        resp.raise_for_status()

    mode = "ab" if existing else "wb"
    received = existing
    with open(dest, mode) as f:
        for chunk in resp.iter_content(CHUNK_SIZE):
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)
            if on_progress:
                on_progress(DownloadProgress(received))


def _verify_sha1(path: Path, expected: str) -> None:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if not chunk:
                break
            h.update(chunk)
    actual = h.hexdigest()
    if actual != expected:
        path.unlink(missing_ok=True)
        raise DownloadError(f"SHA1 校验失败: 期望 {expected}, 实际 {actual}")

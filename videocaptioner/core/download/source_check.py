"""视频下载源连通性检查：用 yt-dlp 真实解析稳定公开视频。

诊断页"视频下载"项与 ``videocaptioner doctor --check-api`` 共用。
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

from videocaptioner.core.download import net


@dataclass(frozen=True)
class DownloadSource:
    key: str
    title: str
    probe_url: str
    fix_hint: str


DOWNLOAD_SOURCES: tuple[DownloadSource, ...] = (
    DownloadSource(
        key="youtube",
        title="YouTube",
        probe_url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
        fix_hint="访问 YouTube 通常需要代理：开启系统代理或设置 HTTPS_PROXY 后重试。",
    ),
    DownloadSource(
        key="bilibili",
        title="哔哩哔哩",
        probe_url="https://www.bilibili.com/video/BV1GJ411x7h7",
        fix_hint="检查网络后重试；若提示风控（412），先在浏览器中登录哔哩哔哩，或导出 cookies.txt 到应用数据目录。",
    ),
)


@dataclass(frozen=True)
class SourceCheckResult:
    key: str
    title: str
    success: bool
    detail: str


def _probe_title(url: str, timeout: int, cookies_browser: Optional[str]) -> str:
    import yt_dlp

    options = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "noplaylist": True, "socket_timeout": timeout,
        "retries": 0, "extractor_retries": 0,
    }
    proxy = net.proxy_for_url(url)
    if proxy is not None:
        options["proxy"] = proxy
    if cookies_browser is not None:
        options["cookiesfrombrowser"] = (cookies_browser,)
    elif net.cookies_file().exists():
        options["cookiefile"] = str(net.cookies_file())

    with yt_dlp.YoutubeDL(options) as ydl:
        if net.is_bilibili_url(url):
            net.inject_bilibili_buvid(ydl)
        info = ydl.extract_info(url, download=False, process=False)
    title = str(info.get("title") or "").strip()
    if not title:
        raise RuntimeError("解析成功但没有取到视频信息")
    return title


def check_download_source(source: DownloadSource, timeout: int = 15) -> SourceCheckResult:
    """真实解析一条稳定公开链接，验证该站点当前可用。"""
    try:
        title, used_browser = net.run_with_browser_cookie_fallback(
            source.probe_url,
            lambda browser: _probe_title(source.probe_url, timeout, browser),
        )
    except Exception as exc:
        return SourceCheckResult(source.key, source.title, False, str(exc))
    detail = title if not used_browser else f"{title}（已通过 {used_browser} 登录态验证）"
    return SourceCheckResult(source.key, source.title, True, detail)


def check_download_sources(timeout: int = 15) -> list[SourceCheckResult]:
    """并行检查全部下载源。"""
    with ThreadPoolExecutor(max_workers=len(DOWNLOAD_SOURCES)) as pool:
        futures = [
            pool.submit(check_download_source, source, timeout)
            for source in DOWNLOAD_SOURCES
        ]
        return [future.result() for future in futures]

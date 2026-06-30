"""yt-dlp 在线视频下载引擎（无 Qt 依赖）。

GUI 下载线程与 CLI download 命令共用本引擎。
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Optional

import requests
import yt_dlp

from videocaptioner.core.download import net
from videocaptioner.core.utils.logger import setup_logger

logger = setup_logger("media_download")

_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

_DEFAULT_FORMAT = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
_HLS_FORMAT = "bestvideo[protocol^=m3u8]+bestaudio[protocol^=m3u8]/best[protocol^=m3u8]/best"

ProgressCallback = Callable[[int, str], None]
StatsCallback = Callable[[str, str], None]
InfoCallback = Callable[[dict], None]
CancelCheck = Callable[[], None]


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """清理文件名：非法字符、控制符、结尾空格点、超长与 Windows 保留名。"""
    sanitized = re.sub(r'[<>:"/\\|?*]', replacement, name)
    sanitized = re.sub(r"[\x00-\x1f]", "", sanitized).rstrip(" .")
    if len(sanitized) > 255:
        base, ext = os.path.splitext(sanitized)
        sanitized = base[: 255 - len(ext)] + ext
    if os.path.splitext(sanitized)[0].upper() in _WINDOWS_RESERVED:
        sanitized = f"{sanitized}_"
    return sanitized or "media"


class MediaDownloader:
    """把一个 http(s) 链接下载到 target_dir，连同可用的同语言字幕。"""

    def __init__(
        self,
        url: str,
        target_dir: Optional[str] = None,
        *,
        probe_only: bool = False,
        max_height: Optional[int] = None,
        on_progress: Optional[ProgressCallback] = None,
        on_stats: Optional[StatsCallback] = None,
        on_media: Optional[InfoCallback] = None,
        on_probed: Optional[InfoCallback] = None,
        cancel_check: Optional[CancelCheck] = None,
    ):
        if not probe_only and not target_dir:
            raise ValueError("target_dir is required unless probe_only")
        self.url = url
        self.target_dir = target_dir
        self.probe_only = probe_only
        self.max_height = max_height
        self._on_progress = on_progress or (lambda _v, _m: None)
        self._on_stats = on_stats or (lambda _s, _e: None)
        self._on_media = on_media or (lambda _info: None)
        self._on_probed = on_probed or (lambda _info: None)
        self._cancel_check = cancel_check or (lambda: None)

    def run(self) -> tuple[Optional[str], Optional[str]]:
        """执行下载（或 probe），返回 (视频路径, 字幕路径或 None)。"""
        result, _used_browser = net.run_with_browser_cookie_fallback(
            self.url,
            self._download_any,
            on_attempt=lambda title: self._on_progress(0, f"读取 {title} 登录态重试"),
            cancel_check=self._cancel_check,
        )
        return result

    def _download_any(
        self, cookies_browser: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str]]:
        try:
            return self._download(self._preferred_format(), cookies_browser)
        except Exception as exc:
            self._cancel_check()
            message = str(exc)
            if "ted.com" in self.url and "HTTP Error 403" in message:
                logger.warning("TED mp4 直链失败，改用 HLS 流重试: %s", exc)
                return self._download(_HLS_FORMAT, cookies_browser)
            if "youtu" in self.url and "HTTP Error 403" in message:
                logger.warning("YouTube 403 节流，改用 android 播放端重试")
                self._on_progress(0, "切换播放端重试")
                return self._download(
                    self._preferred_format(),
                    cookies_browser,
                    player_client=("android", "web_safari"),
                )
            raise

    def _preferred_format(self) -> str:
        if not self.max_height:
            return _DEFAULT_FORMAT
        h = self.max_height
        return (
            f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height<={h}][ext=mp4]/best[height<={h}]/best"
        )

    def _progress_hook(self, data: dict):
        self._cancel_check()
        if data.get("status") != "downloading":
            return
        percent = net.strip_ansi(data.get("_percent_str", "0")).replace("%", "")
        speed = net.strip_ansi(data.get("_speed_str", "")) or "--"
        eta = net.strip_ansi(data.get("_eta_str", "")) or "--"
        try:
            value = int(float(percent))
        except ValueError:
            value = 0
        self._on_progress(value, "正在下载媒体")
        self._on_stats(speed, f"剩余 {eta}")

    def _download(
        self,
        video_format: str,
        cookies_browser: Optional[str] = None,
        player_client: Optional[tuple[str, ...]] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        logger.info("开始下载: %s", self.url)
        options = {
            "outtmpl": {"default": "%(title).200s.%(ext)s"},
            "format": video_format,
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
        }
        if player_client is not None:
            options["extractor_args"] = {"youtube": {"player_client": list(player_client)}}
        proxy = net.proxy_for_url(self.url)
        if proxy:
            logger.info("使用代理: %s", proxy)
            options["proxy"] = proxy
        elif proxy == "":
            options["proxy"] = ""
        if cookies_browser is not None:
            options["cookiesfrombrowser"] = (cookies_browser,)
        elif net.cookies_file().exists():
            logger.info("使用 cookies: %s", net.cookies_file())
            options["cookiefile"] = str(net.cookies_file())

        with yt_dlp.YoutubeDL(options) as ydl:
            if net.is_bilibili_url(self.url):
                net.inject_bilibili_buvid(ydl)
            self._on_progress(0, "解析视频信息")
            info = ydl.extract_info(self.url, download=False)
            self._cancel_check()
            if info.get("_type") == "playlist":
                entries = [entry for entry in info.get("entries") or [] if entry]
                if not entries:
                    raise RuntimeError("链接里没有可下载的视频。")
                info = entries[0]
            if info.get("is_live"):
                raise RuntimeError("暂不支持下载直播，请等视频生成回放后再试。")
            self._on_media(media_summary(info))
            if self.probe_only:
                self._on_probed(probe_summary(info))
                return None, None

            target_dir = Path(self.target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            language = (info.get("language") or "").lower().split("-")[0] or None
            if language:
                ydl.params["subtitleslangs"] = [language]
            ydl.params.update({"paths": {"home": str(target_dir)}})
            ydl.process_info(info)
            self._cancel_check()

            video_path = Path(ydl.prepare_filename(info))
            subtitle_path = resolve_downloaded_subtitle(info, video_path, language, proxy)
            logger.info("下载完成: %s (字幕: %s)", video_path, subtitle_path)
            return (
                str(video_path) if video_path.exists() else None,
                subtitle_path,
            )


def resolve_downloaded_subtitle(
    info: dict, video_path: Path, language: Optional[str], proxy: Optional[str] = None
) -> Optional[str]:
    """取与视频同语言的字幕 sidecar。"""
    from videocaptioner.core.entities import SupportedSubtitleFormats

    usable = {f".{fmt.value}" for fmt in SupportedSubtitleFormats}
    downloaded = next(
        (
            file
            for file in sorted(video_path.parent.iterdir())
            if file != video_path
            and file.name.startswith(video_path.stem)
            and file.suffix.lower() in usable
        ),
        None,
    )
    if downloaded is None:
        return None
    if not language or f".{language}" in downloaded.name.lower():
        return str(downloaded)

    link = None
    for captions in (info.get("subtitles"), info.get("automatic_captions")):
        if not captions:
            continue
        for code, tracks in captions.items():
            if code.startswith(language) and tracks:
                link = tracks[-1].get("url")
                break
        if link:
            break
    downloaded.unlink(missing_ok=True)
    if not link:
        return None
    try:
        with requests.Session() as session:
            if proxy:
                session.proxies.update({"http": proxy, "https": proxy})
            elif proxy == "":
                session.trust_env = False
            text = session.get(link, timeout=30).text
    except requests.RequestException:
        logger.warning("按语言重下字幕失败: %s", link)
        return None
    if not text:
        return None
    target = video_path.parent / f"{video_path.stem}.{language}.vtt"
    target.write_text(text, encoding="utf-8")
    return str(target)


def media_summary(info: dict) -> dict:
    """从 yt-dlp info 提取站点通用的展示字段。"""
    summary = {"title": info.get("title") or ""}
    if info.get("uploader"):
        summary["uploader"] = info["uploader"]
    duration = info.get("duration")
    if duration:
        minutes, seconds = divmod(int(duration), 60)
        if minutes >= 60:
            hours, minutes = divmod(minutes, 60)
            summary["duration"] = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            summary["duration"] = f"{minutes:02d}:{seconds:02d}"
    site = info.get("extractor_key") or ""
    if site and site.lower() != "generic":
        summary["site"] = site
    return summary


def probe_summary(info: dict) -> dict:
    """probe 模式的解析结果：元数据 + 清晰度档位 + 字幕可用性。"""
    summary = media_summary(info)
    heights = sorted(
        {
            f["height"]
            for f in info.get("formats") or []
            if f.get("height") and f.get("vcodec") != "none"
        },
        reverse=True,
    )
    qualities = [h for h in heights if h >= 144]
    if not qualities and info.get("height"):
        qualities = [int(info["height"])]
    summary["qualities"] = qualities
    summary["has_subtitle"] = bool(info.get("subtitles"))
    return summary

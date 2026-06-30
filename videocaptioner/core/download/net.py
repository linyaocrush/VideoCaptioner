"""在线视频下载的网络环境：代理、cookies、浏览器登录态、B 站风控、错误翻译。

下载引擎（core/download/media.py）与诊断的下载源检查（source_check.py）
共用这里的逻辑。
"""

from __future__ import annotations

import json
import os
import platform
import re
import urllib.request
from http.cookiejar import Cookie
from pathlib import Path
from typing import Callable, Optional, TypeVar

from videocaptioner.config import APPDATA_PATH
from videocaptioner.core.utils.logger import setup_logger

logger = setup_logger("download_net")

T = TypeVar("T")

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def cookies_file() -> Path:
    return APPDATA_PATH / "cookies.txt"


def system_proxy() -> Optional[str]:
    """探测可用代理：环境变量优先，其次操作系统代理设置。"""
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = os.environ.get(key)
        if value:
            return value
    try:
        if platform.system() == "Darwin":
            import _scproxy
            proxies = _scproxy._get_proxies()
        else:
            proxies = urllib.request.getproxies()
    except Exception:
        return None
    return proxies.get("https") or proxies.get("http")


def fetch_bilibili_buvid(timeout: int = 8) -> dict[str, str]:
    """从 B 站 spi 接口领一份匿名设备指纹 cookie（buvid3/buvid4）。"""
    request = urllib.request.Request(
        "https://api.bilibili.com/x/frontend/finger/spi",
        headers={"User-Agent": _BROWSER_UA, "Referer": "https://www.bilibili.com/"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
        data = payload.get("data") or {}
        cookies = {}
        if data.get("b_3"):
            cookies["buvid3"] = data["b_3"]
        if data.get("b_4"):
            cookies["buvid4"] = data["b_4"]
        return cookies
    except Exception as exc:
        logger.warning("获取 B 站匿名 buvid 失败: %s", exc)
        return {}


def inject_bilibili_buvid(ydl) -> None:
    """给 YoutubeDL 实例补 B 站匿名 buvid cookie（已有则不动）。"""
    jar = getattr(ydl, "cookiejar", None)
    if jar is None:
        return
    existing = {cookie.name for cookie in jar if "bilibili.com" in (cookie.domain or "")}
    if "buvid3" in existing:
        return
    for name, value in fetch_bilibili_buvid().items():
        if name in existing:
            continue
        jar.set_cookie(
            Cookie(
                0, name, value, None, False,
                ".bilibili.com", True, True, "/", True,
                False, None, False, None, None, {},
            )
        )


def is_bilibili_url(url: str) -> bool:
    return "bilibili.com" in url or "b23.tv" in url


def proxy_for_url(url: str) -> Optional[str]:
    """按站点分流代理：B 站等国内站点直连。"""
    if is_bilibili_url(url):
        return ""
    return system_proxy()


_ERROR_RULES = [
    (("sign in to confirm", "not a bot"), "YouTube 要求登录验证。请在浏览器中登录后重试。"),
    (("is only available for registered users",), "该视频需要登录后才能观看。"),
    (("http error 412",), "站点拒绝了请求（需要有效登录态）。"),
    (("premium", "membership", "大会员", "充电专属"), "该视频为会员或付费内容，当前账号没有观看权限。"),
    (("not available in your", "geo restriction", "geo-restricted"), "该视频在当前地区不可用。"),
    (("unsupported url",), "暂不支持该网站的链接。"),
    (("http error 404", "does not exist", "video unavailable"), "链接指向的内容不存在，请检查链接。"),
    (("http error 403",), "站点拒绝了下载请求，请稍后重试。"),
    (("unable to download webpage", "getaddrinfo", "timed out", "connection"), "网络连接失败，请检查网络后重试。"),
    (("ffmpeg is not installed", "ffmpeg not found", "postprocessing"), "合并音视频需要 FFmpeg，请先安装。"),
    (("no space left",), "磁盘空间不足，请清理后重试。"),
]


def strip_ansi(text: str) -> str:
    """去掉 yt-dlp 报错里的终端颜色码。"""
    return re.sub(r"\x1b\[[0-9;]*m", "", str(text)).strip()


def friendly_download_error(url: str, message: str) -> str:
    """把 yt-dlp 的报错翻译成简短、可行动的提示。"""
    message = strip_ansi(message)
    lowered = message.lower()
    if "ted.com" in url and "http error 403" in lowered:
        return "TED 拒绝了请求，请稍后重试或换一个公开链接。"
    if is_bilibili_url(url) and "http error 412" in lowered:
        return "哔哩哔哩风控拦截了请求，请稍等几分钟重试；如持续出现，可在浏览器登录后导出 cookies.txt。"
    for hints, friendly in _ERROR_RULES:
        if any(hint in lowered for hint in hints):
            return friendly
    first_line = message.splitlines()[0] if message else "下载失败"
    first_line = re.sub(r"^ERROR:\s*", "", first_line)
    return first_line[:120] or "下载失败"


# 浏览器登录态兜底阶梯
_COOKIE_ERROR_HINTS = (
    "http error 412", "sign in", "log in", "login", "cookie",
    "private video", "members only", "需要登录",
)

_BROWSER_PROFILES = {
    "chrome": (
        "~/Library/Application Support/Google/Chrome",
        "~/AppData/Local/Google/Chrome",
        "~/.config/google-chrome",
    ),
    "edge": (
        "~/Library/Application Support/Microsoft Edge",
        "~/AppData/Local/Microsoft/Edge",
        "~/.config/microsoft-edge",
    ),
    "brave": (
        "~/Library/Application Support/BraveSoftware/Brave-Browser",
        "~/AppData/Local/BraveSoftware/Brave-Browser",
        "~/.config/BraveSoftware/Brave-Browser",
    ),
    "firefox": (
        "~/Library/Application Support/Firefox/Profiles",
        "~/AppData/Roaming/Mozilla/Firefox/Profiles",
        "~/.mozilla/firefox",
    ),
    "safari": (
        "~/Library/Cookies/Cookies.binarycookies",
        "~/Library/Containers/com.apple.Safari",
    ),
}
_BROWSER_TITLES = {
    "chrome": "Chrome", "edge": "Edge", "brave": "Brave",
    "firefox": "Firefox", "safari": "Safari",
}

_last_good_browser: Optional[str] = None


def detect_cookie_browsers() -> list[str]:
    """探测本机已安装、可读取登录态的浏览器。"""
    found = []
    for browser, candidates in _BROWSER_PROFILES.items():
        if any(Path(path).expanduser().exists() for path in candidates):
            found.append(browser)
    if _last_good_browser in found:
        found.remove(_last_good_browser)
        found.insert(0, _last_good_browser)
    return found


def looks_like_cookie_error(message: str) -> bool:
    lowered = message.lower()
    return any(hint in lowered for hint in _COOKIE_ERROR_HINTS)


_COOKIE_READ_FAILURE_HINTS = (
    "operation not permitted", "permission denied", "could not copy",
    "could not find", "failed to decrypt", "database is locked",
)


def run_with_browser_cookie_fallback(
    url: str,
    attempt: Callable[[Optional[str]], T],
    *,
    on_attempt: Optional[Callable[[str], None]] = None,
    cancel_check: Optional[Callable[[], None]] = None,
) -> tuple[T, Optional[str]]:
    """先匿名（或 cookies.txt）执行，登录态错误时依次换浏览器登录态重试。"""
    try:
        return attempt(None), None
    except Exception as original:
        if cancel_check:
            cancel_check()
        original_message = strip_ansi(str(original))
        browsers = detect_cookie_browsers()
        if not looks_like_cookie_error(original_message) or not browsers:
            raise RuntimeError(friendly_download_error(url, original_message)) from original

        global _last_good_browser
        had_cookies_file = cookies_file().exists()
        rejected: list[str] = []
        unreadable: list[str] = []
        for browser in browsers:
            title = _BROWSER_TITLES[browser]
            logger.info("需登录态，尝试 %s 浏览器 cookies: %s", title, url)
            if on_attempt:
                on_attempt(title)
            try:
                result = attempt(browser)
                _last_good_browser = browser
                return result, title
            except Exception as exc:
                if cancel_check:
                    cancel_check()
                message = strip_ansi(str(exc))
                logger.warning("%s 登录态重试失败: %s", title, message)
                if any(h in message.lower() for h in _COOKIE_READ_FAILURE_HINTS):
                    unreadable.append(title)
                else:
                    rejected.append(title)

        parts = [friendly_download_error(url, original_message)]
        if rejected:
            parts.append(
                f"已尝试 {'、'.join(rejected)} 浏览器登录态，仍被拒绝，"
                "请先在浏览器中登录该网站。"
            )
        if unreadable:
            parts.append(
                f"{'、'.join(unreadable)} 的登录态因系统隐私保护无法读取"
                "（可在 系统设置 → 隐私与安全性 → 完全磁盘访问权限 中允许后重试）。"
            )
        if had_cookies_file:
            parts.append("另外检测到 cookies.txt 已失效，建议删除后重新导出。")
        logger.warning("浏览器登录态全部失败，cookies.txt=%s", cookies_file())
        raise RuntimeError(" ".join(parts)) from original

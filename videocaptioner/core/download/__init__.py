"""视频/模型下载模块"""

from .downloader import DownloadCancelled, DownloadError, download_file
from .media import MediaDownloader, media_summary, probe_summary, sanitize_filename
from .models import (
    ModelFile,
    ModelSpec,
    download_model,
    find_model,
    has_partial_download,
    iter_models,
    model_install_state,
)
from .net import (
    cookies_file,
    friendly_download_error,
    inject_bilibili_buvid,
    is_bilibili_url,
    proxy_for_url,
    run_with_browser_cookie_fallback,
    strip_ansi,
    system_proxy,
)
from .programs import (
    detect_program,
    program_install_plan,
    program_variants,
)
from .source_check import (
    DOWNLOAD_SOURCES,
    check_download_source,
    check_download_sources,
)

__all__ = [
    "DownloadCancelled",
    "DownloadError",
    "DOWNLOAD_SOURCES",
    "MediaDownloader",
    "ModelFile",
    "ModelSpec",
    "check_download_source",
    "check_download_sources",
    "cookies_file",
    "detect_program",
    "download_file",
    "download_model",
    "find_model",
    "friendly_download_error",
    "has_partial_download",
    "inject_bilibili_buvid",
    "is_bilibili_url",
    "iter_models",
    "media_summary",
    "model_install_state",
    "probe_summary",
    "program_install_plan",
    "program_variants",
    "proxy_for_url",
    "run_with_browser_cookie_fallback",
    "sanitize_filename",
    "strip_ansi",
    "system_proxy",
]

"""通用 Worker 线程基类，简化 QThread 的创建和取消处理。"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class WorkerCancelled(Exception):
    """在工作线程中抛出以表示任务被取消。"""
    pass


class WorkerThread(QThread):
    """可取消的通用 Worker 基类。

    子类只需实现 _work()，并通过 checkpoint() 在长操作中定期检查取消状态。
    """

    progress = pyqtSignal(int, str)  # 进度百分比, 状态描述
    error = pyqtSignal(str)

    def __init__(self, parent: Optional[object] = None):
        super().__init__(parent)
        self._cancel_requested = False

    # ── 子类实现 ──────────────────────────────────────────────────────────

    def _work(self) -> None:
        """子类在此实现实际工作逻辑。正常返回表示成功。"""
        raise NotImplementedError

    def _on_cancel(self) -> None:
        """取消钩子：子类可在此终止正在运行的子进程/执行器等。"""
        pass

    # ── 取消机制 ──────────────────────────────────────────────────────────

    def is_cancel_requested(self) -> bool:
        return self._cancel_requested

    def checkpoint(self) -> None:
        """在长操作中定期调用；如果已请求取消则抛出 WorkerCancelled。"""
        if self._cancel_requested:
            raise WorkerCancelled()

    def request_cancel(self) -> None:
        """请求取消（非阻塞）。"""
        self._cancel_requested = True
        self._on_cancel()

    def stop(self, wait_ms: int = 3000) -> None:
        """请求取消并等待线程结束；超时则强制 terminate。"""
        self.request_cancel()
        if not self.wait(wait_ms):
            logger.warning("Worker %s did not finish within %d ms, terminating", self, wait_ms)
            self.terminate()
            self.wait(500)

    # ── 运行循环 ──────────────────────────────────────────────────────────

    def run(self) -> None:
        try:
            self._work()
        except WorkerCancelled:
            logger.info("Worker %s cancelled", self)
        except Exception as exc:
            logger.exception("Worker %s failed", self)
            self.error.emit(str(exc))

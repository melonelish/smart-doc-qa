"""
WebSocket progress tracker — pushes real-time document processing status.
"""

import asyncio
import json
import threading
import time
from typing import Optional

from fastapi import WebSocket

_TTL_SECONDS = 60


class ProgressTracker:
    """Singleton per-document progress broadcaster."""

    def __init__(self):
        self._state: dict[str, dict] = {}
        self._subscribers: dict[str, list[WebSocket]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_lock = threading.Lock()

    def _get_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        if self._loop and not self._loop.is_closed():
            return self._loop
        with self._loop_lock:
            if self._loop and not self._loop.is_closed():
                return self._loop
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # Never call get_event_loop() from a background thread —
                # it may create a new idle loop that isn't the server's loop.
                self._loop = None
            return self._loop

    def _schedule_send(self, ws: WebSocket, msg: str):
        loop = self._get_loop()
        if loop is None or not loop.is_running():
            # State is already saved; subscriber will receive it on connect.
            return
        try:
            # Use thread-safe method to schedule coroutine on the event loop.
            # loop.create_task() must be called from the loop's own thread;
            # from a background thread (e.g. BackgroundTasks) it raises RuntimeError.
            asyncio.run_coroutine_threadsafe(self._safe_send(ws, msg), loop)
        except Exception:
            pass

    def set(self, doc_id: str, stage: str, percent: int):
        self._state[doc_id] = {"stage": stage, "percent": percent, "ts": time.time()}
        msg = json.dumps({
            "type": "progress",
            "doc_id": doc_id,
            "stage": stage,
            "percent": percent,
        }, ensure_ascii=False)

        for ws in list(self._subscribers.get(doc_id, [])):
            self._schedule_send(ws, msg)

        if percent >= 100 or percent <= 0:
            loop = self._get_loop()
            if loop and loop.is_running():
                loop.call_later(_TTL_SECONDS, self._cleanup_if_stale, doc_id, percent)

    def _cleanup_if_stale(self, doc_id: str, expected_percent: int):
        st = self._state.get(doc_id)
        if st and st["percent"] == expected_percent:
            self.clear(doc_id)

    def get(self, doc_id: str) -> Optional[dict]:
        return self._state.get(doc_id)

    def clear(self, doc_id: str):
        self._state.pop(doc_id, None)
        self._subscribers.pop(doc_id, None)

    async def subscribe(self, doc_id: str, ws: WebSocket):
        with self._loop_lock:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

        if doc_id not in self._subscribers:
            self._subscribers[doc_id] = []
        self._subscribers[doc_id].append(ws)

        if doc_id in self._state:
            st = self._state[doc_id]
            msg = json.dumps({
                "type": "progress",
                "doc_id": doc_id,
                "stage": st["stage"],
                "percent": st["percent"],
            }, ensure_ascii=False)
            try:
                await ws.send_text(msg)
            except Exception:
                pass

    async def unsubscribe(self, doc_id: str, ws: WebSocket):
        if doc_id in self._subscribers:
            self._subscribers[doc_id] = [
                w for w in self._subscribers[doc_id] if w is not ws
            ]

    @staticmethod
    async def _safe_send(ws: WebSocket, data: str):
        try:
            await ws.send_text(data)
        except Exception:
            pass


progress_tracker = ProgressTracker()

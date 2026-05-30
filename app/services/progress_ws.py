"""
WebSocket progress tracker — pushes real-time document processing status.

Usage:
    from app.services.progress_ws import set_progress, register_ws, unregister_ws

    # In your processing pipeline:
    set_progress(doc_id, "加载文档...", 10)
    set_progress(doc_id, "文本分割...", 40)
    set_progress(doc_id, "向量化...", 70)
    set_progress(doc_id, "完成", 100)
"""

import asyncio
import json
from typing import Optional

from fastapi import WebSocket


class ProgressTracker:
    """Singleton per-document progress broadcaster."""

    def __init__(self):
        self._state: dict[str, dict] = {}  # doc_id → {stage, percent}
        self._subscribers: dict[str, list[WebSocket]] = {}  # doc_id → [ws, ...]

    def set(self, doc_id: str, stage: str, percent: int):
        """Update progress and broadcast to all subscribers."""
        self._state[doc_id] = {"stage": stage, "percent": percent}
        msg = json.dumps({
            "type": "progress",
            "doc_id": doc_id,
            "stage": stage,
            "percent": percent,
        }, ensure_ascii=False)

        for ws in self._subscribers.get(doc_id, []):
            try:
                asyncio.get_event_loop().create_task(self._safe_send(ws, msg))
            except RuntimeError:
                pass

    def get(self, doc_id: str) -> Optional[dict]:
        return self._state.get(doc_id)

    def clear(self, doc_id: str):
        self._state.pop(doc_id, None)
        self._subscribers.pop(doc_id, None)

    async def subscribe(self, doc_id: str, ws: WebSocket):
        """Register a WebSocket for progress updates."""
        if doc_id not in self._subscribers:
            self._subscribers[doc_id] = []
        self._subscribers[doc_id].append(ws)

        # Send current state immediately
        if doc_id in self._state:
            msg = json.dumps({
                "type": "progress",
                "doc_id": doc_id,
                "stage": self._state[doc_id]["stage"],
                "percent": self._state[doc_id]["percent"],
            }, ensure_ascii=False)
            await ws.send_text(msg)

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


# Module-level singleton
progress_tracker = ProgressTracker()
"""
Conversation Store — Redis-backed with in-memory fallback
===========================================================
Persists multi-turn conversation history across server restarts.
Uses Redis Hash + TTL when available; falls back to in-memory dict
when Redis is not configured / unreachable.
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    role: str  # "user" | "assistant"
    content: str
    sources: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


# ── Serialisation helpers ──────────────────────────────────

_TURN_KEYS = {"role", "content", "sources", "timestamp"}


def _turn_to_dict(t: ConversationTurn) -> dict:
    return asdict(t)


def _dict_to_turn(d: dict) -> ConversationTurn:
    return ConversationTurn(
        role=d.get("role", "unknown"),
        content=d.get("content", ""),
        sources=d.get("sources", []),
        timestamp=d.get("timestamp", time.time()),
    )


# ── Redis client (lazy) ────────────────────────────────────

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        from app.core.config import get_settings
        settings = get_settings()
        import redis as _redis
        _redis_client = _redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=1,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        _redis_client.ping()
        logger.info("Conversation store: using Redis (%s:%s)",
                     settings.redis_host, settings.redis_port)
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable, falling back to in-memory: %s", exc)
        _redis_client = None  # sentinel
        return None


# ── TTL ────────────────────────────────────────────────────

def _ttl() -> int:
    try:
        from app.core.config import get_settings
        return get_settings().conversation_ttl_seconds
    except Exception:
        return 3600


# ═══════════════════════════════════════════════════════════
#  Conversation Store
# ═══════════════════════════════════════════════════════════


class ConversationStore:
    """
    Persistent conversation store.

    Strategy (first-wins):
        1. Redis Hash (with global TTL per conversation)
        2. In-memory dict (same as old ConversationMemory)
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._memory: Dict[str, List[ConversationTurn]] = {}  # fallback
        self._redis: Optional["redis.Redis"] = _get_redis()

    # ── Redis helpers ──────────────────────────────────────

    def _redis_key(self, conv_id: str) -> str:
        return f"conv:{conv_id}"

    def _redis_write(self, conv_id: str, turns: List[ConversationTurn]) -> None:
        if self._redis is None:
            return
        try:
            pipe = self._redis.pipeline()
            key = self._redis_key(conv_id)
            pipe.delete(key)
            for i, t in enumerate(turns):
                pipe.hset(key, str(i), json.dumps(_turn_to_dict(t),
                                                   ensure_ascii=False))
            pipe.expire(key, self._ttl)
            pipe.execute()
        except Exception as exc:
            logger.warning("Redis write failed for conv %s: %s", conv_id, exc)

    def _redis_read(self, conv_id: str) -> Optional[List[ConversationTurn]]:
        if self._redis is None:
            return None
        try:
            key = self._redis_key(conv_id)
            raw = self._redis.hgetall(key)
            if not raw:
                return None
            pairs = sorted(raw.items(), key=lambda x: int(x[0]))
            turns = []
            for _, val in pairs:
                d = json.loads(val)
                turns.append(_dict_to_turn(d))
            # Refresh TTL
            self._redis.expire(key, self._ttl)
            return turns
        except Exception as exc:
            logger.warning("Redis read failed for conv %s: %s", conv_id, exc)
            return None

    def _redis_delete(self, conv_id: str) -> None:
        if self._redis is None:
            return
        try:
            self._redis.delete(self._redis_key(conv_id))
        except Exception:
            pass

    # ── Public API ─────────────────────────────────────────

    def get_history(
        self, conversation_id: str, max_turns: int = 6
    ) -> List[ConversationTurn]:
        now = time.time()
        # Try Redis first
        if self._redis is not None:
            turns = self._redis_read(conversation_id)
            if turns is not None:
                # Evict expired
                turns = [t for t in turns if now - t.timestamp < self._ttl]
                return turns[-max_turns:]
        # Fallback to memory
        return self._memory.get(conversation_id, [])[-max_turns:]

    def add_turn(self, conversation_id: str, turn: ConversationTurn) -> None:
        # Always keep in-memory fallback in sync
        if conversation_id not in self._memory:
            self._memory[conversation_id] = []
        self._memory[conversation_id].append(turn)

        # Write-through to Redis
        if self._redis is not None:
            self._redis_write(conversation_id, self._memory[conversation_id])

    def clear(self, conversation_id: str) -> None:
        self._memory.pop(conversation_id, None)
        self._redis_delete(conversation_id)

    @property
    def store_type(self) -> str:
        return "redis" if self._redis is not None else "memory"

    def cleanup_expired(self) -> int:
        """Remove expired in-memory conversations (Redis handles its own TTL)."""
        now = time.time()
        expired = []
        for cid, turns in self._memory.items():
            self._memory[cid] = [t for t in turns if now - t.timestamp < self._ttl]
            if not self._memory[cid]:
                expired.append(cid)
        for cid in expired:
            del self._memory[cid]
        return len(expired)


# Module-level singleton (replace old conversation_memory)
conversation_store = ConversationStore()

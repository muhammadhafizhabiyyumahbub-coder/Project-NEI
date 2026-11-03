"""SSE route: live task status via Server-Sent Events."""
import json
import asyncio
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

# In-memory event bus: task_id -> list of subscribers (asyncio.Queue)
_subscribers: dict[str, list[asyncio.Queue]] = {}


def publish_event(task_id: str, event: str, data: dict) -> None:
    """Publish to all SSE subscribers for this task."""
    for q in _subscribers.get(task_id, []):
        q.put_nowait({"event": event, "data": data})


def subscribe(task_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(task_id, []).append(q)
    return q


def unsubscribe(task_id: str, q: asyncio.Queue) -> None:
    """Remove subscriber; no-op if already gone."""
    subs = _subscribers.get(task_id)
    if subs and q in subs:
        subs.remove(q)


@router.get("/tasks/{task_id}/events")
async def task_events(task_id: str):
    q = subscribe(task_id)

    async def generator():
        try:
            # Initial snapshot
            from nei.core.task_manager import get_task
            task = await get_task(task_id)
            if task:
                yield {"event": "snapshot", "data": json.dumps(task)}
            while True:
                item = await q.get()
                yield {"event": item["event"], "data": json.dumps(item["data"])}
        finally:
            unsubscribe(task_id, q)

    return EventSourceResponse(generator())

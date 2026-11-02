"""SSE routes for task status updates."""
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio

router = APIRouter()


@router.get("/tasks/{task_id}/events")
async def task_events(task_id: str):
    async def event_generator():
        while True:
            # Placeholder: In real app, poll DB or use task queue/pubsub
            yield {"data": "status update"}
            await asyncio.sleep(5)
    return EventSourceResponse(event_generator())

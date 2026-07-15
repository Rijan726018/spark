"""WebSocket connection manager and endpoints."""
import asyncio
import json
import logging
import os
from typing import Set

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("nexus.ws")

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("WS client connected. Total: %d", len(self._connections))

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.discard(ws)
        logger.info("WS client disconnected. Total: %d", len(self._connections))

    async def broadcast(self, data: dict):
        if not self._connections:
            return
        msg = json.dumps(data)
        dead: Set[WebSocket] = set()
        async with self._lock:
            conns = set(self._connections)
        for ws in conns:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.add(ws)
        if dead:
            async with self._lock:
                self._connections -= dead


ws_manager = ConnectionManager()


@router.websocket("/ws/market")
async def ws_market(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_text(json.dumps({"type": "status", "connected": True}))
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                data = json.loads(msg)
                if data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif data.get("type") == "subscribe":
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "symbol": data.get("symbol", "ES"),
                    }))
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WS error: %s", exc)
    finally:
        await ws_manager.disconnect(websocket)


@router.websocket("/ws/trades")
async def ws_trades(websocket: WebSocket):
    await websocket.accept()
    r = aioredis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )
    pubsub = r.pubsub()
    await pubsub.subscribe("pamm_updates")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
            if message:
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe("pamm_updates")


@router.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket):
    await websocket.accept()
    r = aioredis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )
    pubsub = r.pubsub()
    await pubsub.subscribe("live_prices")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
            if message:
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        await pubsub.unsubscribe("live_prices")

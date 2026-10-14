"""
تست‌های خودکار وب‌سرور سلامت‌سنجی Render و UptimeRobot
"""

import pytest
from aiohttp.test_utils import TestClient, TestServer

from bot import __version__
from bot.web.health import create_health_app


@pytest.mark.asyncio
async def test_root_endpoint(test_db):
    app = create_health_app()
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()

    try:
        resp = await client.get("/")
        assert resp.status == 200
        text = await resp.text()
        assert "NoorBot" in text
        assert f"v{__version__}" in text
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_health_endpoint(test_db):
    app = create_health_app()
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()

    try:
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "NoorBot"
        assert "database" in data
        assert data["database"]["connected"] is True
        assert "uptime_seconds" in data
    finally:
        await client.close()

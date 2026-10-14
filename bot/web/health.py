"""
سرور وب سبک HTTP جهت بررسی سلامت (Health Check) برای Render و UptimeRobot
"""

import logging
import os
import time
from aiohttp import web

from bot import __version__
from bot.config import settings
from bot.db.base import db

logger = logging.getLogger("web.health")

START_TIME = time.time()


async def handle_root(request: web.Request) -> web.Response:
    uptime_sec = int(time.time() - START_TIME)
    return web.Response(
        text=(
            f"🌟 NoorBot Religious Suite & Istikhara Bot v{__version__} is active.\n"
            f"Uptime: {uptime_sec} seconds.\n"
            f"Health status: /health"
        ),
        content_type="text/plain"
    )


async def handle_health(request: web.Request) -> web.Response:
    """
    بررسی سلامت واقعی و زنده سامانه شامل پایگاه داده و زمان فعالیت
    سازگار با الزامات مانیتورینگ UptimeRobot و Render Health Checks
    """
    db_health = await db.health_check()
    uptime_sec = int(time.time() - START_TIME)

    is_healthy = db_health.get("connected", False)
    status_code = 200 if is_healthy else 503

    payload = {
        "status": "healthy" if is_healthy else "degraded",
        "service": "NoorBot",
        "version": __version__,
        "uptime_seconds": uptime_sec,
        "database": db_health,
        "environment": settings.environment,
        "port": settings.port
    }
    return web.json_response(payload, status=status_code)


def create_health_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    return app


async def start_health_server(host: str, port: int) -> web.AppRunner:
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    logger.info("Health server listening on http://%s:%s/health", host, port)
    return runner

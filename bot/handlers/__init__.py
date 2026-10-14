from aiogram import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.ahkam import router as ahkam_router
from bot.handlers.group import router as group_router
from bot.handlers.istikhara import router as istikhara_router
from bot.handlers.prayer import router as prayer_router
from bot.handlers.quran import router as quran_router
from bot.handlers.religious import router as religious_router
from bot.handlers.start import router as start_router
from bot.handlers.tasbih import router as tasbih_router


def get_main_router() -> Router:
    main_router = Router(name="main_router")
    main_router.include_router(admin_router)
    main_router.include_router(group_router)
    main_router.include_router(start_router)
    main_router.include_router(istikhara_router)
    main_router.include_router(quran_router)
    main_router.include_router(tasbih_router)
    main_router.include_router(prayer_router)
    main_router.include_router(religious_router)
    main_router.include_router(ahkam_router)
    return main_router


__all__ = ["get_main_router"]

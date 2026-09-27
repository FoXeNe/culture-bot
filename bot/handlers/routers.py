from maxapi import Router

from bot.handlers.admin import router as admin_router
from bot.handlers.start import router as start_router
from bot.handlers.register import router as register_router
from bot.handlers.challenge import router as challenge_router
from bot.handlers.menu import router as menu_router

routers: list[Router] = [admin_router, start_router, register_router, challenge_router, menu_router]

from maxapi import Router

from bot.handlers.start import router as start_router
from bot.handlers.register import router as register_router

routers: list[Router] = [start_router, register_router]

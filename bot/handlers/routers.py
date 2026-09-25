from maxapi import Router

from bot.handlers.start import router as start_router

routers: list[Router] = [start_router]

"""
    Модуль диспетчера-исполнителя всех страниц. Регулирует кол-во браузеров, 
    и количество потоков для наиболее эффективного парсинга.
"""

import asyncio

from typing import List

from pyppeteer import launch

from .gui import AbstractGUIParser
from .router import SiteRouter


class Dispatcher:
    def __init__(self) -> None:
        self.spa_routers: List[SiteRouter] = []
        self.mpa_routers: List[SiteRouter] = []

    def include_router(self, router: SiteRouter):
        if router.is_spa:
            self.spa_routers.append(router)
        else:
            self.mpa_routers.append(router)

    async def start(self):
        if len(self.spa_routers) != 0:
            browser = await launch(headless=False)

        await asyncio.gather(
            *[router.executor(browser=browser) for router in self.spa_routers],
            *[router.executor() for router in self.mpa_routers],
        )

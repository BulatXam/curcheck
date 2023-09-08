"""
    Модуль диспетчера-исполнителя всех страниц. Регулирует кол-во браузеров, 
    и количество потоков для наиболее эффективного парсинга.
"""

import asyncio

from typing import List

from pyppeteer import launch

from .router import AbstractRouter


class Dispatcher:
    """ 
    Диспетчер роутеров. В зависимости от нагрузки, диспетчер будет принимать
    решения какая страницы работает на каком браузере в определенное кол-во потоков.  
    """
    def __init__(self) -> None:
        self.spa_routers: List[AbstractRouter] = []
        self.mpa_routers: List[AbstractRouter] = []

    def include_router(self, router: AbstractRouter):
        if router.is_spa:
            self.spa_routers.append(router)
        else:
            self.mpa_routers.append(router)

    async def start(
        self, options: dict = None, **kwargs
    ):
        if len(self.spa_routers) != 0:
            browser = await launch(
                options=options, **kwargs
            )

        await asyncio.gather(
            *[router.executor(browser=browser) for router in self.spa_routers],
            *[router.executor() for router in self.mpa_routers],
        )

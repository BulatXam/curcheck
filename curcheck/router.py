"""
    Модуль роутеров-сборников команд, вызывающих нужные события-декораторы.

    Каждый роутер-это отдельный сайт. Регулирует кол-во страниц и тд в каждом
    отдельном сайте для наиболее эффективного парсинга.
"""

import asyncio

from typing import List
from aiohttp import ClientSession

from pyppeteer import launch
from pyppeteer.browser import Browser

from .errors import SiteConfigurationError
from .events import EventPage, EventPaginator, EventLongpoll


class SiteRouter:
    def __init__(
        self, domain: str, is_spa: bool = False
    ) -> None:
        self.domain = domain
        self.is_spa = is_spa

        self.browser: Browser = None

        self.pages: List[EventPage] = []
        self.paginators: List[EventPaginator] = []
        self.longpolls: List[EventLongpoll] = []


    def paginate_page(
        self, url: str, pages_links_xpath: str, count_in_approach: int = 10
    ) -> EventPaginator:
        paginator = EventPaginator(
            domain=self.domain, 
            url=url,
            pages_links_xpath=pages_links_xpath, 
            count_in_approach=count_in_approach,
            is_browser=self.is_spa
        )
        self.paginators.append(paginator)

        return paginator

    def page(self, url: str) -> EventPage:
        page = EventPage(
            domain=self.domain, 
            url=url,
            is_browser=self.is_spa
        )
        self.pages.append(page)

        return page

    def longpoll(
        self, url: str, timeout: int = 60, count: int|None = None
    ) -> EventLongpoll:
        longpoll = EventLongpoll(
            domain=self.domain,
            url=url,
            timeout=timeout,
            count=count,
            is_browser=self.is_spa
        )
        self.longpolls.append(longpoll)

        return longpoll

    async def executor(self, browser: Browser|None = None) -> None:
        if self.is_spa:
            if not browser:
                browser = await launch(headless=True)

            await asyncio.gather(
                *[page.task(browser) for page in self.pages]
            )

            await asyncio.gather(
                *[paginator.task(browser) for paginator in self.paginators]
            )

            await asyncio.gather(
                *[longpoll.task(browser) for longpoll in self.longpolls]
            )
        else:
            async with ClientSession() as session:
                await asyncio.gather(
                    *[page.task(session) for page in self.pages]
                )

                await asyncio.gather(
                    *[paginator.task(session) for paginator in self.paginators]
                )

                await asyncio.gather(
                    *[longpoll.task(session) for longpoll in self.longpolls]
                )

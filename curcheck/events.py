"""
    Модуль, в котором находятся все события, которые можно вызвать откуда угодно
"""

import functools
import asyncio

from aiohttp import ClientSession
from lxml import html

from typing import List, Awaitable

from pyppeteer.browser import Browser

from .errors import ConfigurationError


class AbstractEvent:
    task: Awaitable|None = None

    def __init__(
        self, 
        domain: str, 
        url: str, 
        is_browser: bool = False, 
        cookies: dict|None = None
    ):
        self.domain = domain
        self.url = url
        self.is_browser = is_browser
        self.cookies = cookies

        if "http://" in self.url and "." in self.url:
            self.link: str = self.url
        elif "//" in self.url and not "http:" in self.url:
            self.link: str = "http:" + self.url
        else:
            self.link: str = self.domain + self.url
    
    async def _get_page(self, browser: Browser):
        page = await browser.newPage()
        page.setDefaultNavigationTimeout(0)
        if self.cookies:
            await page.setCookie(*self.cookies)
        await page.goto(url=self.link)


class EventPage(AbstractEvent):
    def __init__(
        self, 
        domain: str, 
        url: str, 
        is_browser: bool = False, 
        cookies: dict|None = None
    ):
        super().__init__(
            domain=domain, url=url, is_browser=is_browser, cookies=cookies
        )

    def __call__(self, func: Awaitable):
        @functools.wraps(func) 
        async def spa_task(browser: Browser, *args, **kwargs):
            page = await browser.newPage()
            page.setDefaultNavigationTimeout(0)
            if self.cookies:
                await page.setCookie(*self.cookies)
            await page.goto(url=self.link)
            await func(page, *args, **kwargs)
            await page.close()

        @functools.wraps(func) 
        async def mpa_task(session: ClientSession, *args, **kwargs):
            response = await session.request("GET", self.link)
            tree = html.fromstring(await response.text())

            await func(tree, *args, **kwargs)

        if self.is_browser:
            self.task = spa_task
        else:
            self.task = mpa_task

        return self.task


class EventPaginator(AbstractEvent):
    def __init__(
        self, 
        domain: str|None = None, 
        url: str|None = None, 
        pages_links_xpath: str|None = None,
        count_in_approach: int = 10,
        is_browser: bool = False,
        auxiliary_function: Awaitable|None = None,
        paginate_urls: list|None = None,
        cookies: dict|None = None
    ) -> None:
        super().__init__(
            domain=domain, url=url, is_browser=is_browser, cookies=cookies
        )

        if domain and url:
            self.pages_links_xpath = pages_links_xpath
            self.count_in_approach = count_in_approach
            self.auxiliary_function = auxiliary_function
        elif paginate_urls:
            self.paginate_urls = paginate_urls
        else:
            raise ConfigurationError(
                "Ошибка! Нельзя одновременно парсить пагинатор страницы и "\
                "отправлять свои ссылки для пагинации!"
            )


        self.pages: List[EventPage] = []

    def __call__(self, func: Awaitable):
        @functools.wraps(func) 
        async def spa_task(browser: Browser, *args, **kwargs):
            if not self.paginate_urls:
                base_page = await browser.newPage()
                base_page.setDefaultNavigationTimeout(0)
                if self.cookies:
                    await base_page.setCookie(*self.cookies)
                await base_page.goto(url=self.domain+self.url)

                if self.auxiliary_function:
                    await self.auxiliary_function(base_page)
                
                if self.pages_links_xpath.split("/")[-1][0] == "@":
                    html_attr = f'.getAttribute("{self.pages_links_xpath.split("/")[-1][1:]}")'
                elif self.pages_links_xpath.split("/")[-1] == "text()":
                    html_attr = ".innerText"
                else:
                    html_attr = ".innerHTML"

                xpath = "/".join(self.pages_links_xpath.split("/")[:-1])

                pages_links = await base_page.xpath(xpath)

                self.pages = [
                    EventPage(
                        domain=self.domain, 
                        url=await base_page.evaluate(
                            f"(link) => link{html_attr}", link
                        ),
                        is_browser=True,
                        cookies=self.cookies
                    )(func) for link in pages_links
                ]
            else:
                self.pages = [
                    EventPage(
                        domain=self.domain, url=url, is_browser=True
                    )(func) for url in self.paginate_urls
                ]

            approach_len = (
                len(self.pages) // self.count_in_approach 
                if len(self.pages) % self.count_in_approach == 0 
                else (len(self.pages) // self.count_in_approach)+1
            ) # кол-во подходов

            for i in range(approach_len):
                if i < approach_len - 1:
                    await asyncio.gather(
                        *[page_task(browser, *args, **kwargs) for page_task in self.pages[i: (i+1)*self.count_in_approach]]
                    )
                else:
                    await asyncio.gather(
                        *[page_task(browser, *args, **kwargs) for page_task in self.pages[i: len(self.pages)-i*self.count_in_approach]]
                    )

        @functools.wraps(func) 
        async def mpa_task(session: ClientSession, *args, **kwargs):
            response = await session.request("GET", self.link)

            base_tree = html.fromstring(await response.text())

            if self.auxiliary_function:
                await self.auxiliary_function(base_tree)

            pages_links_elements = base_tree.xpath(self.pages_links_xpath)

            self.pages = [
                EventPage(
                    domain=self.domain, 
                    url=link,
                    is_browser=False
                )(func) for link in pages_links_elements
            ]

            approach_len = (
                len(self.pages) // self.count_in_approach 
                if len(self.pages) % self.count_in_approach == 0 
                else (len(self.pages) // self.count_in_approach)+1
            ) # кол-во подходов

            for i in range(approach_len):
                if i < approach_len - 1:
                    await asyncio.gather(
                        *[page_task(session, *args, **kwargs) for page_task in self.pages[i: (i+1)*self.count_in_approach]]
                    )
                else:
                    await asyncio.gather(
                        *[page_task(session, *args, **kwargs) for page_task in self.pages[i: len(self.pages)-i*self.count_in_approach]]
                    )

        if self.is_browser:
            self.task = spa_task
        else:
            self.task = mpa_task

        return self.task


class EventLongpoll(AbstractEvent):
    def __init__(
        self, 
        domain: str, 
        url: str, 
        timeout: int = 60, 
        count: int = None,
        is_browser: bool = False,
        cookies: dict|None = None,
    ) -> None:
        super().__init__(domain=domain, url=url, is_browser=is_browser, cookies=cookies)

        self.count = count
        self.timeout = timeout
        self.i = 0

    def __call__(self, func: Awaitable):
        @functools.wraps(func)
        async def spa_task(browser: Browser, *args, **kwargs):
            self.browser = browser
            page = await self.browser.newPage()
            if self.cookies:
                await page.setCookie(*self.cookies)
            page.setDefaultNavigationTimeout(0)
            await self.page.goto(self.link)
            while self.i <= self.count or self.count == None:
                self.i += 1
                await func(page, *args, **kwargs)
                await page.reload()
                await asyncio.sleep(self.timeout)

        @functools.wraps(func) 
        async def mpa_task(session: ClientSession, *args, **kwargs):
            while self.i <= self.count or self.count == None:
                response = await session.request("GET", self.link)
                
                tree = html.fromstring(await response.text())
                await func(tree, *args, **kwargs)

                await asyncio.sleep(self.timeout)
                self.i += 1

        if self.is_browser:
            self.task = spa_task
        else:
            self.task = mpa_task

        return self.task

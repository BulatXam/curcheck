"""
    Модуль, в котором находятся все события, которые можно вызвать откуда угодно
"""

import functools
import asyncio

from aiohttp import ClientSession
from lxml import html

from typing import Any, List, Awaitable

from pyppeteer.browser import Browser


class AbstractEvent:
    task: Awaitable|None = None

    def __init__(self, domain: str, url: str, is_browser: bool = False):
        self.domain = domain
        self.url = url
        self.is_browser = is_browser

        if "http://" in self.url and "." in self.url:
            self.link: str = self.url
        elif "//" in self.url and not "http:" in self.url:
            self.link: str = "http:" + self.url
        else:
            self.link: str = self.domain + self.url


class EventPage(AbstractEvent):
    def __init__(self, domain: str, url: str, is_browser: bool = False):
        super().__init__(domain=domain, url=url, is_browser=is_browser)

    def __call__(self, func):
        @functools.wraps(func) 
        async def spa_task(browser: Browser):
            page = await browser.newPage()
            await page.goto(url=self.link)
            await func(page)
            await page.close()

        @functools.wraps(func) 
        async def mpa_task(session: ClientSession):
            response = await session.request("GET", self.link)
            tree = html.fromstring(await response.text())

            await func(tree)

        if self.is_browser:
            self.task = spa_task
        else:
            self.task = mpa_task

        return self.task


class EventPaginator(AbstractEvent):
    def __init__(
        self, 
        domain: str, 
        url: str, 
        pages_links_xpath: str, 
        count_in_approach: int = 10,
        is_browser: bool = False
    ) -> None:
        super().__init__(domain=domain, url=url, is_browser=is_browser)

        self.pages_links_xpath = pages_links_xpath
        self.count_in_approach = count_in_approach

        self.pages: List[EventPage] = []

    def __call__(self, func):
        @functools.wraps(func) 
        async def spa_task(browser: Browser):
            base_page = await browser.newPage()
            await base_page.goto(url=self.domain+self.url)
            
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
                    is_browser=True
                )(func) for link in pages_links
            ]

            approach_len = (
                len(self.pages) // self.count_in_approach 
                if len(self.pages) % self.count_in_approach == 0 
                else (len(self.pages) // self.count_in_approach)+1
            ) # кол-во подходов

            for i in range(approach_len):
                if i < approach_len - 1:
                    await asyncio.gather(
                        *[page_task(browser) for page_task in self.pages[i: (i+1)*self.count_in_approach]]
                    )
                else:
                    await asyncio.gather(
                        *[page_task(browser) for page_task in self.pages[i: len(self.pages)-i*self.count_in_approach]]
                    )

        @functools.wraps(func) 
        async def mpa_task(session: ClientSession):
            response = await session.request("GET", self.link)

            base_tree = html.fromstring(await response.text())
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
                        *[page_task(session) for page_task in self.pages[i: (i+1)*self.count_in_approach]]
                    )
                else:
                    await asyncio.gather(
                        *[page_task(session) for page_task in self.pages[i: len(self.pages)-i*self.count_in_approach]]
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
        is_browser: bool = False
    ) -> None:
        super().__init__(domain=domain, url=url, is_browser=is_browser)

        self.count = count
        self.timeout = timeout
        self.i = 0

    def __call__(self, func) -> Any:
        @functools.wraps(func)
        async def spa_task(browser: Browser):
            self.browser = browser
            page = await self.browser.newPage()
            await self.page.goto(self.link)
            while self.i <= self.count or self.count == None:
                self.i += 1
                await func(page)
                await page.reload()
                await asyncio.sleep(self.timeout)

        @functools.wraps(func) 
        async def mpa_task(session: ClientSession):
            while self.i <= self.count or self.count == None:
                response = await session.request("GET", self.link)
                
                tree = html.fromstring(await response.text())
                await func(tree)

                await asyncio.sleep(self.timeout)
                self.i += 1

        if self.is_browser:
            self.task = spa_task
        else:
            self.task = mpa_task

        return self.task

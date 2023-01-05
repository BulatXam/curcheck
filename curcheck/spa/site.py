from typing import List, Any

import asyncio
from asyncio import coroutine

from pyppeteer.browser import Browser

from ..base import AbstractSite

from .page import Page


class Site(AbstractSite):
    def __init__(self, browser: Browser, domain: str):
        self.browser = browser
        self.domain = domain
        self.pages = []

    async def create_page(self, url: str, timeout: int = 5) -> Page:
        browser_page = await self.browser.newPage()
        await browser_page.goto(f"{self.domain}{url}")
        await asyncio.sleep(timeout)

        page = Page(page=browser_page)
        self.pages.append(page)

        return page

    async def create_page_task(self, url: str, task: coroutine) -> Any:
        page = await self.create_page(url)

        return await task(page)

    async def paginate(self, urls: List[str], func: coroutine) -> List[Any]:
        tasks = []

        for url in urls:
            tasks.append(self.create_page_task(url, func))
        
        results = await asyncio.gather(*tasks)
        return results

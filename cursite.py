from typing import List

import asyncio
from asyncio import coroutine

from pyppeteer.browser import Browser


class Site:
    def __init__(self, browser: Browser, domain: str):
        self.browser = browser
        self.domain = domain
        self.pages = []

    async def create_page(self, url: str, timeout: int = 5):
        browser_page = await self.browser.newPage()
        await browser_page.goto(f"{self.domain}{url}")
        await asyncio.sleep(timeout)

        page = Page(page=browser_page)
        self.pages.append(page)

        return page
    
    async def create_page_task(self, url: str, task: coroutine):
        page = await self.create_page(url)

        return await task(page)

    async def paginate(self, urls: List[str], func: coroutine):
        tasks = []

        for url in urls:
            tasks.append(self.create_page_task(url, func))
        
        results = await asyncio.gather(*tasks)
        return results


async def get_site(browser: Browser, domain: str) -> Site:
    return Site(browser=browser, domain=domain)

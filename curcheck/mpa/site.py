from typing import List, Any

from io import StringIO

import asyncio
from asyncio import coroutine

from aiohttp import ClientSession

from lxml import etree

from ..base import AbstractSite

from .page import Page


class Site(AbstractSite):
    def __init__(self, domain: str):
        self.domain = domain
        self.pages = []
    
    async def create_page(self, url: str, timeout: int = 0) -> Page:
        async with ClientSession() as session:
            response = await session.get(self.domain+url)
            data = StringIO(await response.text())

            html_parser = etree.HTMLParser()
            tree = etree.parse(data, html_parser)

            page = Page(tree=tree)

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

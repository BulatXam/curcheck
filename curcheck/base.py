from typing import List, Any, Iterator

from asyncio import coroutine

from pyppeteer.browser import Browser
from pyppeteer.page import Page as pyppeteerPage


class AbstractPage:
    def __init__(self, page: pyppeteerPage):
        self.page = page

    async def iter_products(self, xpath: str, **kwargs) -> Iterator[dict]:
        raise NotImplementedError

    async def get_products(self, xpath: str, **kwargs) -> List[dict]:
        raise NotImplementedError


class AbstractSite:
    def __init__(self, browser: Browser, domain: str):
        self.browser = browser
        self.domain = domain
        self.pages = []

    async def create_page(self, url: str, timeout: int = 5) -> AbstractPage:
        raise NotImplementedError
    
    async def create_page_task(self, url: str, task: coroutine) -> Any:
        raise NotImplementedError

    async def paginate(self, urls: List[str], func: coroutine) -> List[Any]:
        raise NotImplementedError

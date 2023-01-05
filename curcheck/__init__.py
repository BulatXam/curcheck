from typing import Union

from aiohttp import ClientSession

from io import StringIO

from lxml import etree

from pyppeteer import launch
from pyppeteer.browser import Browser

from .mpa.site import Site as mpa_site
from .spa.site import Site as spa_site


async def is_spa_site(url: str, check_xpath: str) -> bool:
    async with ClientSession() as session:
        response = await session.get(url)
        data = StringIO(await response.text())

        html_parser = etree.HTMLParser()
        tree = etree.parse(data, html_parser)

        check_element = tree.xpath(check_xpath)

        if not check_element:
            return True


async def get_site(
    domain: str, browser: Browser = None, base_page_url: str = "", 
    check_xpath: str = None, is_spa: bool = False
) -> Union[mpa_site, spa_site]:
    if is_spa or await is_spa_site(
        url=f"{domain}{base_page_url}", 
        check_xpath=check_xpath
    ):
        if not browser:
            browser = await launch()

        return spa_site(browser=browser, domain=domain)
    else:
        return mpa_site(domain=domain)

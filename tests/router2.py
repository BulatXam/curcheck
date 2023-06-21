import asyncio

from pyppeteer.browser import Page
from xml import etree

from curcheck import SiteRouter


router2 = SiteRouter(
    domain="https://academic.ru",
    is_spa=False
)


@router2.page(url="/")
async def hi1(tree: etree):
    print(
        tree.xpath(
            "a[starts-with(@href,'//dic.academic.ru/contents.nsf')]"
        )
    )

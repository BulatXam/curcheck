import asyncio

from pyppeteer.page import Page

from curcheck import SiteRouter


router1 = SiteRouter(
    domain="https://inf-ege.sdamgia.ru",
    is_spa=True,
)

@router1.page("test?id=13325835")
async def hi(page: Page):
    element = await page.xpath("//div[@class='new_header']/b")
    print(
        await page.evaluate(
            "(element) => element.innerText", element[0]
        )
    )

import pytest

from curcheck import get_site

from curcheck.spa.site import Site
from curcheck.spa.page import Page


@pytest.mark.asyncio
async def test_create_site():
    site = await get_site(
        domain="https://www.wildberries.ru/",
        is_spa=True
    )
    await site.browser.close()

    assert isinstance(site, Site)


@pytest.mark.asyncio
async def test_create_page():
    site = await get_site(
        domain="https://www.wildberries.ru/",
        is_spa=True
    )
    page = await site.create_page(
        url="/"
    )
    await site.browser.close()

    assert isinstance(page, Page)


@pytest.mark.asyncio
async def test_create_page_task():
    async def test_task(page: Page):
        return await page.page.xpath("//h2")

    site = await get_site(
        domain="https://www.wildberries.ru/",
        is_spa=True
    )
    task = await site.create_page_task(
        url="/",
        task=test_task
    )

    page = await site.create_page(url="/")

    assert len(task) == len(await page.page.xpath("//h2"))

    await site.browser.close()



@pytest.mark.asyncio
async def test_paginate_task():
    async def test_task(page: Page):
        return await page.page.xpath("//h2")
    
    site = await get_site(
        domain="https://www.wildberries.ru/",
        is_spa=True
    )
    paginator = await site.paginate(
        urls=[
            "catalog/83974872/detail.aspx?targetUrl=MI/", 
            "catalog/93550775/detail.aspx?targetUrl=MI/", 
        ],
        func=test_task
    )

    page1 = await site.create_page("catalog/83974872/detail.aspx?targetUrl=MI/")
    page1_h2 = page1.page.xpath("//h2")

    page2 = await site.create_page("catalog/93550775/detail.aspx?targetUrl=MI/")
    page2_h2 = page2.page.xpath("//h2")

    await site.browser.close()

    assert len(paginator) == len([page1_h2, page2_h2])

import pytest

from curcheck.mpa.site import Site
from curcheck.mpa.page import Page


@pytest.fixture
def site():
    site = Site(domain="https://webdevblog.ru/")

    return site


@pytest.mark.asyncio
async def test_create_site(site):
    assert isinstance(site, Site)


@pytest.mark.asyncio
async def test_create_page(site):
    page = await site.create_page(
        url="python-i-http-klienty/"
    )
    assert isinstance(page, Page)


@pytest.mark.asyncio
async def test_create_page_task(site):
    async def test_task(page: Page):
        return page.tree.xpath("//h2")
    
    task = await site.create_page_task(
        url="python-i-http-klienty/",
        task=test_task
    )

    page = await site.create_page(url="python-i-http-klienty/")

    assert len(task) == len(page.tree.xpath("//h2"))


@pytest.mark.asyncio
async def test_paginate_task(site):
    async def test_task(page: Page):
        return page.tree.xpath("//h2")
    
    paginator = await site.paginate(
        urls=["css-line-clamp/", "obzor-veb-issledovanij-2022-g/", 
                "reaktivnost-v-javascript/"],
        func=test_task
    )

    page1 = await site.create_page("css-line-clamp/")
    page1_h2 = page1.tree.xpath("//h2")

    page2 = await site.create_page("obzor-veb-issledovanij-2022-g/")
    page2_h2 = page2.tree.xpath("//h2")

    page3 = await site.create_page("reaktivnost-v-javascript/")
    page3_h2 = page3.tree.xpath("//h2")

    assert len(paginator) == len([page1_h2, page2_h2, page3_h2])

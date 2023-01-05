from pyppeteer.page import Page as pyppeteerPage
from pyppeteer.element_handle import ElementHandle

from ..base import AbstractPage


class Page(AbstractPage):
    def __init__(self, page: pyppeteerPage):
        self.page = page

    async def get_attribute(self, element: ElementHandle, attribute: str):
        return await self.page.evaluate(
            f"(element) => element.getAttribute('{attribute}')", element
        )

    async def get_text(self, element: ElementHandle):
        return await self.page.evaluate(
            "(element) => element.innerText", element
        )

    async def get_html(self, element: ElementHandle):
        return await self.page.evaluate(
            "(element) => element.innerHTML", element
        )

    async def iter_products(self, xpath: str, **kwargs):
        products = await self.page.xpath(xpath)

        keys = [key for key in kwargs.keys()]
        values_xpath = [value for value in kwargs.values()]

        kwargs_xpath_elements = {}

        for key_num in range(len(keys)):
            values_xpath_element = await self.page.xpath(
                f"{xpath}{values_xpath[key_num]}"
            )
            kwargs_xpath_elements[keys[key_num]] = values_xpath_element

        for product_num in range(len(products)):
            product_schema = {}

            for key_num in range(len(keys)):
                product_schema[keys[key_num]] = kwargs_xpath_elements[keys[key_num]][product_num]
            
            yield product_schema

    async def get_products(self, xpath: str, **kwargs):
        return [product async for product in self.iter_products(xpath, **kwargs)]

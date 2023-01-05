from typing import List

from lxml import etree

from ..base import AbstractPage


class Page(AbstractPage):
    def __init__(self, tree):
        self.tree = tree
    
    async def get_attribute(self, element, attribute: str):
        return element.get(attribute)

    async def get_text(self, element):
        return element.text

    async def get_html(self, element):
        return etree.tostring(element)

    async def iter_products(self, xpath: str, **kwargs) -> List:
        products = self.tree.xpath(xpath)

        if not kwargs:
            for product in products:
                yield product
        else:
            keys = [key for key in kwargs.keys()]
            values_xpath = [value for value in kwargs.values()]

            kwargs_xpath_elements = {}

            for key_num in range(len(keys)):
                values_xpath_element = self.tree.xpath(
                    f"{xpath}{values_xpath[key_num]}"
                )
                kwargs_xpath_elements[keys[key_num]] = values_xpath_element

            for product_num in range(len(products)):
                product_schema = {}

                for key_num in range(len(keys)):
                    product_schema[keys[key_num]] = kwargs_xpath_elements[keys[key_num]][product_num]
                
                yield product_schema
    
    async def get_products(self, xpath: str, **kwargs) -> List:
        return [product async for product in self.iter_products(xpath, **kwargs)]

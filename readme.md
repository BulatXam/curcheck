# Curcheck
___

Library for parsing SPA sites based on pyppeteer

___

### How use

example parsing products in wildberries.ru

```python3
import asyncio

from pyppeteer import launch

from cursite import get_site, Page


async def paginator(page: Page):
    products = await page.get_products(
        xpath="//div["
                "@class='product-card j-card-item j-good-for-listing-event'"
            "]",
        title="//strong[@class='brand-name']",
        delivery="//b[@class='product-card__delivery-date']"
    )
    
    return products


async def main():
    browser = await launch(headless=False)
    site = await get_site(browser, domain="https://www.wildberries.ru")
    page = await site.create_page(
        url="/",
    )
    urls_elements = await page.get_products(
        xpath="//li[@class='swiper-slide promo__item']",
        url="//a[@class='j-banner-shown-stat j-banner-click-stat j-banner-wba j-banner']",
    )

    urls = [await page.get_attribute(element['url'], "href") for element in urls_elements]
    print(urls)
    for products in await site.paginate(urls[:3], paginator):
        print(products)

    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

### The code does:

- Create page
- Parsing catalog urls
- Parsing products in catalog for site.paginate
- Performs the "paginator" function on each paginated page

# <p align="center"> Curcheck </p>

<p align="center">Library for parsing spa and mpa sites.

___

## Installation

``` python
pip install curcheck
```

___

## How use

``` python
import asyncio

from pyppeteer.page import Page

from curcheck.router import ExecuteRouter
from curcheck.dispatcher import Dispatcher


dispatcher = Dispatcher()

router = ExecuteRouter(
    domain="https://web.whatsapp.com",
    is_spa=True,
    is_login=True
)


@router.page(
    url="/", 
)
async def start(page: Page):
    await asyncio.sleep(60)


async def main():
    dispatcher.include_router(router)
    await dispatcher.start(headless=False)


asyncio.run(main())

```

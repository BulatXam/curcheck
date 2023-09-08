"""
    Модуль роутеров-сборников команд, вызывающих нужные события-декораторы.

    Каждый роутер-это отдельный сайт. Регулирует кол-во страниц и тд в каждом
    отдельном сайте для наиболее эффективного парсинга.
"""

import asyncio
import json
import functools

from loguru import logger

from abc import ABC, abstractmethod

from typing import List, Awaitable
from aiohttp import ClientSession

from pyppeteer import launch
from pyppeteer.browser import Browser

from .events import AbstractEvent, EventPage, EventPaginator, EventLongpoll


class AbstractRouter(ABC):
    def __init__(
        self, 
        domain: str,
        is_spa: bool = False, 
        is_login: bool = False, 
        login_wait: int = 60,
        login_aux: Awaitable|None = None,
        debug: bool = True
    ) -> None:
        self.domain = domain
        self.is_spa = is_spa
        self.is_login = is_login
        self.login_wait = login_wait # Сколько надо ждать чтобы залогиниться
        self.login_aux = login_aux
        self.debug = debug

        self.browser: Browser|None = None

        self.cookie: list|None = None

    @abstractmethod
    def paginate_page(
        self, 
        url: str, 
        pages_links_xpath: str, 
        count_in_approach: int = 10,
        auxiliary_function: Awaitable|None = None, 
        paginate_urls: List[str]|None = None
    ) -> EventPaginator:
        """ Выполнения сразу несколько страниц в несолько потоков. """
        paginator = EventPaginator(
            domain=self.domain, 
            url=url,
            pages_links_xpath=pages_links_xpath, 
            count_in_approach=count_in_approach,
            is_browser=self.is_spa,
            auxiliary_function=auxiliary_function,
            paginate_urls=paginate_urls,
        )

        return paginator

    @abstractmethod
    def page(self, url: str) -> EventPage:
        """ Исполнение 1 страницы """
        page = EventPage(
            domain=self.domain, 
            url=url,
            is_browser=self.is_spa,
        )

        return page

    @abstractmethod
    def longpoll(
        self, url: str, timeout: int = 60, count: int|None = None
    ) -> EventLongpoll:
        """ 
        Постоянно выполнение 1 страницы раз в опредленное время определенное
        кол-во раз(можно бесконечно). """
        longpoll = EventLongpoll(
            domain=self.domain,
            url=url,
            timeout=timeout,
            count=count,
            is_browser=self.is_spa,
        )

        return longpoll

    @abstractmethod
    def _set_cookies_in_pages(self, cookie) -> None:
        pass

    async def _login_aux_func(self) -> None:
        try:
            with open(f"{self.domain.split('/')[-1]}.json") as f:
                self._set_cookies_in_pages(json.load(f))
        except FileNotFoundError:
            browser = await launch(headless=False)
            page = await browser.newPage()
            page.setDefaultNavigationTimeout(0)
            await page.goto(self.domain)
            await page.evaluate(
                f"() => alert('Привет, это окно для логина. "
                f"Обязательно нажми ок и залогинься в течении {self.login_wait} секунд.')"
            )
            await asyncio.sleep(self.login_wait)

            with open(f"{self.domain.split('/')[-1]}.json", 'w+') as f:
                json.dump(await page.cookies(), f)
                self._set_cookies_in_pages(await page.cookies())
    
    async def _aux_login(self) -> None:
        try:
            with open(f"{self.domain.split('/')[-1]}.json") as f:
                self._set_cookies_in_pages(json.load(f))
                logger.debug("Вход в акк по файлу куки")
        except FileNotFoundError:
            browser = await launch(headless=False)
            page = await browser.newPage()
            page.setDefaultNavigationTimeout(0)
            logger.warning("Файл куки не найден")
            if self.login_aux:
                logger.debug("Создаем куки с помощью вспомогательной функции")
                await self.login_aux(page)
            else:
                logger.debug("Вспомогательной функции нет, создаем куки вручную")
                await page.goto(self.domain)
                await page.evaluate(
                    f"() => alert('Привет, это окно для логина. "
                    f"Обязательно нажми ок и залогинься в течении {self.login_wait} секунд.')"
                )
                await asyncio.sleep(self.login_wait)

            with open(f"{self.domain.split('/')[-1]}.json", 'w+') as f:
                json.dump(await page.cookies(), f)
                self._set_cookies_in_pages(await page.cookies())

    @abstractmethod
    async def executor(self, browser: Browser|None = None) -> None:
        pass

    def include_middleware(self):
        pass


class AuxRouter(AbstractRouter):
    """
    Aux-Auxulary-вспомогальный роутер.

    Роутер, с декораторами, которые требуют(!) вызова функций из вне.
    Функции возвращает данные и должна быть подключена в определнные части 
    архитектуры. Нужна для интеграции в ботов, приложений и т.п.

    При инициализации роутера, браузер запускается сам по себе.
    """
    def __init__(
        self, 
        domain: str,
        is_spa: bool = False, 
        is_login: bool = False, 
        login_wait: int = 60,
        # login_aux: Awaitable|None = None,
        debug: bool = True,
    ) -> None:
        super().__init__(
            domain=domain,
            is_spa=is_spa,
            is_login=is_login,
            login_wait=login_wait,
            debug=debug
        )

    def page(self, url: str) -> EventPage:
        super_page = super().page(url=url)
        def wrapper(func: Awaitable):
            @functools.wraps(func)
            async def _wrapper(*args, **kwargs):
                return await self.execute(
                    executable_event=super_page,
                    func=func,
                    *args, 
                    **kwargs,
                )
            return _wrapper
        return wrapper

    async def longpoll(
        self, url: str, timeout: int = 60, count: int|None = None
    ):
        super_longpoll = super().longpoll(
            url=url, timeout=timeout, count=count
        )
        def wrapper(func: Awaitable):
            @functools.wraps(func)
            async def _wrapper(*args, **kwargs):
                return await self.execute(
                    executable_event=super_longpoll,
                    func=func,
                    *args,
                    **kwargs
                )
            return _wrapper
        return wrapper
                

    async def paginate_page(
        self, 
        url: str, 
        pages_links_xpath: str, 
        count_in_approach: int = 10,
        auxiliary_function: Awaitable|None = None, 
        paginate_urls: List[str]|None = None
    ):
        def wrapper(func: Awaitable):
            paginator_event = EventPaginator(
                url=url,
                pages_links_xpath=pages_links_xpath,
                count_in_approach=count_in_approach,
                auxiliary_function=auxiliary_function,
                paginate_urls=paginate_urls
            )
            @functools.wraps(func)
            async def _wrapper(*args, **kwargs):
                return await self.execute(
                    executable_event=paginator_event,
                    func=func,
                    *args,
                    **kwargs
                )
            return _wrapper
        return wrapper
    
    async def execute(
            self, 
            executable_event: AbstractEvent,
            func: Awaitable,
            *args,
            **kwargs
        ):
        """ Здесь будет регистрация, логин, добавление хуки и всякая боль """

        if self.is_login and not self.cookie:
            # если нет куки для регистрации
            await self._aux_login()

        if self.cookie:
            executable_event.cookies = self.cookie

        return await executable_event(func)(
            browser=self.browser, *args, **kwargs
        )

    def _set_cookies_in_pages(self, cookie) -> None:
        self.cookie = cookie

    async def executor(self, browser: Browser) -> None:
        """ 
        Чтобы корректно влючился браузер во все корутины роутера, экзеутор
        должен быть включен до вызова нужных функций 
        """
        if not browser:
            browser = await launch(headless=False)

        self.browser = browser


class ExecuteRouter(AbstractRouter):
    """ 
    execute-исполнять. Самовключающийся роутер.

    Роутер, с декораторами, которые не требуют(!) вызова функций из вне, 
    а запускают все сами экзекутором и управляются автоматически. Функции не
    возвращают никаких данных, они требуются для занесения в базу данных или в 
    для хранения в другой форме. Являются локальной зоной архитектуры и никак не
    общаются с остальными частями архитектуру. Только через бд.
    """

    def __init__(
        self, 
        domain: str, 
        is_spa: bool = False, 
        is_login=False, 
        login_wait=60,
        login_aux: Awaitable|None = None,
        debug: bool = True,
    ) -> None:
        self.domain = domain
        self.is_spa = is_spa
        self.is_login = is_login
        self.login_wait = login_wait # Сколько надо ждать чтобы залогиниться
        self.login_aux = login_aux
        self.debug = debug

        self.browser: Browser = None

        self.pages: List[EventPage] = []
        self.paginators: List[EventPaginator] = []
        self.longpolls: List[EventLongpoll] = []

    def paginator(
        self,
        paginate_urls: List[str],
        count_in_approach: int = 10,
    ) -> EventPaginator:
        paginator = EventPaginator(
            domain=self.domain, 
            count_in_approach=count_in_approach,
            is_browser=self.is_spa,
            paginate_urls=paginate_urls,
        )
        self.paginators.append(paginator)

        return paginator

    def paginate_page(
        self, 
        url: str, 
        pages_links_xpath: str, 
        count_in_approach: int = 10,
        auxiliary_function: Awaitable|None = None, 
        paginate_urls: List[str]|None = None
    ) -> EventPaginator:
        paginator = super().paginate_page(
            url=url,
            pages_links_xpath=pages_links_xpath, 
            count_in_approach=count_in_approach,
            auxiliary_function=auxiliary_function,
            paginate_urls=paginate_urls,
        )
        self.paginators.append(paginator)

        return paginator

    def page(self, url: str) -> EventPage:
        page = super().page(url=url)
        self.pages.append(page)

        return page

    def longpoll(
        self, url: str, timeout: int = 60, count: int|None = None
    ) -> EventLongpoll:
        longpoll = super().longpoll(
            url=url,
            timeout=timeout,
            count=count,
        )
        self.longpolls.append(longpoll)

        return longpoll
    
    def _set_cookies_in_pages(self, cookie) -> None:
        for page in self.pages:
            page.cookies = cookie

        for paginator in self.paginators:
            paginator.cookies = cookie

        for longpoll in self.longpolls:
            longpoll.cookies = cookie
    
    async def _execute_spa(self) -> None:
        if not browser:
            browser = await launch(headless=True)

        await asyncio.gather(
            *[page.task(browser) for page in self.pages]
        )

        await asyncio.gather(
            *[paginator.task(browser) for paginator in self.paginators]
        )

        await asyncio.gather(
            *[longpoll.task(browser) for longpoll in self.longpolls]
        )
    
    async def _execute_mpa(self) -> None:
        async with ClientSession() as session:
            await asyncio.gather(
                *[page.task(session) for page in self.pages]
            )

            await asyncio.gather(
                *[paginator.task(session) for paginator in self.paginators]
            )

            await asyncio.gather(
                *[longpoll.task(session) for longpoll in self.longpolls]
            )

    async def debug_executor(self, browser: Browser|None = None) -> None:
        try:
            if self.is_spa:
                if self.is_login:
                    await self._aux_login()
                await self._execute_spa()
            else:
                await self._execute_mpa()
        except Exception as exp:
            logger.error(exp)
    
    async def deploy_executor(self, browser: Browser|None = None) -> None:
        if self.is_spa:
            if self.is_login:
                await self._aux_login()
            await self._execute_spa()
        else:
            await self._execute_mpa()
    
    async def executor(self, browser: Browser|None = None) -> None:
        logger.info("Начинаем исполнение парсерных функций... ")
        if self.debug:
            await self.debug_executor(browser=browser)
        else:
            await self.deploy_executor(browser=browser)

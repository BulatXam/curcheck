import asyncio

from curcheck import *

dispatcher = Dispatcher()


async def main():
    from router1 import router1
    from router2 import router2

    dispatcher.include_router(router1)
    dispatcher.include_router(router2)

    await dispatcher.start()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())

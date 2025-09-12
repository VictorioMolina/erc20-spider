"""
Main entry point for the ERC-20 Spider Bot.
Initialises the bot instance and handles graceful shutdown signals.
"""

import asyncio
import signal

from core.eth_spider import SpiderBot


async def _main() -> None:
    """
    Asynchronous main function to initialise and start the spider bot.
    Configures signal handlers for clean shutdown on interrupt or termination.
    """
    bot = SpiderBot()
    
    loop = asyncio.get_event_loop()
    
    loop.add_signal_handler(
        signal.SIGINT,
        lambda: asyncio.create_task(bot.stop())
    )
    
    loop.add_signal_handler(
        signal.SIGTERM,
        lambda: asyncio.create_task(bot.stop())
    )
    
    await bot.start()


if __name__ == "__main__":
    asyncio.run(_main())

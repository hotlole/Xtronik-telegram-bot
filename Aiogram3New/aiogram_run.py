import asyncio
import logging
from create_bot import bot, dp
from handlers.start import start_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    dp.include_router(start_router)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
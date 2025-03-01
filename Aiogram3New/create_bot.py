import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Инициализация диспетчера
dp = Dispatcher(storage=MemoryStorage())

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Экспортируемые объекты
__all__ = ['bot', 'dp', 'scheduler']
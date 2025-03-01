from aiogram import Bot, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from create_bot import bot
from . import problem_handler
from aiogram.types import FSInputFile
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


start_router = Router()

# ID группы для трансляции сообщений
GROUP_ID = -4647347489

# Машина состояний для обработки выбора
class ProblemSelection(StatesGroup):
    waiting_for_problem = State()
    waiting_for_custom_problem = State()

# Меню выбора адаптера
menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="CHAdeMO - GB/T", callback_data="adapter_chademo_gbt"),
     InlineKeyboardButton(text="CCS2 - GB/T", callback_data="adapter_ccs2_gbt")],
    [InlineKeyboardButton(text="CHAdeMO - CCS", callback_data="adapter_chademo_ccs"),
     InlineKeyboardButton(text="GB/T - CCS2", callback_data="adapter_gbt_ccs2")]
])
# Основная клавиатура с кнопкой "Старт"
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Старт")]
    ],
    resize_keyboard=True  # Подгоняем под экран
)

# Команда /start (срабатывает на команду или кнопку "🚀 Старт")
@start_router.message(F.text == "🚀 Старт")
@start_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Это бот Xtronik, созданный для помощи с переходниками для зарядных станций.\n"
        "Выберите тип переходника, с которым у вас проблема:",
        reply_markup=menu  # Показываем меню выбора адаптера
    )
# Обработка выбора адаптера
@start_router.callback_query(F.data.startswith("adapter_"))
async def handle_adapter_selection(callback: CallbackQuery, state: FSMContext):
    adapter_type = callback.data  # Сохраняем выбранный адаптер
    await state.update_data(adapter=adapter_type)

    await callback.message.edit_text(
        "Выберите тип проблемы:",
        reply_markup=problems_menu()
    )
    await state.set_state(ProblemSelection.waiting_for_problem)

# Функция для генерации кнопок с проблемами
def problems_menu() -> InlineKeyboardMarkup:
    problems = [
        "Как пользоваться этим переходником",
        "Обрыв зарядной сессии",
        "Не запускается зарядная сессия",
        "Получить список станций, на которых переходники работают стабильно",
        "Другая проблема"
    ]
    buttons = [
        [InlineKeyboardButton(text=problem, callback_data=str(i))]
        for i, problem in enumerate(problems)
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_adapters")])  # Добавили кнопку назад
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Обработчик кнопки "🔙 Назад"
@start_router.callback_query(F.data == "back_to_adapters")
async def back_to_adapters(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # Сбрасываем состояние
    await callback.message.edit_text(
        "Выберите тип переходника, с которым у вас проблема:",
        reply_markup=menu  # Показываем меню выбора адаптера
    )

# Обработка выбора проблемы
@start_router.callback_query(ProblemSelection.waiting_for_problem)
async def handle_problem_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    adapter_type = data.get("adapter")

    if callback.data == "cancel":
        await state.clear()
        await callback.message.answer("Выбор отменён. Введите /start, чтобы начать заново.")
        return

    if not callback.data.isdigit():
        await callback.message.answer("Ошибка: некорректный выбор проблемы.")
        return

    problem_index = int(callback.data)
    problems_list = [
        "Как пользоваться этим переходником",
        "Обрыв зарядной сессии",
        "Не запускается зарядная сессия",
        "Получить список станций, на которых переходники работают стабильно",
        "Другая проблема"
    ]

    problem_title = problems_list[problem_index]

    if problem_index == 4:  # "Другая проблема"
        await callback.message.answer("Опишите вашу проблему, и мы обязательно поможем вам:")
        await state.set_state(ProblemSelection.waiting_for_custom_problem)
        return

    # Получаем описание стандартной проблемы
    problem_description = problem_handler.get_problem_description(adapter_type, problem_index)

    # Дополнительная информация для CCS2-GBT
    if adapter_type == "adapter_ccs2_gbt" and problem_index == 2:
        problem_description += (
            "\n\n🔴Важно: Этапы зарядки CCS2-GBT\n\n"
            "⚪Белый (5 сек.) – Загрузка\n"
            "🟣Фиолетовый – Готова к старту зарядной сессии\n\n"
            "✨Моргание (готов к заряду):\n"
            "🟢Зеленый – Батарея полностью заряжена\n"
            "🔵Синий – Осталось 30-70% заряда\n"
            "🔴Красный – Батарея разряжена\n\n"
            "⚪Белый (короткое горение) – Установка связи со станцией\n"
            "🌊Бирюзовый – Начат обмен данными\n"
            "🟢Зеленый (горение) – Идет зарядка\n\n"
            "Если переходник моргает красным, значит он разряжен. Зарядите его перед использованием! 🔋"
        )
        animation = FSInputFile("media/gifka.gif")
        await bot.send_animation(chat_id=callback.message.chat.id, animation=animation)

    # Отправляем ответ пользователю с полным описанием
    await callback.message.answer(problem_description)

    # Транслируем в группу только название проблемы
    await bot.send_message(
        GROUP_ID,
        f"👤 Пользователь: @{callback.from_user.username or callback.from_user.full_name}\n"
        f"🔌 Адаптер: {adapter_type.replace('adapter_', '').upper()}\n"
        f"❗ Проблема: {problem_title}"
    )

    await state.clear()  # Сбрасываем состояние

# Обработка пользовательского ввода кастомной проблемы
@start_router.message(ProblemSelection.waiting_for_custom_problem)
async def handle_custom_problem(message: Message, state: FSMContext):
    data = await state.get_data()
    adapter_type = data.get("adapter")
    custom_problem = message.text

    # Отправляем ответ пользователю
    await message.answer("Спасибо! Ваша проблема передана специалистам.")

    # Транслируем информацию в группу
    await bot.send_message(
        GROUP_ID,
        f"👤 Пользователь: @{message.from_user.username or message.from_user.full_name}\n"
        f"🔌 Адаптер: {adapter_type.replace('adapter_', '').upper()}\n"
        f"❗ Проблема: {custom_problem}\n"
    )

    await state.clear()  # Сбрасываем состояние после обработки

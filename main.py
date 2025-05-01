import logging
import asyncio
import time

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import TOKEN, ADMIN_IDS, BOOKING_URL, RULES_URL, LOCATION_URL, SOCIAL_URL

logging.basicConfig(level=logging.INFO)

class ContactAdmin(StatesGroup):
    waiting_for_message = State()

class Chatting(StatesGroup):
    in_chat = State()

active_chats = {}

main_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔗 Забронювати місце", url=BOOKING_URL)],
    [InlineKeyboardButton(text="📜 Правила озера", url=RULES_URL)],
    [InlineKeyboardButton(text="📍 Локація озера", url=LOCATION_URL)],
    [InlineKeyboardButton(text="📸 Ми в соцмережах", callback_data="social_links")],
    [InlineKeyboardButton(text="✉️ Зв'язок з адміністрацією", callback_data="contact_admin")]
])

reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="До меню")]
    ],
    resize_keyboard=True
)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
@dp.message(F.text.lower() == "до меню")
async def start_handler(message: Message):
    await message.answer("🎣 Вітаємо на офіційному боті спортивного озера Едельвейс!\n\nОберіть потрібну опцію нижче ⬇️",
                         reply_markup=main_buttons)

@dp.callback_query(F.data == "go_home")
async def go_home(callback: CallbackQuery):
    await callback.message.answer("🎣 Вітаємо на офіційному боті спортивного озера Едельвейс!\n\nОберіть потрібну опцію нижче ⬇️",
                                  reply_markup=main_buttons)
    await callback.answer()

@dp.callback_query(F.data == "social_links")
async def social_links_callback(callback: CallbackQuery):
    text = "🌐 Наші соцмережі: (тут зʼявиться ваш текст)"
    await callback.message.answer(text, reply_markup=reply_keyboard)
    await callback.answer()

@dp.callback_query(F.data == "contact_admin")
async def contact_admin_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✉️ Напишіть ваше повідомлення для адміністрації:", reply_markup=reply_keyboard)
    await state.set_state(ContactAdmin.waiting_for_message)
    await callback.answer()

@dp.message(ContactAdmin.waiting_for_message)
async def handle_user_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    for admin_id in ADMIN_IDS:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Прийняти консультацію", callback_data=f"take_chat_{user_id}")]
        ])

        if message.photo:
            largest_photo = message.photo[-1]
            await bot.send_photo(admin_id, largest_photo.file_id, caption=f"📨 Фото від @{username}", reply_markup=reply_markup)
        else:
            text = message.text or "<непідтримуваний формат>"
            await bot.send_message(admin_id, f"📨 Повідомлення від @{username}:\n{text}", reply_markup=reply_markup)

    await message.answer("✅ Ваше повідомлення надіслано. Очікуйте відповідь адміністратора.", reply_markup=reply_keyboard)
    await state.clear()

@dp.callback_query(F.data.startswith("take_chat_"))
async def take_chat(callback: CallbackQuery):
    admin_id = callback.from_user.id
    user_id = int(callback.data.split("_")[-1])
    active_chats[admin_id] = user_id

    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Завершити консультацію", callback_data="end_chat")]
    ])

    await callback.message.answer(f"✅ Ви прийняли чат з користувачем <code>{user_id}</code>.\nВідтепер ви можете йому писати прямо сюди.", reply_markup=reply_markup)
    await callback.answer()

@dp.callback_query(F.data == "end_chat")
async def end_chat(callback: CallbackQuery):
    admin_id = callback.from_user.id
    user_id = active_chats.pop(admin_id, None)

    if user_id:
        try:
            await bot.send_message(user_id, "🔚 Консультацію завершено. Дякуємо за звернення!", reply_markup=reply_keyboard)
        except:
            pass

    await callback.message.answer("✅ Консультацію завершено.", reply_markup=reply_keyboard)
    await callback.answer()

@dp.message(F.from_user.id.in_(ADMIN_IDS))
async def admin_message(message: Message):
    admin_id = message.from_user.id
    user_id = active_chats.get(admin_id)

    if not user_id:
        await message.answer("❗ Ви ще не вибрали користувача. Спочатку натисніть «Прийняти консультацію».")
        return

    try:
        if message.photo:
            largest_photo = message.photo[-1]
            await bot.send_photo(user_id, largest_photo.file_id, caption="💬 Адміністрація", reply_markup=reply_keyboard)
        else:
            await bot.send_message(user_id, f"💬 Адміністрація:\n{message.text}", reply_markup=reply_keyboard)
        await message.answer("✅ Повідомлення надіслано.")
    except Exception:
        await message.answer("❌ Не вдалося надіслати повідомлення.")

@dp.message()
async def handle_additional_user_message(message: Message):
    user_id = message.from_user.id

    for admin_id, chatting_user in active_chats.items():
        if chatting_user == user_id:
            if message.photo:
                largest_photo = message.photo[-1]
                await bot.send_photo(admin_id, largest_photo.file_id, caption="📨 Фото від користувача", reply_markup=reply_keyboard)
            else:
                await bot.send_message(admin_id, f"📨 Користувач:\n{message.text}", reply_markup=reply_keyboard)
            return

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

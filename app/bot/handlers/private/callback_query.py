from contextlib import suppress

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery

from app.bot.handlers.private.windows import Window
from app.bot.manager import Manager
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData
from app.bot.utils.texts import SUPPORTED_LANGUAGES

router = Router()
router.callback_query.filter(F.message.chat.type == "private", StateFilter(None))


@router.callback_query(F.data.startswith("close_ticket:"))
async def close_ticket_handler(
    call: CallbackQuery,
    manager: Manager,
    redis: RedisStorage,
    user_data: UserData,
) -> None:
    """
    Handles the user's response to the ticket close confirmation.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    parts = call.data.split(":")  # ["close_ticket", "yes"/"no", "12345"]
    action = parts[1]
    thread_id = int(parts[2])

    if action == "yes":
        with suppress(TelegramBadRequest):
            await manager.bot.delete_forum_topic(
                chat_id=manager.config.bot.GROUP_ID,
                message_thread_id=thread_id,
            )
        await redis.clear_topic(thread_id, user_data.id)
        text = manager.text_message.get("close_ticket_confirmed")
    else:
        text = manager.text_message.get("close_ticket_declined")

    with suppress(TelegramBadRequest):
        await call.message.edit_text(text)
    await call.answer()


@router.callback_query()
async def handler(call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData) -> None:
    """
    Handles callback queries for selecting the language.

    If the callback data is 'ru' or 'en', updates the user's language code in Redis and sets
    the language for the manager's text messages. Then, displays the main menu window.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    if call.data in SUPPORTED_LANGUAGES.keys():
        user_data.language_code = call.data
        manager.text_message.language_code = call.data
        await redis.update_user(user_data.id, user_data)
        await manager.state.update_data(language_code=call.data)
        await Window.main_menu(manager)

    await call.answer()

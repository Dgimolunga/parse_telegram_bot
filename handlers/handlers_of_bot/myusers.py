# -*- coding: utf-8 -*-
from telethon import events
from ..tools import states as st
from ...Database import database as db
from telethon.tl.custom import Button
from ..tools import tools


@events.register(events.CallbackQuery(pattern='myusers_'))
@tools.fsm_decor(st.ActionCallBack())
async def BOT_handler_button_myusers(event):
    _ = CI[event]._
    # localization.change_lang('ru_RU')
    users_list = db.get_all_users(event.sender_id)
    buttons = []
    if users_list:
        buttons = [Button.inline(f'{user_logging}', f'user_{user_logging}') for user_logging in users_list]
        buttons = list(tools.split_(buttons, 2))
    buttons.append([Button.inline(_('🧑‍💻 Create new user'), 'newuser')])
    buttons.append([Button.inline(_('🧑‍💻 Add user to me'), 'adduser')])
    await event.edit(_('Choose a username from the list below:'), buttons=buttons)
    return [event.message_id]


@events.register(events.NewMessage(pattern='/myusers'))
@tools.fsm_decor(st.ActionCommand())
async def BOT_handler_myusers_command(event):
    _ = CI[event]._
    # localization.change_lang('ru_RU')
    users_list = get_all_users(event.sender_id)
    buttons = []
    if users_list:
        buttons = [Button.inline(f'{user_logging}', f'user_{user_logging}') for user_logging in users_list]
        buttons = list(split_(buttons, 2))
    buttons.append([Button.inline(_('🧑‍💻 Create new user'), 'newuser')])
    buttons.append([Button.inline(_('🧑‍💻 Add user to me'), 'adduser')])
    message = await event.respond(_('Choose a username from the list below:'), buttons=buttons)
    return [message.id]

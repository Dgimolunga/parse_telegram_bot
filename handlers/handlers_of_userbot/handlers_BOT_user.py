# -*- coding: utf-8 -*-
from logger import logger as my_logger
# import localization.localization as localization
import telethon
import config_for_bot as cfg
from data_value import telegram_parse

""" Handlers and method for User_bot"""
# ____________________________________________________________
# add my logger
logger = my_logger.get_logger(__name__)


# ____________________________________________________________
# handlers for telegram client
@telethon.events.register(telethon.events.NewMessage(chats=[-1001518950788]))
async def event_handler_ms_from(event):
    client_event = event.client
    if event.message and event.message.sender_id != -1001557150106:
        print(event.message.text)
        await client_event.forward_messages(cfg.my_channel_id, event.message)
        if event.message.text == "132":
            telegram_parse.add_client_to_loop()
            print('client connect!: ')
    raise telethon.events.StopPropagation


@telethon.events.register(telethon.events.NewMessage)
async def event_handler_spam_ms(event):
    client_event = event.client
    if event.message and event.message.sender_id not in (-1001509028433, -1001557150106, 1939139289):
        print(event.message.text)
        await client_event.send_message(cfg.my_spam_channel_id, message="!!!SPAM FROM SUB!!!")

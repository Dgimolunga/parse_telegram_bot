# -*- coding: utf-8 -*-
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! конфигурация логов должна быть установлена до импорта всех модулей
import logger.logger as my_logger
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! для избежания не проработки встроееных логеров
import config_for_bot as cfg
from handlers import dict_of_used_handlers as cfg_d
import data_value as data_value
import telethon
import asyncio
from handlers.handlers_of_bot.handlers_BOTS import delete_all_message_from_chats

bot_name_set = {'bot_parse', 'bot_admin', 'bot_user'}
__stop_msg__ = 'Program STOP' + '❌' * 100 + 'Program STOP'

if __name__ == '__main__':
    logger = my_logger.get_logger(__name__)


class MyTelethonClient(telethon.TelegramClient):
    __bot_name_set = bot_name_set

    def __init__(self, api_id: int, api_hash: str, bot_type: str = 'bot_parse',
                 session: 'typing.Union[str, Session]' = None):
        if bot_type not in self.__bot_name_set:
            raise AttributeError(f'type_bot must be in {self.__bot_name_set}')
        if session is None:
            session = f'BOT_USER{cfg.id_}' if bot_type == 'bot_user' else bot_type.upper()
        super().__init__(session, api_id, api_hash)
        for handler in cfg_d.handlers_BOT_dict[bot_type]:
            logger.info('Info: %s add to %s ', handler, session)
            self.add_event_handler(cfg_d.handlers_BOT_dict[bot_type][handler])


# @telethon.events.register(telethon.events.NewMessage)
# async def event_handler_ms(event):
#     client_event = event.client
#     if event.message and event.message.sender_id != -1001557150106:
#         print(client_event)
#         await client_event.send_message(cfg.my_channel_id, message="!!!!!!!!!!!!!!!!!!NewMessage!!!!!!!!!!!!!!!")


# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)
class SingleTonePattern:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingleTonePattern, cls).__new__(cls)
        return cls._instances[cls]


class TelegramParse(SingleTonePattern):
    _logger = logger
    __bot_name_set = bot_name_set
    bots = {'bot_admin': {'name': 'bot_admin', 'bot_client': None, 'msg': {'start_msg': '📍📢Info: START BOT ADMIN '
                                                                                        '👨‍🔧👮🏻‍♂️👨🏼‍⚕️ '}},
            'bot_parse': {'name': 'bot_parse', 'bot_client': None, 'msg': {'start_msg': '📍📢Info: START BOT PARSE '
                                                                                        '🕵️🕵️‍♂️🕵️️ '}},
            'bot_user': {'name': 'bot_user', 'users': [], 'msg': {}},
            }

    def __init__(self, loop):
        self.loop = loop
        self._logger.debug('Initing TelegramParse ...')

    # running telegramClient: bot_parse and bot_admin
    def start(self):
        self.loop.run_until_complete(self.some_BOT_run('bot_admin', cfg.bot_admin_token),)
        self.loop.run_until_complete(self.some_BOT_run('bot_parse', cfg.bot_token))

    # bot client of same bos
    async def some_BOT_run(self, bot_type: str, bot_token: str):
        bot = MyTelethonClient(cfg.api_id, cfg.api_hash, bot_type=bot_type)
        if bot_type == 'bot_user':
            pass
            # self.bots['bot_users'].append(bot)
        else:
            self.bots[bot_type]['bot_client'] = bot
        await bot.start(bot_token=bot_token)
        self._logger.error(self.bots[bot_type]['msg']['start_msg'])
        # await bot.run_until_disconnected()

    # funcion for logger
    def send_bot_message_to(self, msg: str, bot_name='bot_admin', sender=cfg.admin_id):
        task = self.loop.create_task(self.bots[bot_name]['bot_client'].send_message(sender, msg))
        if not self.loop.is_running():
            self.loop.run_until_complete(task)

    async def client_run(self, loop, client_bot=None, sender_id='Dgimolunga2'):
        if client_bot is None:
            client_bot = botsMain
        client = telega("Client" + str(cfg.id_), cfg.api_id, cfg.api_hash, loop=loop)
        cfg.id_ += 1
        await client.connect()
        if not await client.is_user_authorized():
            logger.ERROR('Info: Starting new Client%s', cfg.id_)
            await client.send_code_request("79525362955")
            if client_bot is None:
                client_bot = botsMain
                await client_bot.start()
                await client_bot.connect()
            async with client_bot.conversation(sender_id) as conv:
                await conv.send_message('Enter password?')
                password = await conv.get_response(timeout=100)
                await client.sign_in("79525362955", password)
                await conv.send_message('Nice to meet you, {}!'.format(password.text))
            clients.append(client)
        await client.start()
        await client.run_until_disconnected()

    def add_client_to_loop(client_bot=None, sender_id=None):
        if client_bot is None:
            client_bot = data_value.bots['bot_admin']
        loop = asyncio.get_event_loop()
        loop.create_task(client_run(loop, client_bot, sender_id))


def main():
    logger.info('Starting Main_bot4.3.py ...')
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    asyncio.set_event_loop(loop)
    data_value.telegram_parse = TelegramParse(loop)
    data_value.telegram_parse.start()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.error('📍⛔️KeyboardInterrupt!!!', exc_info=False)
        delete_all_message_from_chats()
    except Exception:
        logger.error('📍⛔️ERROR !!!!', exc_info=True)
    finally:
        logger.error(__stop_msg__)


if __name__ == '__main__':
    main()

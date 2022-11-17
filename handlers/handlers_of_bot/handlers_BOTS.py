# -*- coding: utf-8 -*-
from __future__ import annotations
from logger import logger as my_logger
import localization.localization as localization
from telethon import events
from telethon.errors import MessageNotModifiedError
from telethon.tl.custom import Button
import hashlib
import config_for_bot as cfg
from data_value import telegram_parse
from handlers.tools.chatssettings import CI, ExceptionUserNotSelectedSendAllUsers
from handlers.tools import states as st
from abc import ABC
import asyncio
# ______________________________________________________________________________________________________________________
# import function of database
from Database.database import get_all_users, set_data, get_data_for_str_request, check_user_logging_name_in_db, \
    add_new_user_to_database, db_get_tickers, get_smth_from_database, add_user_to_telegram_id, \
    db_get, db_add_smth_for_user, db_switch_some_for_user, db_del, db_del_1, db_get_all_smth, db_get_1
# import exception of database
from Database.database import NotCorrectExc, DataDuplicateExc, UserNotFoundExc
# import var of database
from Database.database import command_get_list, command_add_list

# ____________________________________________________________
# add my logger
logger = my_logger.get_logger(__name__)

# ____________________________________________________________
# any static
parse_bot_users_state_fsm = st.ParseBotUsersStateFSM()
MAX_SIZE_ADD = 55

# ____________________________________________________________
# any dicts


command_dict = {
    'add_user': '/add_user',
    'my_users': '/myusers'
}

dontUSE_dict_for_back_buttons = {
    'user_': 'myusers',
    'tickers_': 'user_',
    'parsechannels_': 'user_',
    'sharechannels_': 'user_',
    'settings_': 'user_',
    'tags_': 'tickers_',
}

users_setting = {}
name_of_key = {
    'tickers': _('Ticker'),
    'tags': _('Tag'),
    'parsechannels': _('Parsechannel'),
    'sharechannels': _('Sharechannel'),

}


# _____________________________________________________________________________________________________________________
# @decorator functions

def fsm_decor(action: st.ActionForFSM = None, stop_propagation=True):
    def callback(fun):
        async def call(*args, **kwargs):
            try:
                if action:
                    res = await parse_bot_users_state_fsm.action_manager(action, fun, args, kwargs)
                else:
                    await fun(*args, **kwargs)
            except ExceptionUserNotSelectedSendAllUsers:
                await BOT_handler_myusers_command(args[0], stop_propagation=False)

            if stop_propagation and kwargs.get('stop_propagation', True):
                raise events.StopPropagation

        return call

    return callback


def decor_mark_message_for_delete(fun):
    def callback(*args, **kwargs):
        event = args[0]
        # CI[event].messages_for_delete.for_next_delete.update(event.)
        return fun(*args, **kwargs)

    return callback


# _____________________________________________________________________________________________________________________
# tools
def get_k_kdata_backpath_from_data(data):
    res = data.decode().split('_', maxsplit=2)
    return res[0], res[1], res[2]


def comand_get_k_kdata_backpath_from_data(data):
    res = data.decode().split('_', maxsplit=3)
    return res[1], res[2], res[3]


def split_(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_list_with_key_and_keydata_from_eventdata(data):
    res = data.decode().split('_', maxsplit=3)
    res.pop(0)
    return res


async def delete_messages1(event):
    id_messages = CI[event].messages_for_delete.need_delete
    await event.client.delete_messages(event.chat_id, id_messages)
    CI[event].messages_for_delete.need_delete.clear()


def delete_messages(event):
    id_messages = CI[event].messages_for_delete.need_delete
    add_ = CI[event].messages_for_delete.for_next_delete
    id_messages.update(add_)
    loop = asyncio.get_event_loop()
    task = loop.create_task(event.client.delete_messages(event.chat_id, id_messages))
    if not loop.is_running():
        loop.run_until_complete(task)


def delete_all_message_from_chats():
    class FakeEvent:
        import data_value
        client = data_value.telegram_parse.bots['bot_parse']['bot_client']

        def __init__(self, chat_id):
            self.chat_id = chat_id
            self.sender_id = chat_id

    for chat in CI:
        delete_messages(FakeEvent(chat.chat_id))


def check_name_filters(event):
    _ = CI[event]._
    if not check_user_logging_name_in_db(event.text):
        return False, _('Logging name is already in use.')
    if not check_user_logging_name_for_correct(event.text):
        return False, _('Logging name is incorrect, try again.')
    return True, 'Good!'


def check_user_logging_name_for_correct(name: str):
    if (len(name) > 20
            or '/' in name
            or ' ' in name
            or '`' in name
            or '\n' in name
            or '\t' in name):
        return False
    return True


def check_and_get_add_text(text):
    if not text:
        return False
    while text.find('\n\n') > 0:
        text = text.replace('\n\n', '\n')
    res = text.split('\n')
    for one in res:
        if len(one) > MAX_SIZE_ADD:
            return False
    return res


# ______________________________________________________________________________________________________________________
# buttons classes
class MButton:
    def __init__(self, button_title='Button', button_data=None):
        self.button_data = button_data
        self.button_msg = button_title

    def get_button(self):
        return Button.inline(self.button_msg, self.button_data)


class DeleteButton:
    def __init__(self, buttons_table):
        self.button = MButton(_('Delete this'), 'confirmdelete_')
        self.buttons_table = buttons_table

    def create_button(self):
        btf = self.buttons_table.buttons_table_info
        data = self.buttons_table.event_of_callback_query.data.decode()
        self.button.button_msg += btf.delete_msg
        self.button.button_data += data
        return self.button.get_button()


class AddNewButton:
    def __init__(self, buttons_table):
        self.button = MButton(_('Add new'), 'add_')
        self.buttons_table = buttons_table

    def create_button(self):
        btf = self.buttons_table.buttons_table_info
        data = self.buttons_table.event_of_callback_query.data.decode()
        self.button.button_msg += btf.add_msg
        spl = data.split('_', maxsplit=2)
        self.button.button_data += f'{spl[0]}_{spl[1]}_{data}'
        return self.button.get_button()


class SwitchEnableButton:
    def __init__(self):
        pass


class EditButton:
    def __init__(self, buttons_table):
        self.button = MButton(_('Edit this'), 'edit_')
        self.buttons_table = buttons_table

    def create_button(self):
        btf = self.buttons_table.buttons_table_info
        data = self.buttons_table.event_of_callback_query.data.decode()
        self.button.button_msg += btf.edit_msg
        self.button.button_data += data
        return self.button.get_button()


class BackButton:
    def __init__(self, buttons_table):
        self.button = MButton(_('« Back to'))
        self.buttons_table = buttons_table
    # data = 'user_123'
    # data = 'tickers_1' what tickers hav key_user = 1
    # data = 'tags_2' what tags hame key_ticker = 2, back = what first user have key_ticker=2 (1)
    # data = 'tag_3'
    def create_button(self):

        btf = self.buttons_table.buttons_table_info
        data = self.buttons_table.event_of_callback_query.data.decode()
        self.button.button_msg += btf.back_msg
        self.button.button_data = data[data.find('_', data.find('_') + 1) + 1:]  # get second path


        return self.button.get_button()


class GetAllButtons:

    def __init__(self, buttons_table: ButtonsTableOfDataFromDatabase, enable=False):
        self.buttons = []
        btf = buttons_table.buttons_table_info
        data = buttons_table.event_of_callback_query.data.decode()
        _k, _k_data, back_path = get_k_kdata_backpath_from_data(buttons_table.event_of_callback_query.data)
        get_all_list = db_get_all_smth(_k, _k_data)
        if not get_all_list:
            return
        for name, key_and_enable in get_all_list.items():
            # get path!!!!!!!!
            buttons_ = [Button.inline(f'{name}', f'{btf.key_sub}_{key_and_enable[0]}_{data}')]
            if enable:
                if key_and_enable[1]:
                    buttons_.append(Button.inline(_('✅ (click to disable)'), f'switch_{_k}_{key_and_enable[0]}_{data}'))
                if not key_and_enable[1]:
                    buttons_.append(Button.inline(_('❌ (click to enable)'), f'switch_{_k}_{key_and_enable[0]}_{data}'))
            self.buttons.append(buttons_)

    def create_button(self):
        return self.buttons


dict_for_back_buttons = {  # {название ключа: (куда возвращаться, название для кнопки back to , где искать ключ
    # для возврата) }
    'tickersofuser': ('usermenu', _('Menu of user '), '*'),
    'ticker': ('tickersofuser', _('Tickers of '), 'Ticker', 'key_ticker', 'key_user'),
    'tag': ('ticker', 'Ticker ', 'Tag', 'key_tag', 'key_ticker'),
}
dict_for_data_buttons = {
    'tickersofuser': ('ticker', _('Ticker'), 'key_user', ['key_ticker', 'ticker']),
    'ticker': ('tag', _('Tag'), 'key_ticker', ['key_tag', 'tag']),
    'tag': ('Tag',),
}


class ButtonsTable:
    title_msg_ = _('Nothing Title of Buttons Table')
    event_of_callback_query = None
    buttons_list = []
    buttons_table_info = None

    def __init__(self, event, type_buttons_of_key: TypeButtonsABC):
        self.event_of_callback_query = event
        self.buttons_table_info = type_buttons_of_key

    def __create_error_buttons_(self, error):
        self.title_msg_ = _('Error, data not found or not rights for that')
        ## button

    async def reaction_on_click(self, send_msg=False, function_of_react=None, *args, **kwargs):
        if not function_of_react:
            return await self.display_buttons(send_msg=send_msg)
        return await function_of_react(*args, **kwargs)

    async def display_buttons(self, send_msg=False):
        if send_msg:
            message = await self.event_of_callback_query.respond(f'{self.title_msg_}', buttons=self.buttons_list)
        else:
            message = await self.event_of_callback_query.edit(f'{self.title_msg_}', buttons=self.buttons_list)
        return message


class ButtonsTableOfDataFromDatabase(ButtonsTable):
    name_of_key = ''
    database_key = ''
    buttons_list = []

    def __init__(self, event, type_buttons_of_key):
        super().__init__(event, type_buttons_of_key)
        self.title_msg_ = self.get_title()

        self.buttons_list = []
        for mbutton in self.buttons_table_info.available_control_buttons:
            self.buttons_list.append([mbutton(self).create_button()])
        if self.buttons_table_info.get_all:
            buttons_ = GetAllButtons(self, enable=self.buttons_table_info.enable).create_button()
            self.buttons_list.extend(buttons_)

    def get_title(self):
        if self.buttons_table_info.key in ['tickers', 'parsechannels', 'sharechannels']:
            return self.buttons_table_info.title_msg_
        event = self.event_of_callback_query
        _k, _k_data, back_path = get_k_kdata_backpath_from_data(event.data)
        res_db = db_get_1(_k, _k_data)
        if not res_db:
            return []
        name_of_k = res_db.pop()
        return self.buttons_table_info.title_msg_ + ' ' + name_of_k

    def _create_back_button(self):

        self.back_button.button_msg += self.buttons_table_info.back_msg
        if self.buttons_table_info.key == 'usermenu':
            self.back_button.button_data = self.user_logging + '_' + 'Usermenu'
        else:
            get_list = get_smth_from_database(self.event_of_callback_query.sender_id,
                                              self.user_logging,
                                              self.buttons_table_info.back_key_db_where_search,
                                              {self.button_back_info[3]: self.database_key},
                                              [self.button_back_info[4]],
                                              only_one_result=True)
            self.back_button.button_data = self.user_logging + '_' + self.button_back_info[0] + '_' + get_list[0]

    def get_buttons(self):
        self.buttons_list.append(
            [self.back_button.get_button()],
        )
        return self.buttons_list

    def send_message(self):
        pass

    def edit_message(self):
        pass

    def get_list_with_userlogging_and_key_and_keydata_from_eventdata(data):
        return data.decode().split('_', maxsplit=2)


class TypeButtonsABC(ABC):
    available_control_buttons = None
    get_all = None
    key = None
    enable = None
    pass


dict_for_back_buttons = {  # {название ключа: (куда возвращаться, название для кнопки back to , где искать ключ
    # для возврата) }
    'tickersofuser': ('usermenu', _('Menu of user '), '*'),
    'ticker': ('tickersofuser', _('Tickers of '), 'Ticker', 'key_ticker', 'key_user'),
    'tag': ('ticker', _('Ticker '), 'Tag', 'key_tag', 'key_ticker'),
}


class TagButtons(TypeButtonsABC):
    key = 'tag'
    title_msg_ = ' Tag is'
    buttons_table = ButtonsTableOfDataFromDatabase
    available_control_buttons = (BackButton, EditButton, DeleteButton)
    back_msg = _(' Ticker')
    edit_msg = _(' Tag')
    delete_msg = _(' Tag')
    get_all = False
    enable = False

    # end
    # end
    # end
    # end
    # end
    # end
    # end
    # end
    # end
    # end
    # back_msg = _('Tickers of user')
    # back_db_base = 'Tag'
    # btf.back_db_rescolumn = 'key_ticker'
    #
    # buttons_table = ButtonsTableOfDataFromDatabase
    # title_msg_ = 'Tag is'
    #
    #
    # back_msg = _('Tickers of user')  ## 'back to ticker'
    # back_key = 'ticker'
    # back_key_db_where_search = 'Tag'
    # back_key_db_filter = 'НЕ помню нужно свпомнить'
    #
    # def __new__(cls, *args, **kwargs):
    #     return
    #
    # def get_title(self):
    #     pass
    #
    # buttons_list = []


class TagsButtons(TypeButtonsABC):
    key = 'tags'
    title_msg_ = _(' Taker is')
    buttons_table = ButtonsTableOfDataFromDatabase
    available_control_buttons = (BackButton, AddNewButton, EditButton, DeleteButton)
    back_msg = _(' Tickers')
    add_msg = _(' Tag')
    edit_msg = _(' Ticker name')
    delete_msg = _(' Ticker')
    key_sub = 'tag'
    get_all = True
    enable = True

    def __new__(cls, *args, **kwargs):
        return


class TickersButttons(TypeButtonsABC):
    key = 'tickers'
    title_msg_ = _(' Takers of ')
    buttons_table = ButtonsTableOfDataFromDatabase
    available_control_buttons = (BackButton, AddNewButton)
    back_msg = _(' User')
    add_msg = _(' Ticker')
    key_sub = 'tags'
    get_all = True
    enable = True

    def __new__(cls, *args, **kwargs):
        return


class ParseChannelBattons(TypeButtonsABC):
    key = 'parsechannel'
    title_msg_ = _(' Parse channel')
    buttons_table = ButtonsTableOfDataFromDatabase
    available_control_buttons = (BackButton, EditButton, DeleteButton)
    back_msg = _(' Parse channels of user')
    edit_msg = _(' Parse channel')
    delete_msg = _(' Parse channel')
    get_all = False
    enable = False

    def __new__(cls, *args, **kwargs):
        return


class ParseChannelsBattons(TypeButtonsABC):
    key = 'parsechannels'
    title_msg_ = _(' Parse channels of user')
    buttons_table = ButtonsTableOfDataFromDatabase
    available_control_buttons = (BackButton, AddNewButton)
    back_msg = _(' User')
    add_msg = _(' Parse channel')
    key_sub = 'parsechannel'
    get_all = True
    enable = True

    def __new__(cls, *args, **kwargs):
        return


class ShareChannelBattons(TypeButtonsABC):
    key = 'sharechannel'
    title_msg_ = _(' Share channel')
    buttons_table = ButtonsTableOfDataFromDatabase
    available_control_buttons = (BackButton, EditButton, DeleteButton)
    back_msg = _(' Share channels of user')
    edit_msg = _(' Share channel')
    delete_msg = _(' Share channel')
    get_all = False
    enable = False

    def __new__(cls, *args, **kwargs):
        return


class ShareChannelsBattons(TypeButtonsABC):
    key = 'sharechannels'
    title_msg_ = _(' Parse channels of user')
    buttons_table = ButtonsTableOfDataFromDatabase
    available_control_buttons = (BackButton, AddNewButton)
    back_msg = _(' User')
    add_msg = _(' Share channel')
    key_sub = 'sharechannel'
    get_all = True
    enable = True

    def __new__(cls, *args, **kwargs):
        return


# _________________________________________________________________________________________________________________________________________________________________________
# bot`s handlers
# BOT_handler_my_users (command /myusers) in button`s handler Bot_handler_button_myuseres


@events.register(events.NewMessage(pattern='/set'))
async def BOT_handler_set_data(event):
    _ = CI[event]._
    try:
        list_ = event.message.text.split(maxsplit=2)
        if len(list_) < 2:
            raise NotCorrectExc
        set__, data = list_[0:2]
        setlist_ = list_[0].split('_', maxsplit=2)
        if len(setlist_) < 3:
            raise NotCorrectExc
        _, user_logging, arg = setlist_

        set_data(event.sender_id, user_logging, arg, data)
        await event.reply(f"Данные сохранены: session '{user_logging}':{arg}: {data}")
    except NotCorrectExc as e:
        await event.reply(f'{e}\n'
                          'Введена неправильная команда.\nExample: "/set_username_*** value"\n*** - one of:\n for '
                          'start script;\n{} for other set')
    except UserNotFoundExc as e:
        await event.reply(f'Пользователь не найден\n'
                          f'Чтобы создать ползователя используйте команду {command_dict["add_user"]}')
    except:
        logger.error('Что-то пошло не так', exc_info=True)
        await event.reply('Что-то пошло не так')
        raise
    finally:
        raise events.StopPropagation


@events.register(events.NewMessage(pattern='/get'))
async def BOT_handler_get_data(event):
    _ = CI[event]._
    try:
        getlist_ = event.message.text.split(maxsplit=1)[0].split('_', maxsplit=2)
        if len(getlist_) < 3:
            raise NotCorrectExc
        _, user_logging, arg = getlist_

        value_arg = get_data_for_str_request(event.sender_id, user_logging, arg)
        await event.reply(f"username '{user_logging}': {arg}:: {value_arg}")
    except NotCorrectExc as e:
        await event.reply(f'{e}\nВведена неправильная команда.\n'
                          f'Example: "/get_username_***"\n*** - one of: {command_get_list}')

    except UserNotFoundExc as e:
        await event.reply(f'Пользователь не найден\n'
                          f'Чтобы создать ползователя используйте команду {command_dict["add_user"]}')

    except:
        logger.error('Что-то пошло не так', exc_info=True)
        await event.reply('Что-то пошло не так')
        raise
    finally:
        raise events.StopPropagation


@events.register(events.NewMessage(pattern='/add'))
async def BOT_handler_add_data(event):
    _ = CI[event]._
    try:
        list_ = event.message.text.split()
        if len(list_) < 2:
            raise NotCorrectExc
        add__, data = list_[0], list_[1:]
        addlist_ = add__.split('_', maxsplit=2)
        if len(addlist_) != 3:
            raise NotCorrectExc
        _, user_logging, arg = addlist_

        for i in data:
            set_data(event.sender_id, user_logging, arg, i)
        await event.reply(f"Данные сохранены: username '{user_logging}':{arg}: {data}")

    except NotCorrectExc as e:
        await event.reply(f'{e}\nВведена неправильная команда.\n'
                          f'Example: "/add_username_*** value"\n*** - one of:\n{command_add_list}')
    except DataDuplicateExc as e:
        await event.reply(f'{e}')

    except UserNotFoundExc as e:
        await event.reply(f'Пользователь не найден\n'
                          f'Чтобы создать ползователя используйте команду {command_dict["add_user"]}')

    except:
        logger.error('Что-то пошло не так', exc_info=True)
        await event.reply('Что-то пошло не так')
        raise
    finally:
        raise events.StopPropagation


@events.register(events.NewMessage(pattern='/start_script'))
async def BOT_handler_start_script(event):
    _ = CI[event]._
    if all((cfg.api_hash, cfg.api_id, cfg.my_channel_id)):
        telegram_parse.add_client_to_loop(event.client, event.sender_id)
        await event.reply(_("Start!"))
    raise events.StopPropagation


@events.register(events.NewMessage(pattern='/cancel|/start'))
@fsm_decor(st.ActionChangeStateToEcho(st.StateEcho))
async def BOT_handler_cancel(event):
    _ = CI[event]._
    if event.text == '/start':
        await BOT_handler_language_command(event, stop_propagation=False)
    await event.client.send_message(event.sender_id, _('Echo mod active'))
    return []


# _______________________________________________________
# state buttons
class BuilderButtonsTable:
    dict_for_type_buttons_by_key = {}
    for cls in globals()['TypeButtonsABC'].__subclasses__():
        dict_for_type_buttons_by_key[cls.key] = cls

    def __init__(self, event):
        self.event = event

    def build(self):
        key = self.get_key_for_button_key(self.event.data)
        type_buttons = self.dict_for_type_buttons_by_key[key]
        result = type_buttons.buttons_table(self.event, type_buttons)
        return result

    @staticmethod
    def get_key_for_button_key(data):
        return data.decode().split('_', maxsplit=2)[0]


# @events.register(events.CallbackQuery())
# async def test_all_callbackquerry(event):
#     await event.client.send_message(event.sender_id, 'GOOOD')
#
#     #button_table = BuilderButtonsTable(event).build()
#     #await button_table.reaction_on_click()
#     raise events.StopPropagation


@events.register(events.NewMessage(pattern='/myusers'))
@fsm_decor(st.ActionCommand())
async def BOT_handler_myusers_command(event, stop_propagation=True):
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


@events.register(events.CallbackQuery(pattern='myusers_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_myusers(event):
    _ = CI[event]._
    # localization.change_lang('ru_RU')
    users_list = get_all_users(event.sender_id)
    buttons = []
    if users_list:
        buttons = [Button.inline(f'{user_logging}', f'user_{user_logging}') for user_logging in users_list]
        buttons = list(split_(buttons, 2))
    buttons.append([Button.inline(_('🧑‍💻 Create new user'), 'newuser')])
    buttons.append([Button.inline(_('🧑‍💻 Add user to me'), 'adduser')])
    await event.edit(_('Choose a username from the list below:'), buttons=buttons)
    return [event.message_id]


# _________________________________________________________________________________________________________________________________________________________________________
# bot`s Conversations Create user

async def BOT_newuser_check_name(fun, args, kwargs):
    event = args[0]
    chat_info = CI[event]
    _ = chat_info._
    logging_user_name = event.text
    true_name, message_text = check_name_filters(event)
    if not true_name:
        chat_info.chat_state.next_sub_state = BOT_newuser_check_name
        message = await event.reply(message_text + _(' Enter new user logging name:'))
    else:
        chat_info.chat_state_data['logging_name'] = logging_user_name
        chat_info.chat_state.next_sub_state = BOT_newuser_enter_password
        message = await event.reply(message_text + _(' Enter your password:'))
    return [message.id, event.id]


async def BOT_newuser_enter_password(fun, args, kwargs):
    event = args[0]
    chat_info = CI[event]
    _ = chat_info._
    res = event.text
    hash_ = hashlib.sha256()
    salt = cfg.salt
    hash_.update((res + salt).encode('utf_8'))
    chat_info.chat_state_data['password'] = hash_.digest()
    chat_info.chat_state.next_sub_state = BOT_newuser_confirm_password
    message = await event.respond(_('Confirm your password:'))
    return [message.id, event.id]


async def BOT_newuser_confirm_password(fun, args, kwargs):
    event = args[0]
    chat_info = CI[event]
    _ = chat_info._
    res = event.text
    hash_confirm = hashlib.sha256()
    salt = cfg.salt
    hash_confirm.update((res + salt).encode('utf_8'))

    if hash_confirm.digest() != chat_info.chat_state_data['password']:
        chat_info.chat_state.next_sub_state = BOT_newuser_enter_password
        message = await event.respond(_('Different password. Try again. Enter your password:'))
        return [message.id, event.id]

    chat_info.chat_state.finish_and_change_state = True
    chat_info.chat_state.next_sub_state = BOT_newuser_create_user
    return [event.id]


async def BOT_newuser_create_user(fun, args, kwargs):
    event = args[0]
    chat_info = CI[event]
    _ = chat_info._
    user_logging = chat_info.chat_state_data['logging_name']
    add_new_user_to_database(user_logging, chat_info.chat_state_data['password'], event.sender_id)
    await event.respond(_('User {} WAS CREATED 🎉🎉🎉🎉').format(user_logging))
    chat_info.selected_user = user_logging
    msgs = await send_button_table_user(event, user_logging)
    return msgs


@events.register(events.NewMessage(pattern='/newuser'))
@events.register(events.CallbackQuery(pattern='newuser'))
@fsm_decor(st.ActionChangeStateToConversation(st.StateConversation, next_sub_state=BOT_newuser_check_name))
async def BOT_handler_button_create_user(event):
    _ = CI[event]._
    message = await event.respond(_('Enter new user logging name:'))
    return [message.id]


# _________________________________________________________________________________________________________________________________________________________________________


async def BOT_adduser_check_name(fun, args, kwargs):
    event = args[0]
    chat_info = CI[event]
    _ = chat_info._
    logging_user_name = event.text
    if not check_user_logging_name_for_correct(logging_user_name):
        message = await event.respond(_('User logging incorrect, not posyble. Try again:'))
        chat_info.chat_state.next_sub_state = BOT_adduser_check_name
        return [event.id, message.id]
    if check_user_logging_name_in_db(logging_user_name):
        message = await event.respond(_('No that user. Try again,'))
        chat_info.chat_state.next_sub_state = BOT_adduser_check_name
        return [event.id, message.id]

    chat_info.chat_state_data['logging_name'] = logging_user_name
    message = await event.respond(_('Good. Enter password:'))
    chat_info.chat_state.next_sub_state = BOT_adduser_confirm_password
    return [event.id, message.id]


async def BOT_adduser_confirm_password(fun, args, kwargs):
    event = args[0]
    chat_info = CI[event]
    _ = chat_info._
    res = event.text
    hash_confirm = hashlib.sha256()
    salt = cfg.salt
    hash_confirm.update((res + salt).encode('utf_8'))
    user_logging = chat_info.chat_state_data['logging_name']
    if hash_confirm.digest() != (db_get('User', ['user_password'], first=True, key_user=user_logging).pop()).pop():
        message = await event.respond(_('Not that password or logging name. Try again. Enter logging name of user:'))
        chat_info.chat_state.next_sub_state = BOT_adduser_check_name
        return [event.id, message.id]
    chat_info.chat_state.finish_and_change_state = True
    chat_info.chat_state.next_sub_state = BOT_adduser_add_user_to_chat
    return [event.id]


async def BOT_adduser_add_user_to_chat(fun, args, kwargs):
    event = args[0]
    chat_info = CI[event]
    _ = chat_info._
    user_logging = chat_info.chat_state_data['logging_name']
    add_user_to_telegram_id(user_logging, event.sender_id)
    await event.respond(_('User {} HAS BEEN ADDED 🎉🎉🎉🎉').format(user_logging))
    chat_info.selected_user = user_logging
    msgs = await send_button_table_user(event, user_logging)
    return msgs


@events.register(events.NewMessage(pattern='/adduser'))
@events.register(events.CallbackQuery(pattern='adduser'))
@fsm_decor(st.ActionChangeStateToConversation(st.StateConversation, next_sub_state=BOT_adduser_check_name))
async def BOT_handler_add_user(event):
    _ = CI[event]._
    message = await event.respond(_('Enter logging name of user:'))
    return [message.id]


# _________________________________________________________________________________________________________________________________________________________________________


async def send_button_table_user(event, user_logging):
    _ = CI[event]._
    header = _('Here it is {}! \n What do you want to do?').format(user_logging)
    buttons = [
        [Button.inline(_('Tickers'), f'tickers_{user_logging}_user_{user_logging}')],
        [Button.inline(_('Parse Channels'), f'parsechannels_{user_logging}_user_{user_logging}')],
        [Button.inline(_('Share Channels'), f'sharechannels_{user_logging}_user_{user_logging}')],
        [Button.inline(_('User Settings'), f'settings_{user_logging}')],
        [Button.inline(_('Change user'), 'myusers_')],
    ]
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(header, buttons=buttons)
        return [event.message_id]
    if isinstance(event, events.NewMessage.Event):
        message = await event.respond(header, buttons=buttons)
        return [message.id]


@events.register(events.NewMessage(pattern='/usermanager'))
@fsm_decor(st.ActionCommand())
async def BOT_handler_usermanager_command(event):
    _ = CI[event]._
    user_logging = CI[event].selected_user
    res = await send_button_table_user(event, user_logging)
    return res


@events.register(events.CallbackQuery(pattern='user_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_user(event):
    _ = CI[event]._
    user_logging = get_list_with_key_and_keydata_from_eventdata(event.data).pop()
    if user_logging:
        CI[event].selected_user = user_logging
    else:
        user_logging = CI[event].selected_user
    return await send_button_table_user(event, user_logging)


# _________________________________________________________________________________________________________________________________________________________________________
dict_smth_for_buttons_table = {
    'tickers': {
        'back': _('« Back to User'),
        'data_back'
        'add': 2}
}


# tickers: back, new, enable
# tags: back, new, edit, delete, enable tag
# tag: back, edit, delete
# shar_channels: back, new, enable chan
# shar_channel: back, edit, delete
# parse_channels: back, new, enable chan
# parse_channel: back, edit, delete


# DBOT_handler_button_tickers = events.register(events.CallbackQuery(pattern='tickers_|tags_'))(BOT_handler_button_tickers)
# @events.register(events.CallbackQuery(pattern='tickers_|tags_'))    # Добавлено ниже
# @fsm_decor(st.ActionCallBack())   # Добавлено ниже
async def BOT_handler_button_tickers(event, stop_propagation=True, send_msg=False):
    _ = CI[event]._
    # event data have struct: nowcomand_back_key_data_back_key_data_...._myusers_
    builder = BuilderButtonsTable(event)
    buttons_table = builder.build()
    message = await buttons_table.reaction_on_click(send_msg=send_msg)
    return [message.id]
    # _k, _k_data = get_list_with_key_and_keydata_from_eventdata(event.data)
    # user_logging = CI[event].selected_user
    # get_all_list = db_get_all_smth(_k, _k_data)
    # buttons = [
    #     [Button.inline(_('« Back to User'), f'user_')],
    #     [Button.inline(_('Add New Tickers'), f'add_ticker_{CI[event].selected_user}')]]
    # buttons_ = []
    # if tickers_list:
    #     for ticker in tickers_list:
    #         buttons_ = [Button.inline(f'{ticker.ticker}', f'tags_{ticker.key_ticker}')]
    #         if ticker.enable:
    #             buttons_.append(Button.inline(_('✅ (click to disable)'), f'switch_ticker_{ticker.key_ticker}'))
    #         if not ticker.enable:
    #             buttons_.append(Button.inline(_('❌ (click to enable)'), f'switch_ticker_{ticker.key_ticker}'))
    #         buttons.append(buttons_)
    #     # buttons_ = [Button.inline(f'{ticker.ticker}', f'tags_{ticker.key_ticker}') for ticker in tickers_list]
    #     # buttons_ = [buttons_[:1], ] + list(split_(buttons_[1:], 3))
    # # buttons = buttons + buttons_
    # if send_msg:
    #     message = await event.respond(_('It is tickers of {} ! \n What do you want to do?').format(user_logging),
    #                                   buttons=buttons)
    # else:
    #     message = await event.edit(_('It is tickers of {} ! \n What do you want to do?').format(user_logging),
    #                                buttons=buttons)
    # return [message.id]


DBOT_handler_button_tickers = events.register(
    events.CallbackQuery(pattern='tickers_|tags_|tag_|parsechannels_|sharechannels_'))(
    fsm_decor(st.ActionCallBack())(BOT_handler_button_tickers))


@events.register(events.CallbackQuery(pattern='switch_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_switch_some(event):
    _ = CI[event]._
    _k, _k_data, back_path = comand_get_k_kdata_backpath_from_data(event.data)
    res = db_switch_some_for_user(_k, _k_data)
    if not res:
        await event.answer()
    else:
        event.query.data = back_path.encode(encoding='utf-8')
        message_id = await BOT_handler_button_tickers(event)
    return message_id


# _________________________________________________________________________________________________________________________________________________________________________
# add some new

async def BOT_handler_add_confirm(fun, args, kwargs):
    event = args[0]
    _ = CI[event]._
    user_logging = CI[event].selected_user
    _k = CI[event].chat_state_data['state_add_key']
    back_path = CI[event].chat_state_data['state_add_back_path']
    name_of_k = CI[event].chat_state_data['state_add_name_key']

    confirm_list_of_add = check_and_get_add_text(event.text)
    if not confirm_list_of_add:
        message = await event.respond(_(
            'False input, try again. Input new {}. Please use this format, max size of one 55:\nExample1\nexample2😃\n😃exaMple3'))
        return [event.id, message.id]
    CI[event].chat_state_data['state_add_data_list'] = confirm_list_of_add

    buttons = [[Button.inline(_('Yes, add'), f'addnextconfirmyes_{back_path}')],
               [Button.inline(_('No'), f'addnextconfirmno_{back_path}')]]
    message = await event.respond(
        _('Do you want add {0} to: \n{1}').format(name_of_key[_k] + ' ' + name_of_k, '\n'.join(confirm_list_of_add)),
        buttons=buttons)
    CI[event].chat_state.next_sub_state = BOT_handler_add_confirm_received_msg
    return [event.id]


async def BOT_handler_add_confirm_received_msg(fun, args, kwargs):
    event = args[0]
    _ = CI[event]._
    message = await event.respond(_('Press yes/no for confirm. Or enter /cancel for ....(help for translate) '))
    return [message.id, event.id]


# @events.register(events.CallbackQuery(pattern='addnextconfirmno_'))
# @fsm_decor(st.ActionCallBack())
# async def BOT_handler_add_confirm_no_and_finish(event):
#     CI[event].chat_state.finish_and_change_state = True
#     CI[event].chat_state.next_sub_state = BOT_handler_add_no_add
#     return []
#
#
# async def BOT_handler_add_no_add(fun, args, kwarg):
#     event = args[0]
#     _ = CI[event]._
#     event.query.data = CI[event].chat_state_data['back_path']
#     message_id = await BOT_handler_button_tickers(event, send_msg=True)
#     return message_id



@events.register(events.CallbackQuery(pattern='addnextconfirmyes_|addnextconfirmno_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_add_confirm_yes_and_finish(event):
    CI[event].chat_state.finish_and_change_state = True
    CI[event].chat_state_data['state_add_result_confirm'] = event.data.decode().split('_',maxsplit=1).pop(0)
    CI[event].chat_state.next_sub_state = BOT_handler_add_add
    return []


async def BOT_handler_add_add(fun, args, kwarg):
    event = args[0]
    _ = CI[event]._
    user_logging = CI[event].selected_user
    add_data_list = CI[event].chat_state_data['state_add_data_list']
    name_of_k = CI[event].chat_state_data['state_add_name_key']
    _k, _k_data, back_path = comand_get_k_kdata_backpath_from_data(event.data)

    if CI[event].chat_state_data['state_add_result_confirm'] == 'addnextconfirmyes':
        successfully_add = db_add_smth_for_user(_k, _k_data, add_data_list)
        if not successfully_add:
            await event.edit(_('Error add. Try again'))
        else:
            await event.edit(_('Great. To  add:\n {}').format('\n'.join(add_data_list)))
    event.query.data = back_path.encode(encoding='utf-8')
    message_id = await BOT_handler_button_tickers(event, send_msg=False)
    return message_id


@events.register(events.CallbackQuery(pattern='add_'))
@fsm_decor(st.ActionChangeStateToConversation(st.StateConversation, next_sub_state=BOT_handler_add_confirm))
async def BOT_handler_button_add_tickers_input(event):
    _ = CI[event]._
    _k, _k_data, back_path = comand_get_k_kdata_backpath_from_data(event.data)
    # /get name_of_k
    if _k in ['tickers', 'parsechannels', 'sharechannels']:
        name_of_k = CI[event].selected_user
    else:
        res_db = db_get_1(_k, _k_data)
        if not res_db:
            return []
        name_of_k = res_db.pop()
    # get name_of_k/
    message = await event.respond(
        _('Input new {} to\n{}\n Please use this format, max size of one 55:\nExample1\nexample2😃\n😃exaMple3').format(name_of_key[_k], name_of_k))
    # CI[event].chat_state_data['state_add_key'] = _k
    # CI[event].chat_state_data['state_add_key_data'] = _k_data
    CI[event].chat_state_data['state_add_name_key'] = name_of_k
    CI[event].chat_state_data['state_add_key'] = _k
    CI[event].chat_state_data['state_add_back_path'] = '_'.join([_k, _k_data, back_path])

    return [message.id]


# _________________________________________________________________________________________________________________________________________________________________________


# @events.register(events.CallbackQuery(pattern='tags_'))
# async def BOT_handler_button_tags(event):
#     _ = CI[event]._
#     key_ticker = get_list_with_key_and_keydata_from_eventdata(event.data)
#     buttons = [
#         [Button.inline(_('« Back to User'), f'user_{user_logging}')],
#         [Button.inline(_('Add New Tickers'), f'addticker_{user_logging}')],
#         [Button.inline(_('Delete Tickers'), f'delticker_{user_logging}')],
#     ]
#
#
# @events.register(events.CallbackQuery(pattern='parsechannels_'))
# async def BOT_handler_button_parsechannels(event):
#     _ = CI[event]._
#     pass
#
#
# @events.register(events.CallbackQuery(pattern='sharechannels_'))
# async def BOT_handler_button_sharechannels(event):
#     _ = CI[event]._
#     pass

# _________________________________________________________________________________________________________________________________________________________________________
# log out user

@events.register(events.CallbackQuery(pattern='conflogout'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_log_out_user_confirm(event):
    _ = CI[event]._
    logging_user_name = CI[event].selected_user
    buttons = [[Button.inline(_('Yes, logout from'), 'confirmlogout')],
               [Button.inline(_('No, i misclicked'), 'settings_')],
               [Button.inline(_(' « Back to setting'), 'settings_')]]
    import random
    await event.edit(_('You are about to logout from {}. Is that correct?').format(logging_user_name),
                     buttons=random.shuffle(buttons))  ## not show buttons
    return [event.message_id]


@events.register(events.CallbackQuery(pattern='confirmlogout'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_log_out_user_confirm2(event):
    _ = CI[event]._
    logging_user_name = CI[event].selected_user
    buttons = [[Button.inline(_('Yes, i am sure 100%'), 'logout')],
               [Button.inline(_('No, i misclicked'), 'settings_')],
               [Button.inline(_(' « Back to setting'), 'settings_')]]
    await event.edit(_('You are about to logout from {}. Is that correct?').format(logging_user_name), buttons=buttons)
    return [event.message_id]


@events.register(events.CallbackQuery(pattern='logout'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_log_out_user(event):
    _ = CI[event]._
    logging_user_name = CI[event].selected_user
    CI[event].logout()
    buttons = [[Button.inline(_(' « Back to my users'), 'myusers_')]]
    await event.edit(_('You logout from {}.').format(logging_user_name), buttons=buttons)
    return [event.message_id]





# _________________________________________________________________________________________________________________________________________________________________________
# some delete

@events.register(events.CallbackQuery(pattern='confirmdelete_|confdelete_|deleting_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_delete_confirm(event):
    _ = CI[event]._
    logging_user_name = CI[event].selected_user
    # при confdelete_|deleting_ другие эвенты и даты
    _k, _k_data, back_path = comand_get_k_kdata_backpath_from_data(event.data)
    path = '_'.join([_k, _k_data, back_path])
    res_db = db_get_1(_k, _k_data)
    if not res_db:
        return []
    name_of_k = res_db.pop()
    if event.data.decode().startswith('deleting_'):
        res_db = db_del_1(_k, _k_data)
        await event.client.delete_messages(event.chat_id, [event.message_id])
        if res_db:
            await event.respond(_('Was deleted: \n{}').format(name_of_k))
        else:
            await event.respond(_('Dont DELETED. TRY AGAIN ‼️'))
        event.query.data = path.split('_', maxsplit=2).pop().encode('utf_8')
        message_id = await BOT_handler_button_tickers(event, send_msg=True)
        return message_id
    if event.data.decode().startswith('confirmdelete_'):
        buttons = [[Button.inline(_('Yes, delete it'), f'confdelete_{path}')]]
    if event.data.decode().startswith('confdelete_'):
        buttons = [[Button.inline(_('Yes, i am sure 100%'), f'deleting_{path}')]]
    buttons.append([Button.inline(_('No, i misclicked'), f'{path}')])
    buttons.append([Button.inline(_(' « Back'), f'{path}')])

    # import random
    # random.shuffle(buttons)
    await event.edit(_('You are about to delete:\n{}\n . Is that correct?').format(name_of_k),
                     buttons=buttons)  ## not show buttons
    return [event.message_id]
# _________________________________________________________________________________________________________________________________________________________________________


@events.register(events.CallbackQuery(pattern='deleteuser'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_deleteuser_confirm(event):
    _ = CI[event]._
    logging_user_name = CI[event].selected_user
    buttons = [[Button.inline(_('Yes, logout from'), '')],
               [Button.inline(_('No, i misclicked'), 'settings_')],
               [Button.inline(_(' « Back to setting'), 'settings_')]]
    await event.edit(_('You are about to logout from {}. Is that correct?').format(logging_user_name), buttons=buttons)
    return [event.message_id]


@events.register(events.CallbackQuery(pattern='settings_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_settings(event):
    _ = CI[event]._
    buttons = [[Button.inline(_('Log out user'), 'conflogout')],
               [Button.inline(_('Delete user'), 'deluser')],
               [Button.inline(_('Change language'), 'language_')],
               [Button.inline(_('« Back to user manager'), 'user_')]]
    await event.edit(_('Settings'), buttons=buttons)
    return [event.message_id]


@events.register(events.CallbackQuery(pattern='language_|languagecommand_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_languages(event):
    data_key, language = event.data.decode().split('_', maxsplit=1)
    if language and not CI[event].change_language(language):
        await event.answer()
        return [event.message_id]
    # кнопки ниже одинаковы для всех и их можно гденибудь хранить
    _ = CI[event]._
    buttons = []
    for k, v in localization.LANGUAGES.items():
        buttons.append([Button.inline(_('{}').format(v), f'{data_key}_{k}')])
    if data_key == 'language':
        buttons.append([Button.inline(_('« Go to user manager'), 'user_')])
    try:
        await event.edit(_('Choose language:'), buttons=buttons)
    except MessageNotModifiedError:
        await event.answer()
    return [event.message_id]


@events.register(events.NewMessage(pattern='/language'))
@fsm_decor(st.ActionCommand())
async def BOT_handler_language_command(event, stop_propagation=True):
    # кнопки ниже одинаковы для всех и их можно гденибудь хранить
    _ = CI[event]._
    buttons = []
    for k, v in localization.LANGUAGES.items():
        buttons.append([Button.inline(_('{}').format(v), f'languagecommand_{k}')])
    message = await event.respond(_('Choose language:'), buttons=buttons)
    return [message.id]


# @events.register(events.CallbackQuery(pattern='changelang_'))
# async def BOT_handler_button_change_language(event):
#     language = event.data.decode().split('_', maxsplit=1)[1]
#     if language in localization.LANGUAGES.keys():
#         CI[event].change_language(language)
#     await BOT_handler_button_languages(event)
#     # raise events.StopPropagation


# Wrong data in button
@events.register(events.CallbackQuery)
async def BOT_handler_wrong_data_for_button(event):
    _ = CI[event]._
    await event.client.send_message(event.sender_id, _('WrongCallbackQuery'))
    raise events.StopPropagation


# Echo handlers
@events.register(events.NewMessage(incoming=True))
@fsm_decor(st.ActionMassage())
async def BOT_handler_echo(event):
    _ = CI[event]._
    await event.reply(_('Sorry, I am not allowed to talk to you'))
    # m = await event.respond('!pong')
    # await asyncio.sleep(5)
    # await event.client.delete_messages(event.chat_id, {event.id, m.id})
    # raise events.StopPropagation
    return []


@events.register(events.InlineQuery)
async def handler(event):
    builder = event.builder

    # Two options (convert user text to UPPERCASE or lowercase)
    await event.answer([
        builder.article('UPPERCASE', text=event.text.upper()),
        builder.article('lowercase', text=event.text.lower()),
    ])


@events.register(events.NewMessage)
async def BOT_admin_handler_echo(event):
    await event.client.send_message(event.sender_id, 'Welcome', buttons=[
        # # Button.text('Thanks!', resize=True, single_use=True),
        # Button.request_phone('Send phone'),
        # Button.request_location('Send location'),
        # # Button.inline('Button.inline', data='button.inline.data'),
        Button.switch_inline('SWITCH INLINE', 'SOME SWITCH')

    ])
    await event.client.send_message(event.sender_id, 'A single button, with "clk1" as data',
                                    buttons=Button.inline('Click me', b'clk1'))
    await event.reply(event.text)
    raise events.StopPropagation


parse_bot_users_state_fsm = st.ParseBotUsersStateFSM()

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
from handlers.tools.chatssettings import CI, ExceptionUserNotSelectedSendAllUsers, ExceptionNotFindInDB
from handlers.tools import states as st
from abc import abstractmethod, ABC
import asyncio
import telethon.events

# ______________________________________________________________________________________________________________________
# import function of database
from Database.database import get_all_users, check_user_logging_name_in_db, \
    add_new_user_to_database, add_user_to_telegram_id, \
    db_get, db_add_smth_for_user, db_switch_some_for_user, db_del, db_del_1, db_get_all_smth, db_get_1
# import exception of database
from Database.database import NotCorrectExc, DataDuplicateExc, UserNotFoundExc

# ____________________________________________________________
# add my logger
logger = my_logger.get_logger(__name__)

# ____________________________________________________________
# any static
parse_bot_users_state_fsm = st.ParseBotUsersStateFSM()
MAX_SIZE_ADD = 55


# ____________________________________________________________
# any dicts


# command_dict = {
#     'add_user': '/add_user',
#     'my_users': '/myusers'
# }

# dontUSE_dict_for_back_buttons = {
#     'user_': 'myusers',
#     'tickers_': 'user_',
#     'parsechannels_': 'user_',
#     'sharechannels_': 'user_',
#     'settings_': 'user_',
#     'tags_': 'tickers_',
# }

# users_setting = {}
# value_of_key = {
#     'tickers': _('Ticker'),
#     'tags': _('Ticker'),
#     'tag': _('Tag'),
#     'pchs': _('Parsechannel'),
#     'shchs': _('Sharechannel'),
#
# }


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
def get_key_for_button_key(event):
    if isinstance(event, events.NewMessage.Event):
        key = event.text[1:].split(' ').pop(0)
        if key not in ['usermanager']:
            raise Exception('not command in used')
        return key
    elif isinstance(event, events.CallbackQuery.Event):
        return event.data.decode().split('_', maxsplit=2)[0]


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


class ButtonOfTabale(ABC):
    @abstractmethod
    def create_button(buttons_table):
        pass


class DeleteButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        button = MButton(buttons_table._('Delete this'), 'confirmdelete_')
        buttons_table = buttons_table
        btf = buttons_table.buttons_table_info
        button.button_msg += buttons_table._(btf.delete_msg)
        return [[button.get_button()]]

    @abstractmethod
    def delete_msg(self):
        pass


class AddNewButton(ButtonOfTabale, ABC):
    # def __init__(self, buttons_table):
    #     self.button = MButton(buttons_table._('Add new'), 'add_')
    #     self.buttons_table = buttons_table

    @staticmethod
    def create_button(buttons_table):
        button = MButton(buttons_table._('Add new'), 'add_')
        btf = buttons_table.buttons_table_info
        button.button_msg += buttons_table._(btf.add_msg)
        # data = self.buttons_table.event_of_callback_query.data.decode()
        # spl = data.split('_', maxsplit=2)
        # self.button.button_data += f'{spl[0]}_{spl[1]}_{data}'     may be is not use (key is 'add_', data in path)
        return [[button.get_button()]]

    @abstractmethod
    def add_msg(self):
        pass

    @abstractmethod
    def fist_state_of_conversation():
        pass

    @abstractmethod
    def add_to_msg(self):
        pass

    @staticmethod
    async def base_add_state_of_conversation(event, _k, _k_data, value_of_k):
        message = await event.respond(
            _(
                dict_for_type_buttons_by_key[_k].example.format(
                _(dict_for_type_buttons_by_key[_k].add_msg),
                _(dict_for_type_buttons_by_key[_k].add_to_msg),
                value_of_k)
            )
        )
        return message


class SwitchEnableButton:
    def __init__(self):
        pass


class EditButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        button = MButton(buttons_table._('Edit this'), 'edit_')
        btf = buttons_table.buttons_table_info
        button.button_msg += buttons_table._(btf.edit_msg)
        return [[button.get_button()]]

    @abstractmethod
    def edit_msg(self):
        pass


class BackButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        button = MButton(buttons_table._('« Back to'))
        btf = buttons_table.buttons_table_info
        button.button_msg += buttons_table._(btf.back_msg)
        button.button_data = CI[buttons_table.event_of_callback_query].get_back_path()  # get second path
        return [[button.get_button()]]

    @abstractmethod
    def back_msg(self):
        pass


class TickersButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        button = MButton(buttons_table._('Tickers'), 'tickers_')
        event = buttons_table.event_of_callback_query
        button.button_data += CI[event].selected_user
        return [[button.get_button()]]


class ParseChannelsButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        button = MButton(buttons_table._('ParseChannels'), 'pchs_')
        event = buttons_table.event_of_callback_query
        button.button_data += CI[event].selected_user
        return [[button.get_button()]]


class ShareChannelsButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        button = MButton(buttons_table._('ShareChannels'), 'shchs_')
        event = buttons_table.event_of_callback_query
        button.button_data += CI[event].selected_user
        return [[button.get_button()]]


class SettingsButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        return [[MButton(buttons_table._('Settings'), 'settings_').get_button()]]


class MyUsersButton(ButtonOfTabale, ABC):
    @staticmethod
    def create_button(buttons_table):
        return [[MButton(buttons_table._('Change user'), 'myusers_').get_button()]]


class LogOutUserButton(ButtonOfTabale, ABC):
    @staticmethod
    def create_button(buttons_table):
        return [[MButton(buttons_table._('Log out user'), 'conflogout_').get_button()]]


class DeleteUserButton(ButtonOfTabale, ABC):
    @staticmethod
    def create_button(buttons_table):
        return [[MButton(buttons_table._('Delete user'), 'deluser').get_button()]]


class LanguageButton(ButtonOfTabale):
    @staticmethod
    def create_button(buttons_table):
        return [[MButton(buttons_table._('Change language'), 'language_').get_button()]]


class GetAllButton(ButtonOfTabale, ABC):

    @staticmethod
    def create_button(buttons_table):
        buttons = []
        btf = buttons_table.buttons_table_info
        _k, _k_data, value_of_k = CI[buttons_table.event_of_callback_query].get_var_of_last_path()

        get_all_list = db_get_all_smth(_k, _k_data)
        if not get_all_list:
            return []
        for value, key_and_enable in get_all_list.items():
            buttons_ = [Button.inline(f'{value}', f'{btf.key_sub}_{key_and_enable[0]}_')]
            if btf.enable_switch:
                if key_and_enable[1]:
                    buttons_.append(
                        Button.inline(buttons_table._('✅ (click to disable)'), f'switch_{_k}_{key_and_enable[0]}'))
                if not key_and_enable[1]:
                    buttons_.append(
                        Button.inline(buttons_table._('❌ (click to enable)'), f'switch_{_k}_{key_and_enable[0]}'))
            buttons.append(buttons_)
        return buttons

    @abstractmethod
    def key_sub(self):
        pass

    @abstractmethod
    def enable_switch(self):
        pass



class ButtonsTable:
    title_msg_t = _('Nothing Title of Buttons Table')
    error_msg = None

    def __init__(self, event, type_buttons_of_key: ButtonsTableInfoABC):
        self.event_of_callback_query = event
        self.buttons_table_info = type_buttons_of_key

    def __create_error_buttons_(self, error):
        self.title_msg_t = _('Error, data not found or not rights for that')
        ## button

    async def reaction_on_click(self, send_msg=False, function_of_react=None, *args, **kwargs):
        if not function_of_react:
            return await self.display_buttons(send_msg=send_msg)
        return await function_of_react(*args, **kwargs)

    async def display_buttons(self, send_msg=False):
        if self.error_msg is not None:
            message = await self.event_of_callback_query.respond(self.error_msg)
            return []
        if send_msg:
            message = await self.event_of_callback_query.respond(f'{self.title_msg_t}', buttons=self.buttons_list)
        else:
            message = await self.event_of_callback_query.edit(f'{self.title_msg_t}', buttons=self.buttons_list)
        return [message.id]


class ButtonsTableOfDataFromDatabase(ButtonsTable):

    def __init__(self, event, type_buttons_of_key, full_data):
        super().__init__(event, type_buttons_of_key)
        self._ = CI[event]._
        # user_logging = CI[event].selected_user
        # update path
        try:
            CI[event].update_path(full_data, self.buttons_table_info.key)
            if callable(getattr(self.buttons_table_info, 'do_smth', None)):
                getattr(self.buttons_table_info, 'do_smth')(event)
        except ExceptionNotFindInDB as ex:
            self.error_msg = str(ex)
            return

        user_logging = CI[event].selected_user
        self.title_msg_t = self.get_title()
        self.buttons_list = []
        for mbutton in self.buttons_table_info.__class__.__bases__[1:]:
            self.buttons_list.extend(mbutton.create_button(self))
        # for mbutton in self.buttons_table_info.available_control_buttons: # ту на до будет поменять
        #     self.buttons_list.append([mbutton(self).create_button()])
        # # get all from db
        # if getattr(self.buttons_table_info, 'get_all', False):
        #     buttons_ = GetAllButtons(self, enable_switch=self.buttons_table_info.enable_switch).create_button()
        #     self.buttons_list.extend(buttons_)

    def get_title(self) -> str:

        if self.buttons_table_info.key in ['usermanager', 'user', 'settings']:
            return self._(self.buttons_table_info.title_msg_).format(CI[self.event_of_callback_query].selected_user)
        return self._(self.buttons_table_info.title_msg_).format(CI[self.event_of_callback_query].path[-1].value_of_k)


class ButtonsTableInfoABC(ABC):
    @abstractmethod
    def key(self):
        pass

    @abstractmethod
    def title_msg_(self):
        pass

    @abstractmethod
    def buttons_table(self):
        pass
    # available_control_buttons = None
    # get_all = None
    # key = None
    # enable_switch = None


class TagButtonsTable(ButtonsTableInfoABC, BackButton, EditButton, DeleteButton):
    key = 'tag'
    title_msg_ = _(' Tag is {}')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, EditButton, DeleteButton)
    back_msg = _(' Ticker')
    edit_msg = _(' Tag')
    delete_msg = _(' Tag')


class TagsButtonsTable(ButtonsTableInfoABC, BackButton, AddNewButton, EditButton, DeleteButton, GetAllButton):
    key = 'tags'
    title_msg_ = _(' Tags of {}')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, AddNewButton, EditButton, DeleteButton)
    back_msg = _(' Tickers')
    add_msg = _(' Tag')
    add_to_msg = _(' Ticker')
    fist_state_of_conversation = AddNewButton.base_add_state_of_conversation
    example = 'Input new {} to {}:\n{}\n Please use this format, max size of one 55:\nExample1\nexample2😃\n😃exaMple3'
    edit_msg = _(' Ticker name')
    delete_msg = _(' Ticker')
    key_sub = 'tag'
    enable_switch = True


class TickersButtonsTable(ButtonsTableInfoABC, BackButton, AddNewButton, GetAllButton):
    key = 'tickers'
    title_msg_ = _(' Takers of {}')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, AddNewButton)
    back_msg = _(' User')
    add_msg = _(' Ticker')
    add_to_msg = _(' User')
    fist_state_of_conversation = AddNewButton.base_add_state_of_conversation
    example = 'Input new {} to {}:\n{}\n Please use this format, max size of one 55:\nExample1\nexample2😃\n😃exaMple3'
    key_sub = 'tags'
    enable_switch = True


class ParseChannelButtonsTable(ButtonsTableInfoABC, BackButton, EditButton, DeleteButton):
    key = 'pch'
    title_msg_ = _(' Parse channel is {}')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, EditButton, DeleteButton)
    back_msg = _(' Parse channels of user')
    edit_msg = _(' Parse channel')
    delete_msg = _(' Parse channel')


class ParseChannelsButtonsTable(ButtonsTableInfoABC, BackButton, AddNewButton, GetAllButton):
    key = 'pchs'
    title_msg_ = _(' Parse channels of user: {}')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, AddNewButton)
    back_msg = _(' User')

    add_msg = _(' Parse channel')
    add_to_msg = _(' User')
    fist_state_of_conversation = AddNewButton.base_add_state_of_conversation
    example = 'Input new {} to {}:\n{}\n Please use this format, max size of one 55:\n333333\n233333\n123'

    key_sub = 'parsechannel'
    enable_switch = True


class ShareChannelBattonsTable(ButtonsTableInfoABC, BackButton, EditButton, DeleteButton):
    key = 'shch'
    title_msg_ = _(' Share channel is {}')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, EditButton, DeleteButton)
    back_msg = _(' Share channels of user')
    edit_msg = _(' Share channel')
    delete_msg = _(' Share channel')


class ShareChannelsButtonsTable(ButtonsTableInfoABC, BackButton, AddNewButton, GetAllButton):
    key = 'shchs'
    title_msg_ = _(' Parse channels of user: {}')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, AddNewButton)
    back_msg = _(' User')
    add_msg = _(' Share channel')
    add_to_msg = _(' User')
    fist_state_of_conversation = AddNewButton.base_add_state_of_conversation
    example = 'Input new {} to {}:\n{}\n Please use this format, max size of one 55:\n3333333\n233333\n123'

    key_sub = 'sharechannel'
    enable_switch = True


class UserManagerButtonsTable(ButtonsTableInfoABC, TickersButton, ParseChannelsButton, ShareChannelsButton,
                              SettingsButton):
    key = 'usermanager'
    title_msg_ = _('Here it is {}! \n What do you want to do?')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (TickersButton, ParseChannelsButton, ShareChannelsButton, SettingsButton)


class UserButtonsButtons(ButtonsTableInfoABC, TickersButton, ParseChannelsButton, ShareChannelsButton, SettingsButton):
    key = 'user'
    title_msg_ = _('Here it is {}! \n What do you want to do?')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (TickersButton, ParseChannelsButton, ShareChannelsButton, SettingsButton)

    @staticmethod
    def change_user(event):
        new_name = CI[event].path[-1].data
        CI[event].selected_user = new_name

    do_smth = change_user


class DelUserButtons(ButtonsTableInfoABC):
    key = 'deluser'
    title_msg_ = _('Here it is {}! \n What do you want to do?')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (TickersButton, ParseChannelsButton, ShareChannelsButton, SettingsButton)

    @staticmethod
    def change_user(event):
        new_name = CI[event].path[-1].data
        CI[event].selected_user = new_name

    do_smth = change_user


class SettingsButtonsTable(ButtonsTableInfoABC, BackButton, LogOutUserButton, DeleteUserButton, MyUsersButton,
                           LanguageButton):
    key = 'settings'
    title_msg_ = _('settings')
    back_msg = _(' User')
    buttons_table = ButtonsTableOfDataFromDatabase
    # available_control_buttons = (BackButton, LogOutUserButton, DeleteUserButton, MyUsersButton,LanguageButton,)


# _________________________________________________________________________________________________________________________________________________________________________
# bot`s handlers
# BOT_handler_my_users (command /myusers) in button`s handler Bot_handler_button_myuseres


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
    msgs = await BOT_handler_callback_buttons_table(event, send_msg=True, custom_data=f'user_{user_logging}')
    # msgs = await send_button_table_user(event, user_logging)
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
        [Button.inline(_('Tickers'), f'tickers_{user_logging}')],
        [Button.inline(_('Parse Channels'), f'parsechannels_{user_logging}')],
        [Button.inline(_('Share Channels'), f'sharechannels_{user_logging}')],
        [Button.inline(_('User Settings'), f'settings_{user_logging}')],
        [Button.inline(_('Change user'), 'myusers_')],
    ]
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(header, buttons=buttons)
        return [event.message_id]
    if isinstance(event, events.NewMessage.Event):
        message = await event.respond(header, buttons=buttons)
        return [message.id]


# @events.register(events.NewMessage(pattern='/usermanager'))
# @fsm_decor(st.ActionCommand())
# async def BOT_handler_usermanager_command(event):
#     _ = CI[event]._
#     user_logging = CI[event].selected_user
#     res = await send_button_table_user(event, user_logging)
#     return res


@events.register(events.CallbackQuery(pattern='user_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_user(event, buttons_table=None, stop_propagation=True):
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


# DBOT_handler_button_tickers = events.register(events.CallbackQuery(pattern='tickers_|tags_'))(BOT_handler_button_tickers)
# @events.register(events.CallbackQuery(pattern='tickers_|tags_'))    # Добавлено ниже
# @fsm_decor(st.ActionCallBack())   # Добавлено ниже
async def BOT_handler_callback_buttons_table(event, stop_propagation=True, send_msg=False, custom_data=None):
    _ = CI[event]._
    builder = BuilderButtonsTable(event)
    buttons_table = builder.build(full_data=custom_data)
    if isinstance(event, events.NewMessage.Event):
        send_msg = True
    message_id = await buttons_table.reaction_on_click(send_msg=send_msg)
    return message_id


DBOT_handler_button_tickers = events.register(
    events.CallbackQuery(pattern='tickers_|tags_|tag_|pchs_|shchs_|user_|usermanager_|settings_'))(
    fsm_decor(st.ActionCallBack())(
        BOT_handler_callback_buttons_table))
DBOT = events.register(
    events.NewMessage(pattern='/usermanager'))(
    fsm_decor(st.ActionCommand())(
        BOT_handler_callback_buttons_table))


@events.register(events.CallbackQuery(pattern='switch_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_switch_some(event):
    _ = CI[event]._
    __, _k, _k_data = event.data.decode().split('_', maxsplit=2)
    res = db_switch_some_for_user(_k, _k_data)
    if not res:
        await event.answer()
        return []
    else:
        event.query.data = CI[event].get_last_path().encode(encoding='utf-8')
        message_id = await BOT_handler_callback_buttons_table(event)
    return message_id


# _________________________________________________________________________________________________________________________________________________________________________
# add some new
# so so
# soso2 commit
# commit to new branch
# add new line to pull request
# yet one comment

async def BOT_handler_add_confirm(fun, args, kwargs):
    event = args[0]
    _ = CI[event]._
    user_logging = CI[event].selected_user
    _k, _k_data, value_of_k = CI[event].get_var_of_last_path(from_saved=True)

    confirm_list_of_add = check_and_get_add_text(event.text)
    if not confirm_list_of_add:
        message = await event.respond(_(
            'False input, try again. Input new {}. Please use this format, max size of one 55:\nExample1\nexample2😃\n😃exaMple3'))
        return [event.id, message.id]

    CI[event].chat_state_data['state_add_data_list'] = confirm_list_of_add
    buttons = [[Button.inline(_('Yes, add'), f'addnextconfirmyes_')],
               [Button.inline(_('No'), f'addnextconfirmno_')]]
    message = await event.respond(
        _('Do you want add to {}:\n{}\n{}\n').format(_(dict_for_type_buttons_by_key[_k].add_msg),
                                                     value_of_k,
                                                     '\n'.join(confirm_list_of_add)),
        buttons=buttons)
    CI[event].chat_state.next_sub_state = BOT_handler_add_confirm_received_msg
    return [event.id, message.id]


async def BOT_handler_add_confirm_received_msg(fun, args, kwargs):
    event = args[0]
    _ = CI[event]._
    message = await event.respond(_('Press yes/no for confirm. Or enter /cancel for ....(help for translate) '))
    return [message.id, event.id]


@events.register(events.CallbackQuery(pattern='addnextconfirmyes_|addnextconfirmno_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_add_confirm_and_finish(event):
    CI[event].chat_state.finish_and_change_state = True
    CI[event].chat_state_data['state_add_result_confirm'] = event.data.decode()
    CI[event].chat_state.next_sub_state = BOT_handler_add_finish
    return []


async def BOT_handler_add_finish(fun, args, kwarg):
    event = args[0]
    _ = CI[event]._
    user_logging = CI[event].selected_user
    add_data_list = CI[event].chat_state_data['state_add_data_list']
    _k, _k_data, value_of_k = CI[event].get_var_of_last_path(from_saved=True)

    if CI[event].chat_state_data['state_add_result_confirm'] == 'addnextconfirmyes_':
        successfully_add = db_add_smth_for_user(_k, _k_data, add_data_list) # add to db
        if not successfully_add:
            await event.respond(_('Error add. Try again'))
        else:
            await event.respond(_('Great. To {}: \n{}\n add {}:\n {}').format(
                _(dict_for_type_buttons_by_key[_k].add_to_msg),
                value_of_k,
                _(dict_for_type_buttons_by_key[_k].add_msg),
                '\n'.join(add_data_list)))
    event.query.data = CI[event].get_last_path(from_saved=True).encode(encoding='utf-8')
    message_id = await BOT_handler_callback_buttons_table(event, send_msg=True)
    return message_id


@events.register(events.CallbackQuery(pattern='add_'))
@fsm_decor(st.ActionChangeStateToConversation(st.StateConversation, next_sub_state=BOT_handler_add_confirm))
async def BOT_handler_button_add(event):
    _ = CI[event]._
    _k, _k_data, value_of_k = CI[event].get_var_of_last_path()
    CI[event].save_path_for_state()
    message = await dict_for_type_buttons_by_key[_k].__class__.fist_state_of_conversation(event, _k, _k_data, value_of_k)
    return [message.id]


# _________________________________________________________________________________________________________________________________________________________________________
# log out user

@events.register(events.CallbackQuery(pattern='conflogout_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_log_out_user_confirm(event):
    _ = CI[event]._
    logging_user_name = CI[event].selected_user
    buttons = [[Button.inline(_('Yes, logout from'), 'confirmlogout')],
               [Button.inline(_('No, i misclicked'), 'settings_')],
               [Button.inline(_(' « Back to setting'), 'settings_')]]
    import random
    random.shuffle(buttons)
    await event.edit(_('You are about to logout from {}. Is that correct?').format(logging_user_name),
                     buttons=buttons)
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
    await event.client.delete_messages(event.chat_id, [event.message_id])
    await event.respond(_('YOU LOGOUT FROM {}.🛑🚪🚪🚪🚪🚪🚪🚪🛑').format(logging_user_name))
    message = await event.respond(_('You logout from {}.').format(logging_user_name), buttons=buttons)
    return [message.id]


# _________________________________________________________________________________________________________________________________________________________________________
# some delete

@events.register(events.CallbackQuery(pattern='confirmdelete_|confdelete_|deleting_'))
@fsm_decor(st.ActionCallBack())
async def BOT_handler_button_delete_confirm(event):
    _ = CI[event]._
    logging_user_name = CI[event].selected_user
    _k, _k_data, value_of_k = CI[event].get_var_of_last_path()

    if event.data.decode().startswith('deleting_'):
        res_db = db_del_1(_k, _k_data)
        await event.client.delete_messages(event.chat_id, [event.message_id])
        if res_db:
            await event.respond(
                _('Was deleted {}: \n{}\n').format(_(dict_for_type_buttons_by_key[_k].delete_msg),
                                                   value_of_k))
        else:
            await event.respond(_('Dont DELETED. TRY AGAIN ‼️'))
        event.query.data = CI[event].get_back_path().encode('utf_8')
        message_id = await BOT_handler_callback_buttons_table(event, send_msg=True)
        return message_id
    if event.data.decode().startswith('confirmdelete_'):
        buttons = [[Button.inline(_('Yes, delete it'), f'confdelete_')]]
    if event.data.decode().startswith('confdelete_'):
        buttons = [[Button.inline(_('Yes, i am sure 100%'), f'deleting_')]]
    buttons.append([Button.inline(_('No, i misclicked'), CI[event].get_last_path())])
    buttons.append([Button.inline(_(' « Back'), CI[event].get_last_path())])

    # import random
    # random.shuffle(buttons)
    await event.edit(_('You are about to delete:\n{}\n . Is that correct?').format(value_of_k),
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


# @events.register(events.CallbackQuery(pattern='settings_'))
# @fsm_decor(st.ActionCallBack())
# async def BOT_handler_button_settings(event):
#     _ = CI[event]._
#     buttons = [[Button.inline(_('Log out user'), 'conflogout_')],
#                [Button.inline(_('Delete user'), 'deluser_')],
#                [Button.inline(_('Change language'), 'language_')],
#                [Button.inline(_('« Back to user manager'), 'user_')]]
#     await event.edit(_('Settings'), buttons=buttons)
#     return [event.message_id]


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


# Wrong data in button
@events.register(events.CallbackQuery)
async def BOT_handler_wrong_data_for_button(event):
    _ = CI[event]._
    await event.client.send_message(event.sender_id, _('WrongCallbackQuery, {}').format(event.data.decode()))
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

# _______________________________________________________
# add buttons
dict_for_type_buttons_by_key = {}
for cls in globals()[ButtonsTableInfoABC.__name__].__subclasses__():
    dict_for_type_buttons_by_key[cls.key] = cls()


class BuilderButtonsTable:

    def __init__(self, event):
        self.event = event

    def build(self, full_data=None):
        if not full_data:
            full_data = self.get_data()
        key = full_data.split('_', maxsplit=1)[0]
        # key = get_key_for_button_key(self.event)
        type_buttons = dict_for_type_buttons_by_key[key]
        result = type_buttons.buttons_table(self.event, type_buttons, full_data)
        return result

    def get_data(self) -> str:
        if isinstance(self.event, events.NewMessage.Event):
            return self.event.text.split(' ', maxsplit=2)[0][1:]
        if isinstance(self.event, events.CallbackQuery.Event):
            res = self.event.data.decode()
            if res == 'user_':
                res = res + CI[self.event].selected_user
            return res

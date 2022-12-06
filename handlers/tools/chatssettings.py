# -*- coding: utf-8 -*-
from logger import logger as my_logger
from localization import localization

from Database.database import db_set_to_chatssettings, db_get_from_chatssettings, db_del, db_get, \
    db_update_selected_user, db_get_1
from handlers.tools import states as St

# ____________________________________________________________
# add my logger
logger = my_logger.get_logger(__name__)

# ____________________________________________________________
#
command = ['usermanager', 'add', 'settings']
nested = ['tickers', 'tags', 'tag', 'pchs', 'pch', 'shchs', 'shch', 'user',]


# ____________________________________________________________
#

class ExceptionUserNotSelectedSendAllUsers(Exception):
    pass

class ExceptionNotFindInDB(Exception):
    pass

class Ev:
    sender_id = 233222
    any_text = 'text'


class ChatUsers:
    def __init__(self):
        self.__users__ = []

    @property
    def chat_users(self):
        return self.__users__

    def chat_add_user(self, user_info):
        pass


class UserId:
    def __init__(self, event):
        self.chat_id = event.sender_id


class ChatState(UserId):
    class MessagesForDelete:
        def __init__(self):
            self.need_delete = set()
            self.for_next_delete = set()

    def ___init__(self, event):
        UserId.__init__(self, event)
        self.chat_state = St.StateEcho()
        self.chat_state_data = {}
        self.messages_for_delete = ChatState.MessagesForDelete()

    def add_mes_for_del(self, event):
        pass

    def change_state(self, state):
        self.chat_state = state

    # def set_chat_id_state(self, state):
    #     self.chat_id_state = state


class ChatLanguage(UserId):

    def __init__(self, event):
        UserId.__init__(self, event)
        self.language = None
        self.translator = None
        self._ = None
        db_language = db_get_from_chatssettings(self.chat_id, language=True)
        if db_language:
            self.set_translator(db_language)
        else:
            self.set_translator(localization.DEF_LANGUAGE)
            db_set_to_chatssettings(self.chat_id, language=localization.DEF_LANGUAGE)

    def set_translator(self, language):
        self.language = language
        tr = localization.get_lang_gettext(language)
        self.translator = tr
        self._ = tr

    def change_language(self, language: str):
        if language not in localization.LANGUAGES.keys():
            return False
        if self.language == language:
            return False
        self.set_translator(language)
        db_set_to_chatssettings(self.chat_id, language=language)
        return True


class ChatSelectedUser(UserId):
    def __init__(self, event):
        UserId.__init__(self, event)
        self.__selected_user = None
        self.selected_user = None

    @property
    def selected_user(self):
        if self.__selected_user is False or self.__selected_user is None:
            raise ExceptionUserNotSelectedSendAllUsers
        return self.__selected_user

    @selected_user.setter
    def selected_user(self, key_user):
        if key_user == '':
            return
        if not key_user:
            res_db = db_get('ChatsSettings', ['selected_user'], first=True, chat_id=self.chat_id)
            key_user = (res_db.pop()).pop()
            self.__selected_user = key_user
        if key_user != self.__selected_user:
            db_update_selected_user(self.chat_id, key_user)
            self.__selected_user = key_user
        if key_user is False:
            raise ExceptionUserNotSelectedSendAllUsers

    def logout(self):
        logout_user = self.selected_user
        self.selected_user = ''
        db_del('TelegramIdHaveUsers', telegram_id=self.chat_id, key_user=logout_user)


class Path(UserId):

    class KeyData:

        def __init__(self, key, data='', value=''):
            self.path_key = key
            self.data = data
            self.value_of_k = value

        def get_sub_path(self):
            return '_'.join([self.path_key, self.data])

        def __eq__(self, other):
            """Overrides the default implementation"""
            if isinstance(other, Path.KeyData) or isinstance(other, Path.Key):
                return self.path_key == other.path_key
            return False

    FIRST_PATH = [KeyData('myusers')]

    def __init__(self, event):
        super().__init__(event)
        self.path = self.FIRST_PATH
        self.saved_path = []
        # path = [key_data, key_data]

    def update_path(self, full_data, _k):
        if _k not in nested and _k not in command:
            raise Exception('key not in command or nested, need add')
        if _k in command:
            sub_path = Path.KeyData(_k)
        # value = self.get_value_of_key(_k, _k_data)
        else:
            _k_data = full_data.split('_', maxsplit=2)[1]
            value_of_k = self.get_value_of_key(_k, _k_data)
            sub_path = Path.KeyData(_k, data=_k_data, value=value_of_k)

        if sub_path in self.path:
            self.path = self.path[:self.path.index(sub_path) + 1]
            return 'Sub in path'
        self.path.append(sub_path)
        return 'Add subpath'

    def save_path_for_state(self):
        self.saved_path = self.path

    @staticmethod
    def get_value_of_key(_k, _k_data):
        res_db = db_get_1(_k, _k_data)
        if not res_db:
            raise ExceptionNotFindInDB('not key_data`s name in db')
        return res_db.pop()

    def get_var_of_last_path(self, from_saved=False):
        if not from_saved:
            return [self.path[-1].path_key, self.path[-1].data, self.path[-1].value_of_k]
        else:
            return [self.saved_path[-1].path_key, self.saved_path[-1].data, self.saved_path[-1].value_of_k]

    def get_back_path(self, from_saved=False):
        if not from_saved:
            return self.path[-2].get_sub_path()
        else:
            return self.saved_path[-2].get_sub_path()

    def get_last_path(self, from_saved=False):
        if not from_saved:
            return self.path[-1].get_sub_path()
        else:
            return self.saved_path[-1].get_sub_path()


class ChatInfo(ChatLanguage, ChatState, ChatSelectedUser, Path):

    def __init__(self, event):
        ChatLanguage.__init__(self, event)
        ChatState.___init__(self, event)
        ChatSelectedUser.__init__(self, event)
        # self.__path_for_button = Path()
        Path.__init__(self, event)


    # @property
    # def path(self):
    #     return self.__path_for_button.path

    # @path.setter
    # def path(self, path):
    #     self.__path_for_button


class ChatsInfoWorker(type):
    chats_info = {}

    def __missing__(self, key):
        return

    def __iter__(self):
        return iter(self.chats_info.values())

    def __getitem__(self, event: Ev) -> ChatInfo:
        """
        :type event: Ev
        """
        if self.chats_info.get(event.sender_id) is None:
            self.chats_info[event.sender_id] = ChatInfo(event)
        return self.chats_info[event.sender_id]

        # return self.chats_info.setdefault(event.sender_id, ChatInfo(event))

    def __setitem__(self, key, value):
        pass


class CI(metaclass=ChatsInfoWorker):
    pass

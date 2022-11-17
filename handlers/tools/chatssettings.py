# -*- coding: utf-8 -*-
from logger import logger as my_logger
from localization import localization

from Database.database import db_set_to_chatssettings, db_get_from_chatssettings, db_del, db_get, \
    db_update_selected_user
from handlers.tools import states as St

# ____________________________________________________________
# add my logger
logger = my_logger.get_logger(__name__)


# ____________________________________________________________
#

class ExceptionUserNotSelectedSendAllUsers(Exception):
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
        if not key_user:
            res_db = db_get('ChatsSettings', ['selected_user'], first=True, chat_id=self.chat_id)
            # key_user = db_get_from_chatssettings(selected_user=key_user)
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


class ChatInfo(ChatLanguage, ChatState, ChatSelectedUser):

    def __init__(self, event):
        ChatLanguage.__init__(self, event)
        ChatState.___init__(self, event)
        ChatSelectedUser.__init__(self, event)
        # path = ''

class ChatsInfoWorker(type):
    chats_info = {}

    def __missing__(self, key):
        return

    def __iter__(self):
        return iter(self.chats_info.values())

    def __getitem__(self, event: Ev):
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


if __name__ == '__main__':
    event = Ev()
    _ = CI[event]._
    print(_)
    print(CI.chats_info)
    CI[event].change_language('ru_RU')

    _w = CI[event]._

    print(_w)

    event.sender_id = 123
    tr = CI[event]._

    e = Ev()
    e.sender_id = 123
    tr2 = CI[e]._
    print(tr2 is tr)
    CI[e].change_language('ru_RU')
    tr = CI[e]._
    print(tr('Start!'))

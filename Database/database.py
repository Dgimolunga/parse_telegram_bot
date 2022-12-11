# -*- coding: utf-8 -*-
from logger import logger as my_logger
# import localization.localization as localization
import data_value as data_value_file

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm.session import sessionmaker

import re

"""
tools for ParseBot`s ORM database
"""
none_ticker = 'No Ticker'
# from sqlalchemy.ext.declarative import declarative_base

DEF_LANGUAGE = 'en_US'
DEF_STATE = 1
# ____________________________________________________________
# add my logger
logger = my_logger.get_logger(__name__)

# ____________________________________________________________
# for ORM
engine = create_engine('sqlite:///Database/USERBOT_DB.db', echo=False)
Base = declarative_base(engine)
session_db = sessionmaker(bind=engine)()


# ____________________________________________________________
# Exception classes
class NotCorrectExc(Exception):
    pass


class DataDuplicateExc(Exception):
    pass


class UserNotFoundExc(Exception):
    pass


# ____________________________________________________________
# utils functions
def raise_exc(error):
    raise NotCorrectExc(error)


def phone_check(phone):
    return phone


def re_check(data, res, error_msg):
    re_data = re.findall(res, data)
    if not (''.join(re_data) == data):
        raise_exc(error_msg)
    return data


# def int_check(data):
#     re_data = re.findall(r'^[0-9]+', data)
#     if not (''.join(re_data) == data):
#         rais_exc("Значение должно состоять из цыфр")
#     return data
#
# def hash_check(data):
#     re_hash = re.findall(r'^[a-zA-Z0-9]+', api_hash)
#     print(re_hash)
#     if not (''.join(re_hash) == api_hash):
#         pass


check_arg_dict = {
    'telegram_id': lambda t_id: raise_exc('telegram not integer') if type(t_id) == type(1) else t_id,
    'phone': lambda phone: phone_check(phone),
    'api_id': lambda api_id: re_check(api_id, r'^[0-9]+', "Неверный формат api_id (от должен состоять из цыфр)"),
    'api_hash': lambda api_hash: re_check(api_hash, r'^[a-zA-Z0-9]+', 'Неверный формат api_hash'),
    'share_channel_id': lambda share_channel_id: re_check(share_channel_id, r'^[0-9]+',
                                                          "Неверный формат share_channel_id (от должен состоять из цыфр)")

}

# ____________________________________________________________
# ORM classes

dict_table_and_column_of_database = {'User': ('key_user', 'user_password'),
                                     'TelegramIdHaveUsers': ('key_tel_user', 'telegram_id', 'key_user'),
                                     'Ticker': ('key_ticker', 'key_user', 'ticker'),
                                     'Tag': ('key_tag', 'key_ticker', 'tag'),
                                     'ShareChannel': ('key_sharechannel', 'key_user', 'share_channel_id'),
                                     'ParsChannel': ('key_parschannel', 'key_user', 'pars_channel_id'),
                                     }


class ChatsSettings(Base):
    __tablename__ = 'ChatsSettings'
    chat_id = Column(Integer, primary_key=True)
    language = Column(String)
    state = Column(Integer)
    selected_user = Column(String)


# ______________________________________________________________

class User(Base):
    __tablename__ = 'Users'
    key_user = Column(String, primary_key=True)
    user_password = Column(String)
    # telegram_id = Column(Integer)  # а если кто то захочет зарегать
    # phone = Column(String)
    # api_id = Column(Integer)
    # api_hash = Column(String)
    # session_name = Column(String)
    # state = Column(String)
    # start_script = Column(String)


# class LanguageTelegramId(Base):
#     __tablename__ = 'LanguageForTelId'
#     telegram_id = Column(Integer, primary_key=True)
#     language_for_tel_id = Column(String)


class TelegramIdHaveUsers(Base):
    __tablename__ = 'Tel_Users'
    key_tel_user = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    key_user = Column(String)


class Ticker(Base):
    __tablename__ = 'Tickers'
    key_ticker = Column(Integer, primary_key=True)
    key_user = Column(String)
    ticker = Column(String)
    enable = Column(Boolean, unique=False, default=True)


class Tag(Base):
    __tablename__ = 'Tags'
    key_tag = Column(Integer, primary_key=True)
    key_ticker = Column(Integer)
    tag = Column(String)
    enable = Column(Boolean, unique=False, default=True)


class ShareChannel(Base):
    __tablename__ = 'ShareChannels'
    key_sharechannel = Column(Integer, primary_key=True)
    key_user = Column(String)
    share_channel_id = Column(Integer)
    enable = Column(Boolean, unique=False, default=True)


class ParsChannel(Base):
    __tablename__ = 'ParsChannels'
    key_parschannel = Column(Integer, primary_key=True)
    key_user = Column(String)
    pars_channel_id = Column(Integer)
    enable = Column(Boolean, unique=False, default=True)

    # def __repr__(self):
    #     return '<User(telegram_id="{}", phone="{}", api_id="{}", api_hash="{}", share_channel_id="{}", session_name="{}", state="{}", start_script="{}"'.format(
    #         self.telegram_id,
    #         self.phone,
    #         self.share_channel_id,
    #         self.session_name,
    #         self.state,
    #         self.start_script,
    #         self.api_id,
    #         self.api_hash,
    #         )
    # def set_telegram_id(telegram_id):
    #     pass
    #
    # def set_api_id_api_hash(self, api_id, api_hash):
    #     self.api_hash = api_hash


Base.metadata.create_all(engine)

# ____________________________________________________________
# tuple for ParseBotORM columns for classes
arg_other = (
    "some arg...."
)
command_add_list = ('sharechannels', 'parsechannels', 'tickers', 'tags')
command_get_list = ('sharechannels', 'parsechannels', 'tickers', 'tags', 'alltags')

command_set_dict = {'sharechannels': (ShareChannel, 'share_channel_id'),
                    'parsechannels': (ParsChannel, 'pars_channel_id'),
                    'ticker': (Ticker, 'ticker'),
                    'tag': (Tag, 'tag'),
                    }
command_get_dict = {'sharechannels': (ShareChannel, 'share_channel_id'),
                    'parsechannels': (ParsChannel, 'pars_channel_id'),
                    'tickers': (Ticker, 'ticker'),
                    'tags': Tag,
                    'alltags': Tag,
                    }
get_data_for_key_dict = {'tag': (Tag, 'key_tag', 'tag'),
                         'ticker': (Tag, 'key_ticket', 'tag'),
                         'tickersofuser': (Ticker, 'key_user', 'ticker'),

                         }


# ____________________________________________________________
# dict for parse chanel
def add_tag_to_searches_dicts(tag, key_user):
    if tag in data_value_file.tags_of_user:
        data_value_file.tags_of_user[tag].append(key_user)
    else:
        data_value_file.tags_of_user[tag] = [key_user, ]
    if key_user in data_value_file.users_tags:
        data_value_file.users_tags[key_user].append(tag)
    else:
        data_value_file.users_tags[key_user] = [tag, ]


# ____________________________________________________________
# method for handler
# ____________________________________________________________
# functions for management ORM database for ParseBot
def filter_method_available_in_db(table, **kwargs):
    query = session_db.query(table).filter_by(**kwargs)
    return query


# def db_get_tickers(user_logging):
#     query = session_db.query(Ticker).filter_by(key_user=user_logging)
#     tickers = []
#     for ticker_obj in query:
#         tickers.append(ticker_obj)
#     return tickers


#  repeatability check for set_data
def filter_method_duplicate(table, error_msg='', **kwargs):
    query = filter_method_available_in_db(table, **kwargs)
    if query.first() is not None:
        raise DataDuplicateExc(error_msg)


def check_user_in_telegram_id(user_logging, telegram_id):
    query = session_db.query(TelegramIdHaveUsers).filter_by(key_user=user_logging, telegram_id=telegram_id)
    return query.first()


# _________________________
# add to database methods
def add_parse_channel_to_database(user_logging, data):
    filter_method_duplicate(ShareChannel, f"Нельзя добавить ParsChannel: {data}, т.к. он добавлен в ShareChannel",
                            key_user=user_logging, share_channel_id=data)
    filter_method_duplicate(ParsChannel, f"ParsChannel: {data} уже добавлен в эту сессию",
                            key_user=user_logging, pars_channel_id=data)
    pars_channel_obj = ParsChannel(key_user=user_logging, pars_channel_id=int(data))
    session_db.add(pars_channel_obj)


def add_share_channel_to_database(user_logging, data):
    # check_arg_dict[arg](data)                     # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    filter_method_duplicate(ShareChannel, f"ShareChannel: {data} уже добавлен в эту сессию",
                            key_user=user_logging, share_channel_id=data)
    filter_method_duplicate(ParsChannel, f"Нельзя добавить ShareChannel: {data}, т.к. он добавлен в PostChannel",
                            key_user=user_logging, pars_channel_id=data)
    share_channel_obj = ShareChannel(key_user=user_logging, share_channel_id=int(data))
    session_db.add(share_channel_obj)


def add_tag_to_database(user_logging, ticker_name, data):
    # check Ticker
    query = session_db.query(Ticker).filter_by(key_user=user_logging, ticker=ticker_name)
    if query.first() is None:
        raise NotCorrectExc(f'Ticker: {ticker_name} not found')
    # check tag
    filter_method_duplicate(Tag, f"Tag: {data} уже добавлен в эту папку", key_ticker=query.first().key_ticker, tag=data)
    tag_obj = Tag(key_ticker=query.first().key_ticker, tag=data)
    session_db.add(tag_obj)
    session_db.commit()
    # add tag to search`s dicts
    add_tag_to_searches_dicts(data, user_logging)


def add_ticker_to_database(user_logging, ticker: str = none_ticker):
    filter_method_duplicate(Ticker, 'ticker yet is in database', key_user=user_logging, ticker=ticker, )
    ticker_obj = Ticker(key_user=user_logging, ticker=ticker)
    session_db.add(ticker_obj)
    session_db.commit()


def add_user_to_telegram_id(user_logging, telegram_id):
    query = session_db.query(TelegramIdHaveUsers).filter_by(telegram_id=telegram_id, key_user=user_logging)
    if query.first():
        return
    tel_user = TelegramIdHaveUsers(telegram_id=telegram_id, key_user=user_logging)
    session_db.add(tel_user)
    session_db.commit()


# for /create_user command
def add_new_user_to_database(user_logging: str, hash_, sender_id):
    user_obj = User(key_user=user_logging, user_password=hash_)
    session_db.add(user_obj)
    add_user_to_telegram_id(user_logging, sender_id)
    add_ticker_to_database(user_logging, none_ticker)
    session_db.commit()


def get_user(user_logging, telegram_user_id: int):
    if not check_user_in_telegram_id(user_logging, telegram_user_id):
        raise UserNotFoundExc()
    query = session_db.query(User).filter_by(key_user=user_logging)
    user = query.first()
    return user


#  util for /create_user command
def check_user_logging_name_in_db(name: str):
    query = session_db.query(User).filter_by(key_user=name)
    user = query.first()
    if user is None:
        return True
    else:
        return False


# # for /get commands
# def get_data_for_str_request(telegram_user_id: int, user_logging, arg, check_user=False):
#     if check_user:
#         pass
#     else:
#         if not check_user_in_telegram_id(user_logging, telegram_user_id):
#             raise UserNotFoundExc()
#     return_list = []
#     # check for get tag in ticker
#     args = arg.split('_', maxsplit=1)
#     if len(args) == 1:
#         ticker_name = none_ticker
#         arg = args[0]
#     else:
#         ticker_name = args[0]
#         arg = args[1]
#
#     if arg not in command_get_dict:
#         raise NotCorrectExc(f"{arg} not in command_get_list")
#
#     if arg != 'tags' and arg != 'alltags':
#         list_of_obj = session_db.query(command_get_dict[arg][0]).filter_by(key_user=user_logging)
#         for obj in list_of_obj:
#             return_list.append(getattr(obj, command_get_dict[arg][1]))
#         return return_list
#     elif arg == 'tags':
#         # check ticker in d
#         query = filter_method_available_in_db(Ticker, key_user=user_logging, ticker=ticker_name)
#         if query.first() is None:
#             raise NotCorrectExc(f'Ticker: {ticker_name} not found')
#         key_ticker = query.first().key_ticker
#         query = session_db.query(Tag).filter_by(key_ticker=key_ticker)
#         for tag_obj in query:
#             return_list.append(tag_obj.tag)
#         return return_list
#     elif arg == 'alltags':
#         query_ticker = filter_method_available_in_db(Ticker, key_user=user_logging)
#         for ticker_obj in query_ticker:
#             query_tag = filter_method_available_in_db(Tag, key_ticker=ticker_obj.key_ticker)
#             str_to_return_list = f'{ticker_obj.ticker}: '
#             list_for_str_to_return_list = []
#             for tag_obj in query_tag:
#                 list_for_str_to_return_list.append(tag_obj.tag)
#             str_to_return_list += str(list_for_str_to_return_list)
#             return_list.append(str_to_return_list)
#         return return_list
#     else:
#         raise NotCorrectExc


def get_smth_from_database(telegram_user_id: int, user_logging: str, data_table: str, filtr: dict,
                           get_attr: list = None, only_one_result=False):
    if not check_user_in_telegram_id(user_logging, telegram_user_id):
        raise UserNotFoundExc()

    if not get_attr:
        get_attr = dict_table_and_column_of_database[data_table]

    if data_table in dict_table_and_column_of_database.keys() \
            and set(list(filtr.keys()) + get_attr).issubset(dict_table_and_column_of_database[data_table]):
        raise NotCorrectExc(f'Any {data_table} or {filtr} or {get_attr} not found in DataBase')

    return_list = []
    query = session_db.query(globals()[data_table]).filter_by(**filtr)
    for obj in query:
        _list = []
        for attr in get_attr:
            _list.append(getattr(obj, attr))
        if only_one_result:
            return_list = _list
            break
        return_list.append(_list)
    return return_list


def get_data_for_buttons_table(telegram_user_id: int, user_logging: str, name_database_for_key, key, check_user=False):
    if not check_user:
        if not check_user_in_telegram_id(user_logging, telegram_user_id):
            raise UserNotFoundExc()
    return_list = []
    query_obj_of_key = session_db.query(get_data_for_key_dict[name_database_for_key][0]).filter_by(
        **{get_data_for_key_dict[name_database_for_key][1]: key})
    for obj in query_obj_of_key:
        return_list.append(getattr(obj, get_data_for_key_dict[name_database_for_key][2]))
    return return_list


# for /my_users command
def get_all_users(telegram_id):
    users_list = []
    query = session_db.query(TelegramIdHaveUsers).filter_by(telegram_id=str(telegram_id))
    for user in query:
        users_list.append(user.key_user)
    return users_list


# # for /set or /add commands
# def set_data(telegram_user_id: int, user_logging, arg, data):
#     user = get_user(user_logging, telegram_user_id)
#     # /add_loggingname_ticker_tag
#     # /add_loggingname_tag    ---- Ticker = 'No Ticker'
#     args = arg.split('_', maxsplit=1)
#     if len(args) == 1:
#         ticker_name = none_ticker
#         arg = args[0]
#     else:
#         ticker_name = args[0]
#         arg = args[1]
#
#     if hasattr(User, arg):
#         check_arg_dict[arg](data)
#         setattr(user, arg, data)
#     elif hasattr(ParsChannel, arg):
#         add_parse_channel_to_database(user_logging, data)
#     elif hasattr(ShareChannel, arg):
#         add_share_channel_to_database(user_logging, data)
#     elif hasattr(Ticker, arg):
#         add_ticker_to_database(user_logging, data)
#     elif hasattr(Tag, arg):
#         add_tag_to_database(user_logging, ticker_name, data)
#     else:
#         raise NotCorrectExc
#     # for arg in (kwargs.keys() & __arg_user_db):
#     #     setattr(user, arg, kwargs[arg])  # что будет если во время запуска поменять данные
#
#     session_db.commit()


# ____________________________________________________________
# users setting

def db_get_from_chatssettings(chat_id, state=False, language=False):
    query = session_db.query(ChatsSettings).filter_by(chat_id=chat_id)
    res = query.first()
    if res:
        if state:
            return res.chat_state
        if language:
            return res.language
    return None


def db_set_none_to_selected_user(chat_id):
    chat_settings = session_db.query(ChatsSettings).filter_by(chat_id=chat_id).first()
    if not chat_settings:
        return
    chat_settings.selected_user = None
    session_db.add(chat_settings)
    session_db.commit()


def db_set_to_chatssettings(chat_id, state=False, language=False):
    settings = session_db.query(ChatsSettings).filter_by(chat_id=chat_id).first()
    if not settings:
        settings = ChatsSettings()
        settings.chat_id = chat_id
        settings.state = state if state else DEF_STATE
        settings.language = language if language else DEF_LANGUAGE
        settings.selected_user = None
        session_db.add(settings)
    else:
        if state:
            settings.chat_state = state
        if language:
            settings.language = language
    session_db.commit()


def db_del(base: str, first=False, **filtr):
    res = []
    if base in globals() and all(hasattr(globals()[base], attr) for attr in list(filtr.keys())):
        query = session_db.query(globals()[base]).filter_by(**filtr)
        for obj in query:
            session_db.delete(obj)
            if first:
                break
    return


def db_update_selected_user(chat_id, new_selected_user):
    query = session_db.query(ChatsSettings).filter_by(chat_id=chat_id)
    u = query.first()
    u.selected_user = new_selected_user
    session_db.commit()


dict_for_add = {
    'tickers': {
        'base': Ticker,
        'list_filter_for_add': ['key_user', 'ticker'],
        'list_filter_for_switch': ['key_ticker'],
        'list_filter_for_get_all': ['key_user'],
        'lambda_for_get_all': lambda obj: {obj.ticker: (obj.key_ticker, obj.enable)}
    },
    'tags': {
        'base': Tag,
        'list_filter_for_add': ['key_ticker', 'tag'],
        'list_filter_for_get_all': ['key_ticker'],
        'list_filter_for_switch': ['key_tag'],
        'lambda_for_get_all': lambda obj: {obj.tag: (obj.key_tag, obj.enable)}
    }
}

dict_for_get_name = {

    'user': {
        'base': User,
        'list_filter_for_del': ['key_user'],
        'get_res': 'key_user'
    },
    'tickers': {
        'base': User,
        'list_filter_for_del': ['key_user'],
        'get_res': 'key_user'
    },
    'tags': {
        'base': Ticker,
        'list_filter_for_del': ['key_ticker'],
        'get_res': 'ticker'
    },
    'tag': {
        'base': Tag,
        'list_filter_for_del': ['key_tag'],
        'get_res': 'tag'
    },
    'pchs': {
        'base': User,
        'list_filter_for_del': ['key_user'],
        'get_res': 'key_user'
    },
    'shchs': {
        'base': User,
        'list_filter_for_del': ['key_user'],
        'get_res': 'key_user'
    },
    'pch': {
        'base': ParsChannel,
        'list_filter_for_del': ['key_user'],
        'get_res': 'key_user'
    },
    'shch': {
        'base': User,
        'list_filter_for_del': ['key_user'],
        'get_res': 'key_user'
    },
}

dict_for_del = {

    'tags': {
        'base': Ticker,
        'list_filter_for_del': ['key_ticker'],
        'get_res': 'ticker'
    },
    'tag': {
        'base': Tag,
        'list_filter_for_del': ['key_tag'],
        'get_res': 'tag'
    },
    'pch': 2,
    'shch': 3
}


def db_add_smth_for_user(_k, _k_data, add_data_list):
    if _k not in dict_for_add:
        return False
    for_query = dict_for_add[_k]
    base_ = for_query['base']
    for data in add_data_list:
        kwarg_filter_and_add = dict(zip(for_query['list_filter_for_add'], [_k_data, data]))
        query = session_db.query(base_).filter_by(**kwarg_filter_and_add)
        if query.first():
            continue
        obj_ = base_(**kwarg_filter_and_add)
        session_db.add(obj_)
    session_db.commit()
    return True


def db_switch_some_for_user(_k, _k_data):
    if _k not in dict_for_add:
        return False
    for_query = dict_for_add[_k]
    base_ = for_query['base']
    kwarg_filter_and_switch = dict(zip(for_query['list_filter_for_switch'], [_k_data]))
    query = session_db.query(base_).filter_by(**kwarg_filter_and_switch)
    obj = query.first()
    if not obj:
        return False
    obj.enable = not obj.enable
    session_db.commit()
    return True


def db_get_all_smth(_k, _k_data):
    if _k not in dict_for_add:
        return False
    for_query = dict_for_add[_k]
    base_ = for_query['base']
    kwarg_filter_and_get_all = dict(zip(for_query['list_filter_for_get_all'], [_k_data]))
    query = session_db.query(base_).filter_by(**kwarg_filter_and_get_all)
    res_all = {}
    # не доделано
    for obj in query:
        res_all.update(for_query['lambda_for_get_all'](obj))
    return res_all


def db_get(base: str, res_column: list, first=False, **filtr):
    res = []
    if base in globals() and all(hasattr(globals()[base], attr) for attr in list(filtr.keys()) + res_column):
        db_query = session_db.query(globals()[base]).filter_by(**filtr)
        for obj in db_query:
            res_ = []
            for column in res_column:
                res_.append(getattr(obj, column))
            res.append(res_)
            if first:
                break
        return res
    return False


def db_get_1(_k, _k_data, first=False):
    if _k not in dict_for_get_name:
        return False
    for_query = dict_for_get_name[_k]
    base_ = for_query['base']
    kwarg_filter_and_get = dict(zip(for_query['list_filter_for_del'], [_k_data]))
    query = session_db.query(base_).filter_by(**kwarg_filter_and_get)
    if not query.first():
        return False
    res = []
    for obj in query:
        res.append(getattr(obj, for_query['get_res'], None))
        if first:
            break

    return res


def db_del_tag(_k_data):
    query = session_db.query(Tag).filter_by(key_tag=_k_data)
    for obj in query:
        session_db.delete(obj)
    session_db.commit()
    return True


def db_del_tags(_k_data):
    query = session_db.query(Tag).filter_by(key_ticker=_k_data)
    for obj in query:
        session_db.delete(obj)
    query = session_db.query(Ticker).filter_by(key_ticker=_k_data)
    for obj in query:
        session_db.delete(obj)
    session_db.commit()
    return True


def db_del_parse_channel(_k_data):
    pass


def db_del_share_channel(_k_data):
    pass


dict_del = {
    'tag': db_del_tag,
    'tags': db_del_tags,
    'pch': db_del_parse_channel,
    'shch': db_del_share_channel,
}


def db_del_1(_k, _k_data):
    if not dict_del.get(_k, None):
        return False
    return dict_del[_k](_k_data)

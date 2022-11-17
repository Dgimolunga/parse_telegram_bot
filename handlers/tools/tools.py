# -*- coding: utf-8 -*-
from telethon import events
from . import states as st

# _____________________________________________________________________________________________________________________
# @decorator functions
parse_bot_users_state_fsm = st.ParseBotUsersStateFSM()


def fsm_decor(action: st.ActionForFSM = None, stop_propagation=True):
    def callback(fun):
        async def call(*args, **kwargs):
            if action:
                res = await parse_bot_users_state_fsm.action_manager(action, fun, args, kwargs)
            else:
                await fun(*args, **kwargs)
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
def split_(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_list_with_userlogging_and_key_and_keydata_from_eventdata(data):
    return data.decode().split('_', maxsplit=2)

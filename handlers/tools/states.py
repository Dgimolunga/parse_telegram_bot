# -*- coding: utf-8 -*-
from __future__ import annotations
from handlers.tools import chatssettings as CS
from handlers.handlers_of_bot import handlers_BOTS as h_bot


# ______________________________________________________________________________________________________________________
# FSM classes

class State:

    async def send_action(self, action, fun, args, kwargs):
        res = await fun(*args, **kwargs)
        return res

    @staticmethod
    async def change_state_to(state: State, event):
        set1 = CS.CI[event].messages_for_delete.need_delete
        set2 = CS.CI[event].messages_for_delete.for_next_delete
        set1.update(set2)
        set2.clear()
        await event.client.delete_messages(event.chat_id, set1)
        # h_bot.delete_messages(event)
        CS.CI[event].change_state(state)


class StateEcho(State):

    async def send_action(self, action, fun, args, kwargs):
        event = args[0]
        res = []
        if not isinstance(action, ActionCallBack):
            h_bot.delete_messages(event)
        if isinstance(action, ActionNotChangeState):  # ActionChangeStateToEcho
            pass
        if isinstance(action, ActionChangeStateCommand):
            await self.change_state_to(action.change_state_to(**action.change_state_kwargs), event)   # add new state!!!
            sub_res = await fun(*args, **kwargs)
            CS.CI[event].messages_for_delete.for_next_delete.update(sub_res)
        else:
            res = await fun(*args, **kwargs)
            CS.CI[event].messages_for_delete.need_delete.update(res)
        return res


class StateConversation(State):
    sub_state_data_cash = {}

    def __init__(self, next_sub_state=None, finish_state=StateEcho):
        if not next_sub_state:
            self.next_sub_state = self.sub_state_pass_to_fun
        else:
            self.next_sub_state = next_sub_state
        self.finish_state = finish_state
        self.finish_and_change_state = False

    async def send_action(self, action, fun, args, kwargs):
        event = args[0]
        to_for_next_delete = []
        to_need_delete = []
        if not isinstance(action, ActionCallBack):
            await event.client.delete_messages(event.chat_id, CS.CI[event].messages_for_delete.need_delete)
        if isinstance(action, ActionCallBack):
            to_for_next_delete = await fun(*args, **kwargs)
        if isinstance(action, ActionMassage):
            to_for_next_delete = await self.send_sub_state(fun, args, kwargs)
        if isinstance(action, ActionCommand):
            to_need_delete = await fun(*args, **kwargs)
        if isinstance(action, ActionChangeStateCommand):
            await self.change_state_to(action.change_state_to(**action.change_state_kwargs), event)
            to_for_next_delete = await fun(*args, **kwargs)
        CS.CI[event].messages_for_delete.for_next_delete.update(to_for_next_delete)
        if self.finish_and_change_state:
            await self.change_state_to(self.finish_state(), event)
            message = await self.next_sub_state(fun, args, kwargs)
            to_need_delete.extend(message)
        CS.CI[event].messages_for_delete.need_delete.update(to_need_delete)
        return []

    # def send_action(self, action, fun, args, kwargs):
    #     event = args[0]
    #     self.change_state_to(action.change_state_to, event)
    #     return self.send_sub_state(fun, args, kwargs)

    def send_sub_state(self, fun, args, kwargs):
        return self.next_sub_state(fun, args, kwargs)

    # sub_state functions__________________________________________
    @staticmethod
    async def sub_state_pass_to_fun(fun, args, kwargs):
        res = await fun(*args, **kwargs)
        return res

    @staticmethod
    async def sub_state_pass_to_nothing(fun, args, kwargs):
        return []


class ConcreteStateCreateUser(StateConversation):
    def __init__(self):
        self.next_sub_state = h_bot.BOT_newuser_check_name
        self.finish_state = StateEcho
        self.finish_and_change_state = False

    def send_sub_state(self, fun, args, kwargs):
        return self.next_sub_state(fun, args, kwargs)

    # sub_state functions__________________________________________


class ConcreteStateAddUser(StateConversation):
    def __init__(self):
        self.next_sub_state = h_bot.BOT_adduser_check_name
        self.finish_state = StateEcho
        self.finish_and_change_state = False

    # тут надо доюавлять уже существующего ползьзователя
    # async def send_action(self, action, fun, args, kwargs):
    #     event = args[0]
    #     to_for_next_delete = []
    #     to_need_delete = []
    #     if not isinstance(action, ActionCallBack):
    #         await event.client.delete_messages(event.chat_id, CS.CI[event].messages_for_delete.need_delete)
    #     if isinstance(action, ActionCallBack):
    #         to_for_next_delete = await fun(*args, **kwargs)
    #     if isinstance(action, ActionMassage):
    #         to_for_next_delete = await self.send_sub_state(fun, args, kwargs)
    #     if isinstance(action, ActionCommand):
    #         to_need_delete = await fun(*args, **kwargs)
    #     if isinstance(action, ActionChangeStateCommand):
    #         await self.change_state_to(action.change_state_to, event)
    #         to_for_next_delete = await fun(*args, **kwargs)
    #     CS.CI[event].messages_for_delete.for_next_delete.update(to_for_next_delete)
    #     if self.finish_and_change_state:
    #         await self.change_state_to(self.finish_state(), event)
    #         to_need_delete.extend(await self.next_sub_state(fun, args, kwargs))
    #     CS.CI[event].messages_for_delete.need_delete.update(to_need_delete)
    #     return []


class ConcreteStateAdd(StateConversation):
    def __init__(self):
        self.next_sub_state = h_bot.BOT_adduser_check_name
        self.finish_state = StateEcho
        self.finish_and_change_state = False


# ______________________________________________________________________________________________________________________
# Action classes for FSM
# action/
# ├─ ActionForFSM/
# │  ├─ ActionNotChangeState/
# │  │  ├─ ActionMassage/
# │  │  ├─ ActionCommand/
# │  ├─ ActionChangeStateCommand/
# │  │  ├─ ActionChangeStateToConversation/
# │  │  ├─ ActionChangeStateToEcho/

class ActionForFSM:
    pass


class ActionNotChangeState(ActionForFSM):
    pass


class ActionChangeStateCommand(ActionForFSM):
    def __init__(self, change_state_to, **kwargs):
        self.change_state_to = change_state_to
        self.change_state_kwargs = kwargs


class ActionCallBack(ActionForFSM):
    pass


# ________________________________
# classes not change state:


class ActionMassage(ActionNotChangeState):
    pass


class ActionCommand(ActionNotChangeState):
    pass


# ________________________________
# classes change state:
class ActionChangeStateToConversation(ActionChangeStateCommand):
    pass


class ActionChangeStateToEcho(ActionChangeStateCommand):
    pass


# ______________________________________________________________________________________________________________________
# ParseBOT FSM
class UserInfo:
    def __init__(self, state: State, sender_id, data=None):
        self.state = state
        self.user_id = sender_id
        self.user_data = data


class ParseBotUsersStateFSM:

    @staticmethod
    async def action_manager(action, fun, args, kwargs):
        event = args[0]
        res = await CS.CI[event].chat_state.send_action(action, fun, args, kwargs)
        return res


DEF_STATE = 0
DICT_STATE = {0: StateEcho,
              1: ConcreteStateCreateUser,

              }

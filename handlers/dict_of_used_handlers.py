
# -*- coding: utf-8 -*-
from handlers.handlers_of_userbot import handlers_BOT_user as h_ubot
from handlers.handlers_of_bot import handlers_BOTS as h_bot
# !!! ВАЖЕН ПОРЯДОК В ЭТИХ СЛОВОРЯХ !!!
handlers_USERBOT_dict = {
    'event_handler_ms_from': h_ubot.event_handler_ms_from,
    # 'event_handler_spam_ms': h_ubot.event_handler_spam_ms,
}

# !!! ВАЖЕН ПОРЯДОК В ЭТИХ СЛОВОРЯХ !!!
handlers_BOT_parse_dict = {
    'handler': h_bot.handler,
    'BOT_handler_start_script': h_bot.BOT_handler_start_script,
    # 'BOT_handler_start': h_bot.BOT_handler_start,
    # 'BOT_handler_create_user': h_bot.BOT_handler_create_user,
    'BOT_handler_add_user': h_bot.BOT_handler_add_user,
    'BOT_handler_cancel': h_bot.BOT_handler_cancel,
    # 'BOT_handler_set_api_hash_and_id': h_bot.BOT_handler_set_api_hash_and_id,
    # 'BOT_handler_set_id_channel': h_bot.BOT_handler_set_id_channel,
    # 'BOT_handler_set_phone_number': h_bot.BOT_handler_set_phone_number,
    # 'BOT_handler_set_data': h_bot.BOT_handler_set_data,
    # 'BOT_handler_get_data': h_bot.BOT_handler_get_data,
    # 'BOT_handler_add_data': h_bot.BOT_handler_add_data,
    'BOT_handler_language_command': h_bot.BOT_handler_language_command,
    # !!!!'test_all_callbackquerry': h_bot.test_all_callbackquerry,
    # 'BOT_handler_usermanager_command': h_bot.BOT_handler_usermanager_command,
    'BOT_handler_myusers_command': h_bot.BOT_handler_myusers_command,
    'BOT_handler_button_myusers': h_bot.BOT_handler_button_myusers,
    'BOT_handler_button_create_user': h_bot.BOT_handler_button_create_user,
    # 'BOT_handler_button_user': h_bot.BOT_handler_button_user,
    'BOT_handler_button_user': h_bot.DBOT,
    'BOT_handler_button_tickers': h_bot.DBOT_handler_button_tickers,
    'BOT_handler_switch_some': h_bot.BOT_handler_switch_some,
    'BOT_handler_button_add': h_bot.BOT_handler_button_add,
    'BOT_handler_add_confirm_and_finish': h_bot.BOT_handler_add_confirm_and_finish,
    # 'BOT_handler_add_confirm_no_and_finish': h_bot.BOT_handler_add_confirm_no_and_finish,
    # 'BOT_handler_button_settings': h_bot.BOT_handler_button_settings,
    'BOT_handler_button_log_out_user_confirm': h_bot.BOT_handler_button_log_out_user_confirm,
    'BOT_handler_button_log_out_user_confirm2': h_bot.BOT_handler_button_log_out_user_confirm2,
    'BOT_handler_button_log_out_user': h_bot.BOT_handler_button_log_out_user,
    'BOT_handler_button_deleteuser_confirm': h_bot.BOT_handler_button_deleteuser_confirm,
    'BOT_handler_button_delete_confirm': h_bot.BOT_handler_button_delete_confirm,
    'BOT_handler_button_languages': h_bot.BOT_handler_button_languages,
    # 'BOT_handler_button_change_language': h_bot.BOT_handler_button_change_language,
    'BOT_handler_echo': h_bot.BOT_handler_echo,
    'BOT_handler_wrong_data_for_button': h_bot.BOT_handler_wrong_data_for_button,
}

# !!! ВАЖЕН ПОРЯДОК В ЭТИХ СЛОВОРЯХ !!!
handlers_BOT_admin_dict = {
    'BOT_admin_handler_echo': h_bot.BOT_admin_handler_echo,
}

# !!! ВАЖЕН ПОРЯДОК В ЭТИХ СЛОВОРЯХ !!!
handlers_BOT_dict = {
    'bot_admin': handlers_BOT_admin_dict,
    'bot_parse': handlers_BOT_parse_dict,
    'bot_user': handlers_USERBOT_dict,
}
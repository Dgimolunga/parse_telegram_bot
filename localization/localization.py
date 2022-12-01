# -*- coding: utf-8 -*-
from logger import logger as my_logger
import gettext
import gettext_windows

# ____________________________________________________________
# add my logger
logger = my_logger.get_logger(__name__)

# ____________________________________________________________
# support languages
LANGUAGES = {'ru_RU': 'Русский', 'en_US': 'English'}
DEF_LANGUAGE = 'en_US'
# ____________________________________________________________
# set env fot gettext
gettext_windows.setup_env()

__translator_dict__ = {}
__started = False
__translator = gettext


def __start__():
    for lang in LANGUAGES.keys():
        __translator_dict__[lang] = gettext.translation('ex', localedir='localization',
                                                        languages=[lang])  # localization

    gettext.install('ex', names=['ngettext'])


def get_lang_gettext(language=None):
    __translator1 = __translator_dict__.get(language) #setdefoult
    if __translator1:
        return __translator1.gettext
    return __translator.gettext


def change_lang(language: 'str'):
    __translator = __translator_dict__.get(language)
    if __translator:
        __translator.install()


if not __started:
    __start__()
    print()
    __started = True

# -*- coding: utf-8 -*-
import os
import gettext
print(os.environ)
import gettext_windows

gettext_windows.setup_env()

# _ = en_US.gettext
# import Tests_python.Test_gettext.modul2 as m2

# _ = gettext.gettext
f = input('Input')
if f == '1':
    all_translator = gettext.translation(
        'exRU', localedir='localization', languages=['ru_RU']  # 'de_DE', 'es_ES', 'en_US'
    )
    # _ = all_translator.gettext
    all_translator.install()
    # m2.fun()
else:

    gettext.install('ex', localedir='localization')

    # _ = gettext.gettext

# gettext.install(
#     'ex',
#     '',
#     names=['ngettext']
# )

d = [_('Apple'),
     _('Tiger'),
     _('pie'),
     _('fire')]
for i in d:
    print(i)
name = _('Nick')
print(_('Hello world, I am bot, HEELP'))
#print(_({name}).format(name))
print(_('Hello {name}').format(name=name))
# print(dir(__builtins__))
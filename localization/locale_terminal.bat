xgettext -o ex.pot -f files_for_loc
msgmerge ex.po ex.pot -o ex.po
msgfmt -o ex.mo ex.po

# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk

class SmartButton(gtk.Button):
    ''' A button widget that allows on-the-fly translation changes '''

    def __init__(self, session, label=None, stock=None, use_underline=True):
        gtk.Button.__init__(self, label, stock, use_underline)
        self.text = label
        self.session = session

        if self.session is not None:
            self.session.config.subscribe(self.on_language_changed,
            'language_config')

    def set_label(self, text):
        self.text = text
        gtk.Button.set_label(self, _(text))

    def on_language_changed(self, language):
        if self.text is not None:
            self.set_label(self.text)

class SmartCheckButton(gtk.CheckButton, SmartButton):
    ''' A checkbutton widget that allows on-the-fly translation changes '''
    def __init__(self, session, label=None, use_underline=True):
        gtk.CheckButton.__init__(self, label, use_underline)
        SmartButton.__init__(self, session, label, use_underline=use_underline)

class SmartLabel(gtk.Label):
    ''' A label widget that allows on-the-fly translation changes '''

    def __init__(self, session, text=None):
        gtk.Label.__init__(self, text)
        self.clear_attrs()
        self.text = text
        self.session = session

        if self.session is not None:
            self.session.config.subscribe(self.on_language_changed,
            'language_config')

    def on_language_changed(self, language):
        if self.text is not None:
            self.set_text(self.text)
        if self.label is not None:
            self.set_label(self.label)
        if self.markup is not None:
            self.set_markup(self.markup)
        if self.bold_text is not None:
            self.set_bold_text(self.bold_text)

    def set_bold_text(self, text):
        self.clear_attrs()
        self.bold_text = text
        gtk.Label.set_markup(self, '<b>'+_(text)+'</b>')

    def set_text(self, text):
        self.clear_attrs()
        self.text = text
        gtk.Label.set_text(self, _(text))

    def set_label(self, text):
        self.clear_attrs()
        self.label = text
        gtk.Label.set_label(self, _(text))

    def set_markup(self, text):
        self.clear_attrs()
        self.markup = text
        gtk.Label.set_markup(self, _(text))

    def clear_attrs(self):
        self.text = None
        self.label = None
        self.markup = None
        self.bold_text = None

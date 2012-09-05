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
import gobject
import os

import e3
from e3.common import MessageFormatter
import gui
from gui.gtkui import check_gtk3
import utils
import RichBuffer

from gui.base import Plus

import logging
log = logging.getLogger('gtkui.Textbox')

class TextBox(gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''
    __gsignals__ = {
            "search_request": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
            }

    def __init__(self, config, on_drag_data_received=None):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)

        self.config = config

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._textbox = InputView()
        self._textbox.set_left_margin(4)
        self._textbox.set_right_margin(4)
        self._textbox.set_pixels_above_lines(4)
        self._textbox.set_pixels_below_lines(4)
        self._textbox.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self._textbox.show()

        if on_drag_data_received is not None:
            self.on_drag_data_received = on_drag_data_received
            self._textbox.drag_dest_add_uri_targets()
            self._textbox.connect('drag-data-received', self.on_drag_data_received)

        self._buffer = RichBuffer.RichBuffer()
        self._buffer.connect('search_request', self._search_request_cb)

        self._textbox.set_buffer(self._buffer)
        self._textbox.connect_after('copy-clipboard', self._on_copy_clipboard)
        self.add(self._textbox)
        self.widgets = {}

    def _search_request_cb(self, texbox, link):
        self.emit("search_request", link)

    def clear(self):
        '''clear the content'''
        self._buffer.set_text('')
        self.widgets = {}

    def _append(self, text, scroll=True, fg_color=None, bg_color=None,
        font=None, size=None, bold=False, italic=False, underline=False,
        strike=False):
        '''append text to the widget'''
        self._buffer.put_text(text, fg_color, bg_color, font, size, bold,
            italic, underline, strike)

        if scroll:
            self.scroll_to_end()

    def append(self, text, scroll=True):
        '''append formatted text to the widget'''
        self._buffer.put_formatted(text)
        for anchor in self._buffer.widgets.keys():
            obj = self._buffer.widgets[anchor]
            if obj is not None:
                if isinstance(obj, gtk.Widget):
                    self.add_widget_at_anchor(anchor, obj)
                else:
                    path, tip = obj
                    try:
                        self.add_image_at_anchor(anchor, path, tip)
                    except gobject.GError:
                        #custom emoticon not yet downloaded
                        pass

        if scroll:
            self.scroll_to_end()

    def add_image_at_anchor(self, anchor, path, tip):
        ''' Reads path as image and adds the image in anchor '''
        pixbuf = gtk.gdk.PixbufAnimation(path)
        widget = gtk.Image()
        widget.set_from_animation(pixbuf)
        widget.set_tooltip_text(tip)
        self.add_widget_at_anchor(anchor,widget)

    def add_widget_at_anchor(self, anchor, widget):
        self._textbox.add_child_at_anchor(widget, anchor)
        self.widgets[anchor] = widget
        if anchor in self._buffer.widgets.keys():
            del self._buffer.widgets[anchor]
        widget.show()

    def scroll_to_end(self):
        '''scroll to the end of the content'''
        end_iter = self._buffer.get_end_iter()
        self._buffer.place_cursor(end_iter)
        self._textbox.scroll_mark_onscreen(self._buffer.get_insert())

    def _set_text(self, text):
        '''set the text on the widget'''
        self._buffer.set_text(text)

    def _replace_emo_with_shortcut(self):
        if not self._buffer.get_has_selection():
            bounds = self._buffer.get_bounds()
            self._buffer.select_range(bounds[0],bounds[1])

        try:
            start, end = self._buffer.get_selection_bounds()
        except ValueError:
            return ""

        if start.get_offset() > end.get_offset():
            start, end = end, start #set the right begining

        selection = self._buffer.get_slice(start,end)
        char = u"\uFFFC" #it means "widget or pixbuf here"

        return_string = ""
        for part in unicode(selection):
            if part == char:
                anchor = start.get_child_anchor()
                if anchor is not None:
                    widget = self.widgets[anchor]
                    if isinstance(widget, gtk.Image):
                        part = widget.get_tooltip_text()
                    elif isinstance(widget, gtk.Label):
                        part = widget.get_text()
            return_string += part #new string with replacements
            start.forward_char()
        return return_string

    def _on_copy_clipboard(self, textview):
        ''' replaces the copied text with a new text with the
        alt text of the images selected at copying '''
        buffer = self._buffer
        if buffer.get_has_selection():
            text = self._replace_emo_with_shortcut()

            # replace clipboard content
            gtk.clipboard_get().set_text(text, len(text.encode('utf8')))
            gtk.clipboard_get().store()

    def _get_text(self):
        '''return the text of the widget'''
        bounds = self._buffer.get_bounds()
        self._buffer.select_range(bounds[0],bounds[1])
        text = self._replace_emo_with_shortcut()
        end = self._buffer.get_end_iter()
        self._buffer.select_range(end, end)
        return text

    text = property(fget=_get_text, fset=_set_text)

class InputView(gtk.TextView):

    __gsignals__ = {
        'message-send':(gobject.SIGNAL_RUN_LAST|gobject.SIGNAL_ACTION,
                        gobject.TYPE_NONE, ())
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        gtk.TextView.__init__(self)
        self.connect('key-press-event', self.on_key_press_event)

        if check_gtk3():
            targets = [gtk.TargetEntry.new('emesene-invite', 0, 3)]
        else:
            targets = [('emesene-invite', 0, 3)]

        self.drag_dest_set(gtk.DEST_DEFAULT_DROP,
                           ,
                           gtk.gdk.ACTION_DEFAULT)

    def on_key_press_event(self, widget, event):
        if event.keyval in [gtk.keysyms.Return, gtk.keysyms.KP_Enter] and \
            not event.state & gtk.gdk.SHIFT_MASK:

            if not check_im_context_filter_keypress(self, event):
                self.emit('message-send')
            return True
        return False

class InputText(TextBox):
    '''a widget that is used to insert the messages to send'''
    NAME = 'Input Text'
    DESCRIPTION = 'A widget to enter messages on the conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, on_send_message, on_cycle_history,
                on_drag_data_received, send_typing_notification):
        '''constructor'''
        TextBox.__init__(self, session.config, on_drag_data_received)
        self.on_send_message = on_send_message
        self.on_cycle_history = on_cycle_history
        self.send_typing_notification = send_typing_notification
        self._tag = None
        self._textbox.connect('key-press-event', self._on_key_press_event)
        self._buffer.connect('changed', self.on_changed_event)
        self.session = session

        self.changed = False
        self.parse_timeout = None
        self.typing_timeout = None
        self.invisible_tag = gtk.TextTag()
        self.invisible_tag.set_property('invisible', True)
        self._buffer.get_tag_table().add(self.invisible_tag)

        self.spell_checker = None

        #FIXME: gtk2 only as there isn't gtk3 package yet
        if not check_gtk3() and self.config.b_enable_spell_check:
            try:
                import gtkspell
                spell_lang = self.config.get_or_set("spell_lang", "en")
                self.spell_checker = gtkspell.Spell(self._textbox, spell_lang)
            except Exception, e:
                log.warning("Could not load spell-check: %s" % e)

        self._textbox.connect_after('message-send', self._on_message_send)

    def _on_message_send(self, widget):
        '''callback called when enter is pressed in the input widget'''

        if self.text == "":
            return True

        self.on_send_message(self.text)
        self.text = ''

        return True

    def grab_focus(self):
        """
        override grab_focus method
        """
        self._textbox.grab_focus()

    def _on_key_press_event(self, widget, event):
        '''method called when a key is pressed on the input widget'''
        self.changed = True
        self.apply_tag()

        if ( event.state & gtk.gdk.CONTROL_MASK ) and \
                 ( event.keyval == gtk.keysyms.p or \
                    event.keyval == gtk.keysyms.Up ):

            if not check_im_context_filter_keypress(self._textbox, event):
                self.on_cycle_history()
            return True
        elif ( event.state & gtk.gdk.CONTROL_MASK ) and \
                ( event.keyval == gtk.keysyms.n or \
                    event.keyval == gtk.keysyms.Down ):

            if not check_im_context_filter_keypress(self._textbox, event):
                self.on_cycle_history(1)
            return True
        else:
            if self.typing_timeout is None:
                self.send_typing_notification()
                self.typing_timeout = gobject.timeout_add_seconds(3, self.reset_typing_timeout)

        if self.parse_timeout is None:
            self.parse_timeout = gobject.timeout_add(500, self.parse_emotes)

    def reset_typing_timeout(self):
        '''emit typing notification'''
        self.typing_timeout = None
        return False

    def parse_emotes(self):
        """
        parse the emoticons in the widget and replace them with
        images
        """
        if self.changed:
          self.changed = False
          emote_theme = gui.theme.emote_theme

          caches = e3.cache.CacheManager(self.session.config_dir.base_dir)
          emcache = caches.get_emoticon_cache(self.session.account.account)

          for code, path in emote_theme.shortcuts_by_length(emcache.list()):
              if not path.startswith(emote_theme.path):
                  path = os.path.join(emcache.path, path)

              start = self._buffer.get_start_iter()
              result = start.forward_search(code,
                      gtk.TEXT_SEARCH_VISIBLE_ONLY)

              if result is None:
                  continue

              while result is not None:
                  position, end = result
                  mark_begin = self._buffer.create_mark(None, start, False)
                  mark_end = self._buffer.create_mark(None, end, False)

                  self._buffer.delete(position, end)
                  pos = self._buffer.get_iter_at_mark(mark_end)
                  anchor = self._buffer.create_child_anchor(pos)

                  self.add_image_at_anchor(anchor, path, code)

                  start = self._buffer.get_iter_at_mark(mark_end)
                  result = start.forward_search(code,
                          gtk.TEXT_SEARCH_VISIBLE_ONLY)
                  self._buffer.delete_mark(mark_begin)
                  self._buffer.delete_mark(mark_end)

        self.parse_timeout = None
        return False

    def update_style(self, style):
        '''update the global style of the widget'''
        if style is None:
            return

        try:
            color = gtk.gdk.color_parse('#' + style.color.to_hex())
            gtk.gdk.colormap_get_system().alloc_color(color)
        except ValueError:
            return

        is_new = False
        if self._tag is None:
            self._tag = gtk.TextTag()
            is_new = True

        self._tag.set_property('font-desc',
            utils.style_to_pango_font_description(style))

        self._tag.set_property('foreground', '#' + style.color.to_hex())
        self._tag.set_property('strikethrough', style.strike)
        self._tag.set_property('underline', style.underline)

        if is_new:
            self._buffer.get_tag_table().add(self._tag)

        if self.spell_checker:
            buffer = self._textbox.get_buffer()

            if not buffer:
                return

            table = buffer.get_tag_table()
            if not table:
                return

            tag = table.lookup('gtkspell-misspelled')
            if not tag:
                return

            tag.set_priority(table.get_size() - 1)

        self.apply_tag()

    def on_changed_event(self, *args):
        '''called when the content of the buffer changes'''
        self.apply_tag()

    def apply_tag(self):
        '''apply the tag that contains the global style to the text in
        the widget'''
        if self._tag:
            self._buffer.apply_tag(self._tag, self._buffer.get_start_iter(),
                self._buffer.get_end_iter())


class OutputText(gui.base.OutputText, TextBox):
    '''a widget that is used to display the messages on the conversation'''
    NAME = 'Output Text'
    DESCRIPTION = _('A widget to display the conversation messages')
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, config, handler):
        '''constructor'''
        TextBox.__init__(self, config)
        gui.base.OutputText.__init__(self, config)
        self.formatter = MessageFormatter()
        self.set_shadow_type(gtk.SHADOW_IN)
        self._textbox.set_editable(False)
        self._textbox.set_cursor_visible(False)
        self.clear()

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        TextBox.clear(self)
        gui.base.OutputText.clear(self)

    def add_message(self, msg, scroll):
        if msg.type == "status":
            msg.message = Plus.msnplus_strip(msg.message)
            text = self.formatter.format_information(msg.message)
        else:
            msg.alias = Plus.msnplus_strip(msg.alias)
            msg.display_name = Plus.msnplus_strip(msg.display_name)
            text = self.formatter.format(msg)
        TextBox.append(self, text, scroll)

    def update_p2p(self, account, _type, *what):
        ''' new p2p data has been received (custom emoticons) '''
        if _type == 'emoticon':
            for anchor in self._buffer.widgets.keys():
                obj = self._buffer.widgets[anchor]
                if not isinstance(obj, gtk.Widget):
                    path, tip = obj
                    if path == what[2]:
                        self.add_image_at_anchor(anchor, path, tip)

def check_im_context_filter_keypress(target, event):
    ''' return True if the event is handled by Input Method '''
    if hasattr(target, 'im_context_filter_keypress') and \
       target.im_context_filter_keypress(event):
        return True
    return False

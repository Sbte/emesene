import unittest
import sys
import os
import time
import shutil

import gettext
gettext.install('emesene')
import gtk

sys.path.append(os.path.abspath('.'))

import extension

import e3
from e3 import dummy

from gui import gtkui
import gui

import testutils

class ConversationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print 'setup'
        extension.category_register('session', dummy.Session, single_instance=True)
        extension.category_register('sound', e3.common.Sounds.SoundPlayer,
                None, True)
        cls.session = extension.get_and_instantiate('session')
        cls._set_config()
        host = dummy.Session.SERVICES['dummy']['host']
        port = dummy.Session.SERVICES['dummy']['port']
        time.sleep(1)
        account = e3.Account('sbte', '', e3.status.ONLINE, host)
        cls.session.login(account.account, account.password, account.status,
            e3.Proxy(), host, port)

        windowcls = extension.get_default('window frame')
        window = windowcls(cls.dummy)

        window.go_conversation(cls.session)
        conv_manager = window.content
        cls.conversations = []
        cls.conversations.append(conv_manager)

        window.show()

        contact = cls.session.contacts.get('cloud@emesene.org')

        cid = time.time()
        cls.conversation1 = conv_manager.new_conversation(cid, [contact.account])
        cls.session.new_conversation(contact.account, cid)

        cls.conversation1.update_data()
        cls.conversation1.show()
        #~ conv_manager.present(cls.conversation1)

        contact = cls.session.contacts.get('you@emesene.org')

        cid = time.time()
        cls.conversation2 = conv_manager.new_conversation(cid, [contact.account])
        cls.session.new_conversation(contact.account, cid)

        cls.conversation2.update_data()
        cls.conversation2.show()
        print 'setup done'

    @classmethod
    def _set_config(cls):
        cls.session.config.get_or_set('b_conv_minimized', True)
        cls.session.config.get_or_set('b_conv_maximized', False)
        cls.session.config.get_or_set('b_mute_sounds', False)
        cls.session.config.get_or_set('b_play_send', True)
        cls.session.config.get_or_set('b_play_nudge', True)
        cls.session.config.get_or_set('b_play_first_send', True)
        cls.session.config.get_or_set('b_play_type', True)
        cls.session.config.get_or_set('b_play_contact_online', True)
        cls.session.config.get_or_set('b_play_contact_offline', True)
        cls.session.config.get_or_set('b_notify_contact_online', True)
        cls.session.config.get_or_set('b_notify_contact_offline', True)
        cls.session.config.get_or_set('b_notify_receive_message', True)
        cls.session.config.get_or_set('b_show_userpanel', True)
        cls.session.config.get_or_set('b_show_emoticons', True)
        cls.session.config.get_or_set('b_show_header', True)
        cls.session.config.get_or_set('b_show_info', True)
        cls.session.config.get_or_set('b_show_toolbar', True)
        cls.session.config.get_or_set('b_allow_auto_scroll', True)
        cls.session.config.get_or_set('adium_theme', 'renkoo.AdiumMessageStyle')
        cls.session.config.get_or_set('b_enable_spell_check', False)
        cls.session.config.get_or_set('b_download_folder_per_account', False)
        cls.session.config.get_or_set('b_override_text_color', False)
        cls.session.config.get_or_set('override_text_color', '#000000')
        cls.session.config.get_or_set('d_user_service', {})

    @classmethod
    def dummy(cls, *args):
        pass

    def test_focus(self):
        time.sleep(1)
        print self.conversation1.output.view
        print self.conversation1.output.view.text
        self.conversation1.input.on_send_message(testutils.random_string())
        print self.conversation1.output.view.text
        self.session.conv_message(self.conversation2.cid, self.conversation2.members[0], testutils.random_string())
        print self.conversation2.output.view.text
        print self.conversation2.output.view.text
        print self.conversation2.output.view.text
        print self.conversation1.output.view.text

class Window(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        button = gtk.Button('Start gtk test')
        button.connect('clicked', self.start)
        self.add(button)
        self.show_all()

    def start(self, *args):
        suite = unittest.TestLoader().loadTestsFromTestCase(ConversationTestCase)
        unittest.TextTestRunner(verbosity=2).run(suite)


class Controller:
    def __init__(self):
        pass

    def start(self):
        window = Window()

    def on_close(self):
        pass

main_method = extension.get_default('main')
main_method(Controller)

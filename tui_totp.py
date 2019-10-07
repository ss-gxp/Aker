# -*- coding: utf-8 -*-

import urwid
import logging

class Window(object):
    """
    Where all the Tui magic happens,
    handles creating urwid widgets and
    user interactions
    """

    def __init__(self, aker_core):
        self.aker = aker_core
        self.user = self.aker.user

    def draw(self):
        self.screen = urwid.raw_display.Screen()
        self.totp_input = urwid.Edit(
            caption='Enter TOTP: ',
            multiline=False,
            mask="*")
        urwid.connect_signal(
            self.totp_input,
            'postchange',
            self.enter_totp)
        self.loop = urwid.MainLoop(urwid.Filler(self.totp_input, 'top'))

    def enter_totp(self, a, b):
        code = self.totp_input.get_edit_text()
        if len(code) == 6:
            self.aker.validateTotp(code)
            self.stop()

    def start(self):
        logging.debug("TUI: totp started")
        self.loop.run()

    def stop(self):
        logging.debug(u"TUI: totp stopped")
        raise urwid.ExitMainLoop()

    def pause(self):
        logging.debug("TUI: totp paused")
        self.loop.stop()

    def restore(self):
        logging.debug("TUI: totp restored")
        self.loop.start()
        self.loop.screen_size = None
        self.loop.draw_screen()

# -*- coding: utf-8 -*-

import urwid
import logging
import pyotp
import qrcode
import StringIO


class Window(object):
    """
    Where all the Tui magic happens,
    handles creating urwid widgets and
    user interactions
    """

    def __init__(self, aker_core):
        self.aker = aker_core
        self.user = self.aker.user
        self.totp_reg = None
        self.screen = None
        self.totp_input = None
        self.loop = None

    def draw(self, issuer):
        self.totp_reg = pyotp.random_base32()
        url = pyotp.totp.TOTP(self.totp_reg).provisioning_uri(self.aker.posix_user, issuer_name=issuer)

        qr = qrcode.QRCode()
        qr.add_data(url)
        s = StringIO.StringIO()
        qr.print_ascii(s, False, True)
        s_qr = s.getvalue()

        self.screen = urwid.raw_display.Screen()

        self.totp_input = urwid.Edit(
            caption=s_qr + '\n\n' + url + '\n\nWelcome! You must enable TOTP, scan QR with app and enter code: ',
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
            self.aker.validate_totp_and_reg(self.totp_reg, code)
            self.stop()

    def start(self):
        logging.debug("TUI: totp reg started")
        self.loop.run()

    def stop(self):
        logging.debug(u"TUI: totp reg stopped")
        raise urwid.ExitMainLoop()

    def pause(self):
        logging.debug("TUI: totp reg paused")
        self.loop.stop()

    def restore(self):
        logging.debug("TUI: totp reg restored")
        self.loop.start()
        self.loop.screen_size = None
        self.loop.draw_screen()

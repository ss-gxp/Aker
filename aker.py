#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       Copyright 2016 ahmed@nazmy.io
#
# For license information see LICENSE.txt


# Meta
from config import Configuration

__version__ = '0.4.5'
__version_info__ = (0, 4, 5)
__license__ = "AGPLv3"
__license_info__ = {
    "AGPLv3": {
        "product": "aker",
        "users": 0,  # 0 being unlimited
        "customer": "Unsupported",
        "version": __version__,
        "license_format": "1.0",
    }
}

import logging
import os
import uuid
import getpass
import paramiko
import time
import signal
import pyotp
import hashlib

from hosts import Hosts
import tui
import tui_totp_reg
import tui_totp
from session import SSHSession
from snoop import SSHSniffer


class User(object):
    def __init__(self, username):
        self.name = username
        gateway_hostgroup = config.get('gateway_group')
        idp = config.get('idp')
        logging.debug("Core: using Identity Provider {0}".format(idp))
        self.hosts = Hosts(config, self.name, gateway_hostgroup, idp)
        self.allowed_ssh_hosts, self.hostgroups = self.hosts.list_allowed()

    def get_priv_key(self):
        try:
            # TODO: check better identity options
            privkey = paramiko.RSAKey.from_private_key_file(
                os.path.expanduser("~/.ssh/id_rsa"))
        except Exception as e:
            logging.error(
                "Core: Invalid Private Key for user {0} : {1} ".format(
                    self.name, e.message))
            raise Exception("Core: Invalid Private Key")
        else:
            return privkey

    def refresh_allowed_hosts(self, fromcache):
        logging.info(
            "Core: reloading hosts for user {0} from backened identity provider".format(
                self.name))
        self.allowed_ssh_hosts, self.hostgroups = self.hosts.list_allowed(
            from_cache=fromcache)


class Aker(object):
    """ Aker core module, this is the management module
    """

    def __init__(self, config):
        self.config = config
        self.tui = None

        try:
            self.posix_user = os.environ['AKERUSER']
        except Exception:
            self.posix_user = getpass.getuser()

        try:
            totp_enabled = self.config.get("General", "totp_enabled", "0")
            if totp_enabled != "0":
                self.totp_enabled = True
            else:
                self.totp_enabled = False
        except:
            self.totp_enabled = True

        if self.totp_enabled:
            self.totp_file = self.config.get("General", "totp_file", "").format(hashlib.sha256(self.posix_user).hexdigest())
            self.totp_issuer = self.config.get("General", "totp_issuer", "Aker")
            try:
                fp = open(self.totp_file, 'r')
                self.totp_secret = fp.read()
                fp.close()
            except Exception:
                self.totp_secret = None

        self.port = config.ssh_port

        logging.info(
            "Core: Starting up, user={0} from={1}:{2}".format(
                self.posix_user,
                config.src_ip,
                config.src_port))

        self.user = User(self.posix_user)

    @staticmethod
    def signal_handler(signum, frame):
        logging.debug("Core: user tried an invalid signal {}".format(signum))

    def run(self):
        # Capture CTRL-C
        original_handler = signal.signal(signal.SIGINT, self.signal_handler)

        try:
            logging.debug("Core: Drawing TUI")

            if self.totp_enabled:
                if not self.totp_secret:
                    self.tui = tui_totp_reg.Window(self)
                    self.tui.draw(self.totp_issuer)
                    self.tui.start()
                else:
                    self.tui = tui_totp.Window(self)
                    self.tui.draw()
                    self.tui.start()

            self.tui = tui.Window(self)
            self.tui.draw()
            self.tui.start()

        finally:
            signal.signal(signal.SIGINT, original_handler)

    def validate_totp(self, code):
        totp = pyotp.TOTP(self.totp_secret)
        if not totp.verify(code):
            logging.info('Wrong TOTP entered')
            raise Exception("Core: Wrong TOTP")

    def validate_totp_and_reg(self, totp_secret, code):
        totp = pyotp.TOTP(totp_secret)
        if not totp.verify(code):
            logging.info('Wrong TOTP entered')
            raise Exception("Core: Wrong TOTP")
        fp = open(self.totp_file, 'w')
        fp.write(totp_secret)
        fp.close()
        self.totp_secret = totp_secret

    def init_connection(self, name):
        screen_size = self.tui.loop.screen.get_cols_rows()
        logging.debug("Core: pausing TUI")
        self.tui.pause()
        # TODO: check for shorter yet unique uuid
        session_uuid = uuid.uuid4()
        session_start_time = time.strftime("%Y%m%d-%H%M%S")
        host = self.user.allowed_ssh_hosts[name]
        session = SSHSession(self, host, session_uuid)
        # TODO: add err handling
        sniffer = SSHSniffer(
            config,
            self.posix_user,
            host.fqdn,
            session_uuid,
            screen_size
        )
        session.attach_sniffer(sniffer)
        logging.info(
            "Core: Starting session UUID {0} for user {1} to host {4}@{2}:{3}".format(
                session_uuid, self.posix_user, host.fqdn, host.ssh_port, host.user))
        session.connect(screen_size)
        try:
            session.start_session()
        finally:
            session.stop_sniffer()
            self.tui.restore()
            self.tui.hostlist.search.clear()  # Clear selected hosts

    def session_end_callback(self, session):
        logging.info(
            "Core: Finished session UUID {0} for user {1} to host {4}@{2}:{3}".format(
                session.uuid,
                self.posix_user,
                session.host,
                session.host_port,
                session.host_user))


if __name__ == '__main__':
    try:
        config = Configuration()

        # Setup logging first thing
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(format=config.log_format, filename=config.log_file, level=config.log_level)

        aker = Aker(config)
        aker.run()
    except Exception as e:
        print e
        logging.exception(e)

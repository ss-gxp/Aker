# -*- coding: utf-8 -*-
import os
import uuid

from backports.configparser import ConfigParser, NoOptionError, NoSectionError


class Configuration(object):
    def __init__(self, filename=None):
        remote_connection = os.environ.get('SSH_CLIENT', '0.0.0.0 0')
        self.src_ip = remote_connection.split()[0]
        self.src_port = remote_connection.split()[1]
        self.session_uuid = uuid.uuid1()

        if filename is None:
            filename = "/etc/aker/aker.ini"
        self.configparser = ConfigParser()
        self.configparser.read(filename)
        self.ssh_port = self.get('General', 'ssh_port', 22)
        self.session_log_dir = self.get('General', 'session_log_dir', '/var/log/aker/')
        self.log_level = self.get('General', 'log_level', 'INFO')
        self.log_file = self.get('General', 'log_file', '/var/log/aker/aker.log')
        self.log_format = self.get('General', 'log_format', '%(asctime)s - %(levelname)s - %(message)s')
        self.realm = self.get('General', 'realm', 'Aker')

        self.palette = [
            self.__get_color('body', 'black', 'light gray'),  # Normal Text
            self.__get_color('focus', 'light green', 'black', 'standout'),  # Focus
            self.__get_color('head', 'white', 'dark gray', 'standout'),  # Header
            self.__get_color('foot', 'light gray', 'dark gray'),  # Footer Separator
            self.__get_color('key', 'light green', 'dark gray', 'bold'),
            self.__get_color('title', 'white', 'black', 'bold'),
            self.__get_color('popup', 'white', 'dark red'),
            self.__get_color('msg', 'yellow', 'dark gray'),
            self.__get_color('SSH', 'dark blue', 'light gray', 'underline'),
            self.__get_color('SSH_focus', 'light green', 'dark blue', 'standout')]  # Focus

    def get(self, *args):
        if len(args) == 3:
            try:
                return self.configparser.get(args[0], args[1])
            except (NoSectionError, NoOptionError):
                return args[2]
        if len(args) == 2:
            return self.configparser.get(args[0], args[1])
        else:
            return self.configparser.get('General', args[0])

    def __get_color(self, name, def_fore, def_back, opt=''):
        return name, self.get('Palette', name + '_fg', def_fore), self.get('Palette', name + '_bg', def_back), self.get('Palette', name + '_opt', opt)

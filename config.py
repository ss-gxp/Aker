# -*- coding: utf-8 -*-
import os
import uuid

from backports.configparser import ConfigParser, NoOptionError


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

    def get(self, *args):
        if len(args) == 3:
            try:
                return self.configparser.get(args[0], args[1])
            except NoOptionError:
                return args[2]
        if len(args) == 2:
            return self.configparser.get(args[0], args[1])
        else:
            return self.configparser.get('General', args[0])

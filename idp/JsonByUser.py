#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Meta

from IdPFactory import IdP
import json
import logging


class JsonByUser(IdP):
    """
    Fetch the authority informataion from a JSON configuration
    """

    def __init__(self, config, username, gateway_hostgroup):
        super(JsonByUser, self).__init__(username, gateway_hostgroup)
        logging.info("JsonByUser: loaded")
        self.config = config
        self.posix_user = username
        self._init_json_config()

    def _init_json_config(self):
        # Load the configration from the already intitialised config parser
        hosts_file = self.config.get("General", "hosts_file", "hosts.json").format(self.posix_user)
        try:
            JSON = json.load(open(hosts_file, 'r'))
        except Exception as e:
            logging.error(
                "JSON: could not read json file {0} , error : {1}".format(
                    hosts_file, e.message))
            raise Exception("Access denied")

        logging.debug("Json: loading all hosts from {0}".format(hosts_file))
        self._all_ssh_hosts = JSON["hosts"]
        self._allowed_ssh_hosts = {}
        self._load_user_allowed_hosts()

    def _load_user_allowed_hosts(self):
        """
        Fetch the allowed hosts based usergroup/hostgroup membership
        """
        for host in self._all_ssh_hosts:
            logging.debug(
                u"Json: loading host {0} for user {1}".format(
                    host.get("name"), self.posix_user))
            self._allowed_ssh_hosts[host.get("name")] = {
                'name': host.get("name"),
                'fqdn': host.get("hostname"),
                'ssh_port': host.get("port", 22),
                'user': host.get("user", None),
                'hostgroups': host.get("hostgroups")
            }

    def list_allowed(self):
        # is our list empty ?
        if not self._allowed_ssh_hosts:
            self._load_user_allowed_hosts()
        return self._allowed_ssh_hosts

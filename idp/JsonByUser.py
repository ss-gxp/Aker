#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Meta

from IdPFactory import IdP
import json
import logging
import hashlib


class JsonByUser(IdP):
    """
    Fetch the authority informataion from a JSON configuration
    """

    def __init__(self, config, username, gateway_hostgroup):
        super(JsonByUser, self).__init__(username, gateway_hostgroup)
        logging.info("JsonByUser: loaded")
        self.config = config
        self.posix_user = username

    def _load_json_config(self):
        # Load the configration from the already intitialised config parser
        hosts_file = self.config.get("General", "hosts_file", "hosts.json").format(hashlib.sha256(self.posix_user).hexdigest())
        try:
            JSON = json.load(open(hosts_file, 'r'))
        except Exception as e:
            logging.error(
                "JSON: could not read json file {0} , error : {1}".format(
                    hosts_file, e.message))
            raise Exception("Access denied")

        logging.debug("Json: loading all hosts from {0}".format(hosts_file))
        ssh_hosts = JSON["hosts"]

        result = {}
        for host in ssh_hosts:
            logging.debug(
                u"Json: loading host {0} for user {1}".format(
                    host.get("name"), self.posix_user))
            result[host.get("name")] = {
                'name': host.get("name"),
                'fqdn': host.get("hostname"),
                'ssh_port': host.get("port", 22),
                'user': host.get("user", None),
                'hostgroups': host.get("hostgroups")
            }
        return result

    def list_allowed(self):
        return self._load_json_config()

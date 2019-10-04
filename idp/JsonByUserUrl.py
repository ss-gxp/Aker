#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Meta

from IdPFactory import IdP
import json
import logging
import urllib
import hashlib


class JsonByUserUrl(IdP):
    """
    Fetch the authority information from a JSON by URL
    """

    def __init__(self, config, username, gateway_hostgroup):
        super(JsonByUserUrl, self).__init__(username, gateway_hostgroup)
        logging.info("JsonByUserUrl: loaded")
        self.config = config
        self.posix_user = username
        self._init_json_config()

    def _init_json_config(self):
        # Load the configration from the already intitialised config parser
        hosts_file = self.config.get("General", "hosts_file", "").format(hashlib.sha256(self.posix_user).hexdigest())
        hosts_url = self.config.get("General", "hosts_url", "").format(self.posix_user)

        response = None
        try:
            try:
                # Get from server
                if hosts_url == "":
                    raise Exception("Configuration error: hosts_url is empty")
                response = urllib.request.urlopen(hosts_url, None, 10).read()
                user_config = json.loads(response)
                logging.debug("Json: loading all hosts from {0}".format(hosts_url))

                # Save to disk copy
                try:
                    fp = open(hosts_file, 'w')
                    fp.write(response)
                    fp.close()
                except Exception as e:
                    logging.error(
                        "JSON: could not save json to file {0} , error : {1}".format(
                        hosts_file, e.message))
            except Exception as e:
                # If request to server failed - load copy from disk
                user_config = json.load(open(hosts_file, 'r'))
                logging.debug("Json: loading all hosts from {0}".format(hosts_file))
        except Exception as e:
            logging.error(
                "JSON: could not read json file {0} , error : {1}".format(
                    hosts_url, e.message))
            raise Exception("Access denied")

        self._all_ssh_hosts = user_config["hosts"]
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

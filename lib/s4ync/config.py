#!/usr/bin/env python

# Copyright 2007,2008 Josh Bressers

# This file is part of s4ync.
#
# s4ync is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# s4ync is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA


import os
import os.path
import ConfigParser

class Config:
    "Class to contain the various configuration derectives."

    def __init__(self):

        self.config = {}

        self.config['config_file'] = os.path.join(os.environ['HOME'], '.s4ync')

        # Set various default configuration options
        self.config['delete'] = False # delete extraneous files from dest dirs
        self.config['verbose'] = 0        # Noise level
        self.config['cache'] = ''
        self.config['progress'] = False

        # XXX: Get these two from a config file
        self.config['encrypt_cmd'] = "gpg --trust-model always -e -o - -r \"%s\" \"%s\""
        self.config['decrypt_cmd'] = "gpg -q --decrypt -o - \"%s\""

        self.read_config_file()

    def __getattr__(self, name):
        if self.config.has_key(name):
            return self.config[name]
        else:
            return None

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def read_config_file(self, file=None):
        'Load the configuration data from the configuration file'

        if file:
            self.config_file = file

        config = ConfigParser.SafeConfigParser()
        config_return = config.read(self.config_file)

        if len(config_return) <= 0:
            # No configuration data to read
            return

        for i in config.items('main'):
            self.config[i[0]] = i[1]

configuration = Config()

def get_config():
    return configuration

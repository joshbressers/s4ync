#!/usr/bin/env python

# Copyright 2007 Josh Bressers

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

class Config:
    "Class to contain the various configuration derectives."

    def __init__(self):

        # Set various default configuration options
        self.delete = False     # delete extraneous files from dest dirs
        self.verbose = 0        # Noise level

        # XXX: Get these two from a config file
        self.encrypt_cmd = "gpg --trust-model always -e -o - -r \"%s\" \"%s\""
        self.decrypt_cmd = "gpg -q --decrypt -o - \"%s\""

configuration = Config()

def get_config():
    return configuration

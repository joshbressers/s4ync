#!/usr/bin/env python

# Copyright 2008 Josh Bressers

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

import config
import os.path
import anydbm
import pickle
import base64

cachepool = {}

class S3Cache:

    def __init__(self, bucket):
        global cachepool
        self.cache = None

        if cachepool.has_key(bucket):
            # First see if we've already opened this bucket cache
            self.cache = cachepool[bucket]
        else:
            # Open the bucket cache
            self.configuration = config.get_config()
            self.cache_dir = self.configuration.cache
            if self.cache_dir:
                cache_file = os.path.join(self.cache_dir, bucket)
                self.cache = anydbm.open(cache_file, 'c')

    def __encode_key(self, key):
        return base64.b64encode(key.encode('utf-8')) 

    def __decode_key(self, key):
        new_key = base64.b64decode(key)
        return unicode(new_key)

    def get(self, key):
        key = self.__encode_key(key)
        if self.cache.has_key(str(key)):
            data = self.cache[str(key)]
            return pickle.loads(data)
        else:
            return None

    def set(self, key, data):
        key = self.__encode_key(key)
        data = pickle.dumps(data)
        self.cache[str(key)] = data

    def get_keys(self):
        new_keys = []
        keys = self.cache.keys()
        for i in keys:
            new_keys.append(self.__decode_key(i))
        return new_keys

    def delete(self, key):
        key = self.__encode_key(key)
        del self.cache[key]

    def delete_all(self):
        self.cache.clear()
        self.cache.sync()

    def has_key(self, key):
        key = self.__encode_key(key)
        return key in self.cache

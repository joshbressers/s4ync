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
import sqlite
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
                self.cache = sqlite.connect(cache_file)
                cachepool[bucket] = self.cache

                # Does the table structure exist?
                cursor = self.cache.cursor()
                cursor.execute(
                    'SELECT name FROM sqlite_master WHERE type="table"'
                )
                if cursor.rowcount == 0:
                    # We need to create the table
                    cursor.execute('CREATE TABLE bucket (filename TEXT PRIMARY KEY, data TEXT)')
                    self.cache.commit()


    def get(self, key):
        cursor = self.cache.cursor()
        cursor.execute('SELECT data FROM bucket WHERE filename="%s"' % key)

        if cursor.rowcount == 1:
            data = cursor.fetchone()[0]
            return pickle.loads(data)
        else:
            return None

    def set(self, key, data):
        cursor = self.cache.cursor()
        data = pickle.dumps(data)

        key = unicode(key).encode('utf-8')

        cursor.execute('SELECT data FROM bucket WHERE filename="%s"' % key)
        if cursor.rowcount == 1:
            # We need to update the data
            cursor.execute('UPDATE bucket set data="%s" where filename="%s"' \
                % (data, key))
        else:
            # New key
            cursor.execute('INSERT INTO bucket values ("%s", "%s")' % (key, data))

        self.cache.commit()

    def get_keys(self):
        cursor = self.cache.cursor()
        new_keys = []

        cursor.execute('SELECT filename FROM bucket')

        for i in cursor.fetchall():
            new_keys.append(i[0])
        return new_keys

    def delete(self, key):
        cursor = self.cache.cursor()
        cursor.execute('DELETE FROM bucket WHERE filename="%s"' % key)
        self.cache.commit()

    def delete_all(self):
        cursor = self.cache.cursor()
        cursor.execute('DELETE FROM bucket')
        self.cache.commit()

    def has_key(self, key):
        cursor = self.cache.cursor()
        cursor.execute('SELECT data FROM bucket WHERE filename="%s"' % key)
        return cursor.rowcount == 1

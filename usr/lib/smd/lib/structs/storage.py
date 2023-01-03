#!/usr/bin/false
# The Storage class is the basis for all file based Python dictionaries.
# This class extends the "dict" class and has options for saving and loading data
# from files.
#
# All non-private (lacking "_" prefixes) attributes are treated as data from the
# internal dictionary.
#
# This allows a Storage class to have attributes set to the internal dictionary
# using standard Python conventions. The other functions, including the "get"
# function, allow for setting defaults while attempting to get information from
# the internal dictionary.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2023 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from json import dumps
from os.path import isfile
from lib.util import write_json, read_json


_INTERNAL = [
    "get",
    "set",
    "send",
    "recv",
    "read",
    "write",
    "update",
    "header",
    "set_file",
    "get_file",
    "is_error",
    "set_config",
    "get_config",
    "set_header",
    "is_multicast",
    "set_multicast",
    "is_from_client",
]


class Storage(dict):
    def __init__(self, data=None, path=None, errors=True, no_fail=False):
        dict.__init__(self)
        if isinstance(data, dict):
            self.update(data)
        self._file = path
        if isinstance(path, str) and len(path) > 0 and isfile(path):
            self.read(self._file, errors=errors)
        self._no_fail = no_fail

    def __str__(self):
        return dumps(self, indent=4, sort_keys=True)

    def get_file(self):
        return self._file

    def update(self, data):
        if not isinstance(data, dict) or len(data) == 0:
            return
        d = data.copy()
        for k in d.keys():
            if not Storage.__is_reserved(k):
                continue
            del d[k]
        super(__class__, self).update(d)
        del d

    @staticmethod
    def __is_reserved(name):
        if not isinstance(name, str) or len(name) == 0:
            return False
        if name[0] == "_":
            return True
        return name in _INTERNAL

    def set_file(self, path):
        self._file = path

    def __getitem__(self, name):
        v = self.__get_set(name, True, None, False)
        if v is None:
            raise KeyError(name)
        return v

    def __delattr__(self, name):
        if Storage.__is_reserved(name):
            return super(__class__, self).__delattr__(name)
        if super(__class__, self).__contains__(name):
            return self.__delitem__(name)
        return super(__class__, self).__delattr__(name)

    def __getattr__(self, name):
        return self.__getattribute__(name)

    def __getattribute__(self, name):
        if Storage.__is_reserved(name):
            return super(__class__, self).__getattribute__(name)
        if super(__class__, self).__contains__(name):
            return self.__getitem__(name)
        try:
            return super(__class__, self).__getattribute__(name)
        except AttributeError as err:
            if self._no_fail:
                return None
            raise err

    def get(self, name, default=None):
        return self.__get_set(name, True, default, False)

    def __setattr__(self, name, value):
        if Storage.__is_reserved(name):
            return super(__class__, self).__setattr__(name, value)
        return self.__setitem__(name, value)

    def __setitem__(self, name, value):
        return self.__get_set(name, False, value, False)

    def __get_single(self, name, default):
        if default is not None and not super(__class__, self).__contains__(name):
            super(__class__, self).__setitem__(name, default)
            return default
        if super().__contains__(name):
            return super(__class__, self).__getitem__(name)
        return None

    def read(self, path=None, errors=True):
        f = self._file if path is None else path
        d = read_json(f, errors=errors)
        if not isinstance(d, dict):
            if not errors:
                raise OSError(f'Result from "{f}" was not a Dict')
            del f
            del d
            return False
        self.update(d)
        del f
        del d
        return True

    def set(self, name, value, only_not_exists=False):
        return self.__get_set(name, False, value, only_not_exists)

    def __set_single(self, name, value, only_not_exists):
        if only_not_exists and super(__class__, self).__contains__(name):
            return
        return super(__class__, self).__setitem__(name, value)

    def __get_set(self, name, get, value, only_not_exists):
        if "." not in name:
            if get:
                return self.__get_single(name, value)
            return self.__set_single(name, value, only_not_exists)
        s = name.split(".")
        if len(s) == 1:
            if get:
                return self.__get_single(s[0], value)
            return self.__set_single(s[0], value, only_not_exists)
        o = dict()
        if super(__class__, self).__contains__(s[0]):
            o = super(__class__, self).__getitem__(s[0])
        elif value is not None or not get:
            super(__class__, self).__setitem__(s[0], o)
        elif get:
            del o
            del s
            return value
        for x in range(1, len(s) - 1):
            n = o.get(s[x])
            if n is None:
                o[s[x]] = dict()
                n = o[s[x]]
            o = n
            del n
        name = s[len(s) - 1]
        del s
        if only_not_exists and not get and name in o:
            return value
        if not get or (value is not None and name not in o):
            o[name] = value
        elif get and name in o:
            return o[name]
        del o
        return value

    def write(self, path=None, indent=4, sort=True, perms=None, errors=True):
        return write_json(
            self._file if path is None else path, self, indent, sort, perms, errors
        )

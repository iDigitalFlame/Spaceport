#!/usr/bin/false
################################
### iDigitalFlame  2016-2024 ###
#                              #
#            -/`               #
#            -yy-   :/`        #
#         ./-shho`:so`         #
#    .:- /syhhhh//hhs` `-`     #
#   :ys-:shhhhhhshhhh.:o- `    #
#   /yhsoshhhhhhhhhhhyho`:/.   #
#   `:yhyshhhhhhhhhhhhhh+hd:   #
#     :yssyhhhhhyhhhhhhhhdd:   #
#    .:.oyshhhyyyhhhhhhddd:    #
#    :o+hhhhhyssyhhdddmmd-     #
#     .+yhhhhyssshdmmddo.      #
#       `///yyysshd++`         #
#                              #
########## SPACEPORT ###########
### Spaceport + SMD
#
# Copyright (C) 2016 - 2024 iDigitalFlame
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

# storage.py
#   The Storage class is the basis for all file based Python dictionaries.
#   This class extends the "dict" class and has options for saving and loading
#   data from files.
#
#   All non-private (lacking "_" prefixes) attributes are treated as data from the
#   internal dictionary.
#
#   This allows a Storage class to have attributes set to the internal dictionary
#   using standard Python conventions. The other functions, including the "get"
#   function, allow for setting defaults while attempting to get information from
#   the internal dictionary.

from json import dumps
from lib.util import nes
from lib.util.file import write_json, read_json

_INTERNAL = [
    "get",
    "set",
    "uid",
    "pid",
    "path",
    "send",
    "recv",
    "save",
    "load",
    "keys",
    "items",
    "update",
    "header",
    "values",
    "forward",
    "is_error",
    "multicast",
    "is_forward",
    "set_forward",
    "is_multicast",
    "set_multicast",
    "is_same_client",
]


class Flex(object):
    __slots__ = ("_data",)

    def __init__(self):
        self._data = dict()

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def __str__(self):
        return dumps(self._data, indent=4, sort_keys=True)

    def __len__(self):
        return self._data.__len__()

    @staticmethod
    def __reserved(name):
        if not isinstance(name, str) or len(name) == 0:
            return False
        if name[0] == "_":
            return True
        return name in _INTERNAL

    def update(self, data):
        if not isinstance(data, dict) or len(data) == 0:
            return
        for k, v in data.items():
            if len(k) == 1 and k == "_":
                self._data.__setitem__("_ro", True)
                continue
            if Flex.__reserved(k):
                continue
            self._data.__setitem__(k, v)

    def set(self, name, value):
        if not isinstance(name, str):
            return self._data.__setitem__(name, value)
        return self.__get(name, value, True, False)

    def __delattr__(self, name):
        if Flex.__reserved(name):
            return super(__class__, self).__delattr__(name)
        try:
            return super(__class__, self).__delattr__(name)
        except AttributeError:
            pass
        try:
            del self._data.__delitem__[name]
        except KeyError:
            pass

    def __getitem__(self, name):
        if not isinstance(name, str):
            return self._data.get(name)
        return self.__get(name, None, False, False)

    def __getattr__(self, name):
        return self.__getattribute__(name)

    def __contains__(self, name):
        return self._data.__contains__(name)

    def __getattribute__(self, name):
        if Flex.__reserved(name):
            return super(__class__, self).__getattribute__(name)
        try:
            return super(__class__, self).__getattribute__(name)
        except AttributeError:
            pass
        return self._data.get(name)

    def load(self, path, errors=True):
        d = read_json(path, errors=errors)
        try:
            if not isinstance(d, dict):
                if not errors:
                    raise ValueError("data is not a valid type")
                return False
            self.update(d)
        finally:
            del d
        return True

    def __setitem__(self, name, value):
        if Flex.__reserved(name):
            # NOTE(dij): Let's raise an error so we can catch anything attempting
            #            to add an invalid attribute.
            raise ValueError(f'cannot use reserved name "{name}"')
        if not isinstance(name, str):
            return self._data.__setitem__(name, value)
        return self.__get(name, value, True, False)

    def __get(self, name, value, set, set_non_exist):
        if "." not in name:
            if set or (set_non_exist and not self._data.__contains__(name)):
                if Flex.__reserved(name):
                    raise ValueError(f'cannot use reserved name "{name}"')
                self._data[name] = value
                return value
            return self._data.get(name, value)
        v = name.split(".")
        if (set or set_non_exist) and Flex.__reserved(v[0]):
            raise ValueError(f'cannot use reserved name "{v[0]}"')
        d = self._data.get(v[0])
        if d is None and not (set or set_non_exist):
            return value
        elif d is None:
            d = dict()
            self._data.__setitem__(v[0], d)
        for x in range(1, len(v) - 1):
            n = d.get(v[x])
            if n is None and not (set or set_non_exist):
                return value
            elif n is None:
                n = dict()
                d.__setitem__(v[x], n)
            d = n
            del n
        if not set:
            if d.__contains__(v[-1]):
                return d.get(v[-1])
            if set_non_exist:
                d.__setitem__(v[-1], value)
            del d
            return value
        d.__setitem__(v[-1], value)
        del d
        return value

    def get(self, name, default=None, set_non_exist=False):
        if not isinstance(name, str):
            return self._data.get(name, default)
        return self.__get(name, default, False, set_non_exist)

    def save(self, path, errors=True, indent=4, sort=True, perms=None):
        write_json(path, self._data, errors, indent, sort, perms)


class Storage(Flex):
    __slots__ = ("_file",)

    def __init__(self, path=None, load=False):
        Flex.__init__(self)
        self._file = path
        if load and self._file is not None:
            self.load()

    def path(self):
        return self._file

    def is_read_only(self):
        return self._data.get("_ro", False)

    def load(self, path=None, errors=True):
        super(__class__, self).load(path if nes(path) else self._file, errors)

    def save(self, path=None, errors=True, indent=4, sort=True, perms=None):
        super(__class__, self).save(
            path if nes(path) else self._file, errors, indent, sort, perms
        )

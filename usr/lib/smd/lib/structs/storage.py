#!/usr/bin/false
# The Storage class is the basis for all file based Python dictionaries.
# This class extends the "dict" class and has options for saving and loading data from files.
#
# All non-private (lacking "_" prefixes) attributes are treated as data from the internal dictionary.
# This allows a Storage class to have attributes set to the internal dictionary using standard Python conventions.
# The other functions, including the "get" function, allow for setting defaults while attempting to get information
# from the internal dictionary.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2021 iDigitalFlame
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


class Storage(dict):
    def __init__(self, data=None, file_path=None):
        dict.__init__(self)
        if isinstance(data, dict):
            self.update(data)
        self._file = file_path
        if self._file is not None and isfile(self._file):
            self.read(self._file, ignore_errors=False)

    def file(self):
        return self._file

    def __str__(self):
        return dumps(self, indent=4, sort_keys=True)

    def get_file(self):
        return self._file

    def __getitem__(self, name):
        item = self.__get_set(name, True, None, False)
        if item is None:
            raise KeyError(name)
        return item

    def __delattr__(self, name):
        if name is not None and len(name) > 0 and name[0] == "_":
            return super().__delattr__(name)
        if super().__contains__(name):
            return self.__delitem__(name)
        return super().__delattr__(name)

    def __getattr__(self, name):
        return self.__getattribute__(name)

    def set_file(self, file_path):
        self._file = file_path

    def __getattribute__(self, name):
        if name is not None and len(name) > 0 and name[0] == "_":
            return super().__getattribute__(name)
        if super().__contains__(name):
            return self.__getitem__(name)
        return super().__getattribute__(name)

    def get(self, name, default=None):
        return self.__get_set(name, True, default, False)

    def __setattr__(self, name, value):
        if name is not None and len(name) > 0 and name[0] == "_":
            return super().__setattr__(name, value)
        return self.__setitem__(name, value)

    def __setitem__(self, name, value):
        return self.__get_set(name, False, value, False)

    def __get_single(self, name, default):
        if default is not None and not super().__contains__(name):
            super().__setitem__(name, default)
            return default
        if super().__contains__(name):
            return super().__getitem__(name)
        return None

    def set(self, name, value, only_not_exists=False):
        return self.__get_set(name, False, value, only_not_exists)

    def read(self, file_path=None, ignore_errors=True):
        file = self._file if file_path is None else file_path
        data = read_json(file, ignore_errors=ignore_errors)
        if not isinstance(data, dict):
            if not ignore_errors:
                raise OSError(f'The data returned from "{file}" was not a Python dict!')
            del file
            return False
        del file
        self.update(data)
        del data
        return True

    def __set_single(self, name, value, only_not_exists):
        if only_not_exists and super().__contains__(name):
            return
        return super().__setitem__(name, value)

    def __get_set(self, name, get, value, only_not_exists):
        if "." not in name:
            if get:
                return self.__get_single(name, value)
            return self.__set_single(name, value, only_not_exists)
        subs = name.split(".")
        if len(subs) == 1:
            if get:
                return self.__get_single(subs[0], value)
            return self.__set_single(subs[0], value, only_not_exists)
        obj = dict()
        if super().__contains__(subs[0]):
            obj = super().__getitem__(subs[0])
        elif value is not None or not get:
            super().__setitem__(subs[0], obj)
        elif get:
            del obj
            del subs
            return value
        for x in range(1, len(subs) - 1):
            new = obj.get(subs[x])
            if new is None:
                new[subs[x]] = dict()
            obj = new
            del new
        name = subs[len(subs) - 1]
        del subs
        if only_not_exists and not get and name in obj:
            return value
        if not get or (value is not None and name not in obj):
            obj[name] = value
        elif get and name in obj:
            return obj[name]
        return value

    def write(
        self, file_path=None, indent=4, sort=True, ignore_errors=True, perms=None
    ):
        return write_json(
            self._file if file_path is None else file_path,
            self,
            indent,
            sort,
            ignore_errors,
            perms,
        )


class SafeStorage(Storage):
    def update(self, data):
        if "header" in data:
            del data["header"]
        if "multicast" in data:
            del data["multicast"]
        super().update(data)

    def __getattribute__(self, name):
        if name is not None and len(name) > 0 and name[0] == "_":
            return super().__getattribute__(name)
        if super().__contains__(name) and name != "set" and name != "get":
            return self.__getitem__(name)
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass
        return None

    def __setattr__(self, name, value):
        if name == "header" or name == "multicast":
            return
        super().__setattr__(name, value)

    def __setitem__(self, name, value):
        if name == "header" or name == "multicast":
            return
        super().__setitem__(name, value)

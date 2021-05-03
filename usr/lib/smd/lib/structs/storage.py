#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Storage class is the basis for all file based Python dictionaries.
# This class extends the "dict" class and has options for saving and loading data from files.
# All non-private (lacking "_" prefixes) attributes are treated as data from the internal dictionary.
# This allows a Storage class to have attributes set to the internal dictionary using standard Python conventions.
# The other functions, including the "get" function, allow for setting defaults while attempting to get infromation
# from the internal dictionary.

from json import dumps
from os.path import isfile
from lib.util import write_json, read_json


class Storage(dict):
    def __init__(self, data=None, file_path=None):
        dict.__init__(self)
        if isinstance(data, dict):
            self.update(data)
        self._file = file_path
        if isfile(self._file):
            self.read(self._file, ignore_errors=False)

    def file(self):
        return self._file

    def __str__(self):
        return dumps(self, indent=4, sort_keys=True)

    def get_file(self):
        return self._file

    def __delattr__(self, name):
        if name is not None and len(name) > 0 and name[0] == "_":
            super().__delattr__(name)
            return
        if super().__contains__(name):
            self.__delitem__(name)
            return
        super().__delattr__(name)

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
        if default is not None and not super().__contains__(name):
            self.__setitem__(name, default)
            return default
        if super().__contains__(name):
            return self.__getitem__(name)
        return None

    def __setattr__(self, name, value):
        if name is not None and len(name) > 0 and name[0] == "_":
            super().__setattr__(name, value)
        else:
            self.__setitem__(name, value)

    def read(self, file_path=None, ignore_errors=True):
        data = read_json(
            self._file if file_path is None else file_path, ignore_errors=ignore_errors
        )
        if not isinstance(data, dict):
            if not ignore_errors:
                raise OSError(
                    'The data returned from "%s" was not a Python dict!' % self._file
                    if file_path is None
                    else file_path
                )
            return False
        self.update(data)
        del data
        return True

    def write(self, file_path=None, indent=4, sort=True, ignore_errors=True):
        return write_json(
            self._file if file_path is None else file_path,
            self,
            indent,
            sort,
            ignore_errors,
        )

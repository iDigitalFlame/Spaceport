#!/usr/bin/false
# The Logger class is exactly as it sounds. This can create and mantain a
# logging instance to file and/or stdout.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2022 iDigitalFlame
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

from os import makedirs, chmod
from traceback import format_exc
from os.path import exists, isdir, dirname
from logging import getLogger, Formatter, StreamHandler, FileHandler
from lib.constants import LOG_FORMAT, LOG_NAMES, LOG_LEVELS, LOG_LEVEL


class Logger(object):
    def __init__(self, name, level="INFO", file=None):
        if not isinstance(level, str) or len(level) == 0:
            raise OSError('"level" must be a non-empty String!')
        self._log = getLogger(name)
        self._log.setLevel(level.upper())
        f = Formatter(LOG_FORMAT)
        s = StreamHandler()
        s.setFormatter(f)
        self._log.addHandler(s)
        del s
        if isinstance(file, str) and len(file) > 0:
            d = dirname(file)
            if not isdir(d) or not exists(d):
                try:
                    makedirs(d, exist_ok=True)
                except OSError as err:
                    raise OSError(f'Error creating log directory "{d}": {err}') from err
            del d
            try:
                h = FileHandler(file)
                h.setFormatter(f)
                h.setLevel(level.upper())
                self._log.addHandler(h)
                chmod(file, 0o0644, follow_symlinks=True)
            except OSError as err:
                raise OSError(f'Error creating log file "{file}": {err}') from err
            del h
        del f

    def set_level(self, log_level):
        c = LOG_NAMES.get(self._log.level, LOG_LEVEL)
        if isinstance(log_level, str):
            v = log_level.lower()
        else:
            v = str(log_level).lower()
        n = LOG_LEVELS.get(v, LOG_LEVEL)
        del v
        try:
            self._log.setLevel(n)
            for h in self._log.handlers:
                h.setLevel(n)
            self.info(f"Log level was changed from {c} to {n}!")
        except ValueError as err:
            self.error(f"Error setting log level to {n}!", err=err)
        del c
        del n

    def info(self, message, err=None):
        if err is not None:
            return self._log.info(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        self._log.info(message)

    def debug(self, message, err=None):
        if err is not None:
            return self._log.debug(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        self._log.debug(
            message,
        )

    def error(self, message, err=None):
        if err is not None:
            return self._log.error(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        self._log.error(message)

    def warning(self, message, err=None):
        if err is not None:
            return self._log.warning(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        self._log.warning(message)

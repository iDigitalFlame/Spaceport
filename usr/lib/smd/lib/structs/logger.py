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

# logger.py
#   The Logger class is exactly as it sounds. This can create and mantain a
#   simple logging instance to file and/or stdout.

from os import chmod
from lib.util import nes
from traceback import format_exc
from lib.util.file import ensure_dir
from lib.constants import LOG_INDEX, LOG_LEVELS, LOG_LEVELS_REVERSE
from logging import getLogger, Formatter, StreamHandler, FileHandler, addLevelName
from lib.constants.config import (
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_FRAME_LIMIT,
    LOG_FORMAT_JOURNAL,
)

_FORMAT = Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
_FORMAT_JOURNAL = Formatter(LOG_FORMAT_JOURNAL, datefmt="%Y-%m-%d %H:%M:%S")


class Logger(object):
    __slots__ = ("_log",)

    def __init__(self, name, level=LOG_LEVEL, file=None, journal=False):
        if isinstance(level, int):
            if level not in LOG_INDEX:
                raise ValueError(f'level "{level}" is invalid')
            v = level
        elif isinstance(level, str):
            if len(level) == 0:
                raise ValueError("level cannot be empty")
            v = LOG_LEVELS.get(level.lower(), LOG_LEVELS[LOG_LEVEL.lower()])
        else:
            raise ValueError(
                f'level must be a positive number or string (is "{type(level)}")'
            )
        # NOTE(dij): Change the names to be more "readable" in log output.
        #            This is safe to be called multiple times if needed.
        for i, n in LOG_INDEX.items():
            addLevelName(i, n)
        self._log = getLogger(name)
        self._log.setLevel(v)
        del v
        s = StreamHandler()
        s.setFormatter(_FORMAT_JOURNAL if journal else _FORMAT)
        self._log.addHandler(s)
        self._log.level
        del s
        if not nes(file):
            return
        try:
            ensure_dir(file)
        except OSError as err:
            raise OSError(f'cannot create log directory for "{file}": {err}')
        try:
            f = FileHandler(file)
            f.setFormatter(_FORMAT)
            f.setLevel(self._log.level)
            self._log.addHandler(f)
            chmod(file, 0o0644, follow_symlinks=True)
            del f
        except OSError as err:
            raise OSError(f'cannot create log file "{file}": {err}')

    def info(self, message, err=None):
        if err is not None:
            return self._log.info(
                f"{message} ({err})\n{format_exc(limit=LOG_FRAME_LIMIT)}"
            )
        self._log.info(message)

    def debug(self, message, err=None):
        if err is not None:
            return self._log.debug(
                f"{message} ({err})\n{format_exc(limit=LOG_FRAME_LIMIT)}"
            )
        self._log.debug(message)

    def error(self, message, err=None):
        if err is not None:
            return self._log.error(
                f"{message} ({err})\n{format_exc(limit=LOG_FRAME_LIMIT)}"
            )
        self._log.error(message)

    def warning(self, message, err=None):
        if err is not None:
            return self._log.warning(
                f"{message} ({err})\n{format_exc(limit=LOG_FRAME_LIMIT)}"
            )
        self._log.warning(message)

    def set_level(self, log_level, notify=True):
        if log_level is None:
            return self.error("[log]: Log level cannot be None!")
        if isinstance(log_level, int):
            if log_level not in LOG_INDEX:
                return self.error(f'[log]: Log level "{log_level}" is invalid!')
            n = log_level
        elif isinstance(log_level, str):
            if len(log_level) == 0:
                return self.error("[log]: Log level name cannot be empty!")
            n = LOG_LEVELS.get(log_level.lower())
            if n is None:
                return self.error(f'[log]: Log level "{log_level}" is invalid!')
        else:
            return self.error(
                f'[log]: Log level must a level number or name (is "{type(log_level)}")!'
            )
        if n == self._log.level:
            return
        p = LOG_LEVELS_REVERSE.get(self._log.level, LOG_LEVEL)
        k = LOG_LEVELS_REVERSE.get(n, LOG_LEVEL)
        try:
            self._log.setLevel(n)
            for h in self._log.handlers:
                h.setLevel(n)
            if notify:
                self.info(f'[log]: Log level was changed from "{p}" to "{k}"!')
        except ValueError as err:
            self.error(f'[log]: Cannot set Log level to "{k}"!', err)
        del p, n, k

#!/usr/bin/false
# The Logger class is exactly as it sounds. This can create and mantain a
# logging instance to file and/or stdout.
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

from os import makedirs, chmod
from traceback import format_exc
from os.path import exists, isdir, dirname
from logging import getLogger, Formatter, StreamHandler, FileHandler
from lib.constants import LOG_FORMAT, LOG_NAMES, LOG_LEVELS, LOG_LEVEL


class Logger(object):
    def __init__(self, log_name, log_level="INFO", log_file=None):
        if not isinstance(log_level, str) or len(log_level) == 0:
            raise OSError('Parameter "log_level" must be a non-empty Python str!')
        self._log = getLogger(log_name)
        self._log.setLevel(log_level.upper())
        formatter = Formatter(LOG_FORMAT)
        stream = StreamHandler()
        stream.setFormatter(formatter)
        self._log.addHandler(stream)
        del stream
        if isinstance(log_file, str) and len(log_file) > 0:
            log_dir = dirname(log_file)
            if not isdir(log_dir) or not exists(log_dir):
                try:
                    makedirs(log_dir, exist_ok=True)
                except OSError as err:
                    raise OSError(f'Failed to create log file "{log_file}"! ({err})')
            del log_dir
            try:
                file = FileHandler(log_file)
                file.setFormatter(formatter)
                file.setLevel(log_level.upper())
                self._log.addHandler(file)
                chmod(log_file, 0o644, follow_symlinks=True)
            except OSError as err:
                raise OSError(f'Failed to create log file "{log_file}"! ({err})')
            else:
                del file
        del formatter

    def set_level(self, log_level):
        last = "INVALID"
        level = LOG_LEVEL
        if self._log.level in LOG_NAMES:
            last = LOG_NAMES[self._log.level]
        if isinstance(log_level, str):
            level_value = log_level.lower()
        else:
            level_value = str(log_level).lower()
        if level_value in LOG_LEVELS:
            level = LOG_LEVELS[level_value]
        del level_value
        self._log.setLevel(level)
        for h in self._log.handlers:
            h.setLevel(level)
        self.info(f"Log level was changed from {last} to {level}!")
        del last
        del level

    def info(self, message, err=None):
        if err is not None:
            self._log.info(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        else:
            self._log.info(message)

    def debug(self, message, err=None):
        if err is not None:
            self._log.debug(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        else:
            self._log.debug(message)

    def error(self, message, err=None):
        if err is not None:
            self._log.error(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        else:
            self._log.error(message)

    def warning(self, message, err=None):
        if err is not None:
            self._log.warning(f"{message} ({str(err)})\n{format_exc(limit=3)}")
        else:
            self._log.warning(message)

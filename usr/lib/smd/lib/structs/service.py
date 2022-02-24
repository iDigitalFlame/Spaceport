#!/usr/bin/false
# The Service class is the base object for Daemon threads that run
# such as the client and system daemons. This allows the daemons to share
# common functions, such as logging and dispatching.
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

from os import getpid
from pprint import pformat
from signal import signal, SIGALRM
from lib.structs.logger import Logger
from lib.structs.storage import Storage
from lib.structs.dispatcher import Dispatcher


class Service(Storage):
    def __init__(self, name, modules, config, level, file, read_only=False):
        Storage.__init__(self, path=config)
        self._loaded = False
        self._log = Logger(
            name,
            level,
            file.replace("{pid}", str(getpid())).replace("{name}", name),
        )
        self._read_only = read_only
        self._log.info(f'Service "{name}" starting up init functions..')
        self._dispatcher = Dispatcher(self, modules)
        signal(SIGALRM, self._watchdog)

    def _load(self):
        self._log.debug(f'Loading configuration from "{self.get_file()}"..')
        try:
            self.read()
        except OSError as err:
            self._log.error(
                f'Error loading configuration "{self.get_file()}", using defaults!',
                err=err,
            )
        self._loaded = True

    def is_server(self):
        return False

    def forward(self, message):
        if message is None:
            return
        message["forward"] = True
        self._log.debug(f"Sending message 0x{message.header():02X} to internal Hooks.")
        self._dispatcher.add(None, message)

    def send(self, eid, result):
        pass

    def _watchdog(self, _, frame):
        self._log.error(
            f'Received a Watchdog timeout for "{frame.f_code.co_name}" '
            f"({frame.f_code.co_filename}:{frame.f_lineno}) [{pformat(frame.f_locals, indent=4)}]"
        )

    def set_level(self, log_level):
        self._log.set_level(log_level)

    def get(self, name, default=None):
        if not self._loaded:
            self._load()
        return super(__class__, self).get(name, default)

    def info(self, message, err=None):
        self._log.info(message, err)

    def debug(self, message, err=None):
        self._log.debug(message, err)

    def error(self, message, err=None):
        self._log.error(message, err)

    def warning(self, message, err=None):
        self._log.warning(message, err)

    def notify(self, title, message=None, icon=None):
        pass

    def set(self, name, value, only_not_exists=False):
        if not self._loaded:
            self._load()
        return super(__class__, self).set(name, value, only_not_exists)

    def get_config(self, name, default=None, save=False):
        r = self.get(name, default)
        if save and not self._read_only:
            try:
                self.write(perms=0o640)
            except OSError as err:
                self.error(f'Error saving configuration "{self.get_file()}"!', err=err)
        return r

    def set_config(self, name, value, save=False, only_not_exists=False):
        r = self.set(name, value, only_not_exists)
        if save and not self._read_only:
            try:
                self.write(perms=0o640)
            except OSError as err:
                self.error(f'Error saving configuration "{self.get_file()}"!', err=err)
        return r

    def write(self, path=None, indent=4, sort=True, perms=None, errors=True):
        if self._read_only:
            return
        return super(__class__, self).write(path, indent, sort, perms, errors)

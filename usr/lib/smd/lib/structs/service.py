#!/usr/bin/false
# The Service class is the base object for Daemon threads that run
# such as the client and system daemons. This allows the daemons to share
# common functions, such as logging and dispatching.
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

from os import getpid
from pprint import pformat
from signal import signal, SIGALRM
from lib.structs.logger import Logger
from lib.structs.storage import Storage
from lib.structs.dispatcher import Dispatcher


class Service(Storage):
    def __init__(self, name, modules, config, log_level, log_path):
        Storage.__init__(self, file_path=config)
        self._loaded = False
        self._log = Logger(
            name,
            log_level,
            log_path.replace("{pid}", str(getpid())).replace("{name}", name),
        )
        self._log.info(f'Service "{name}" starting up init functions..')
        self._dispatcher = Dispatcher(self, modules)
        signal(SIGALRM, self._watchdog)

    def is_server(self):
        return False

    def forward(self, message):
        message["forward"] = True
        self._log.debug(f"Sending message 0x{message.header():02X} to internal Hooks.")
        self._dispatcher.add(None, message)

    def _watchdog(self, _, frame):
        self._log.error(
            f'Received a Watchdog timeout for "{frame.f_code.co_name}" '
            f"({frame.f_code.co_filename}:{frame.f_lineno}) [{pformat(frame.f_locals, indent=4)}]"
        )

    def set_level(self, log_level):
        self._log.set_level(log_level)

    def get(self, name, default=None):
        if not self._loaded:
            self._log.debug(f'Loading configuration from file "{self.get_file()}"..')
            try:
                self.read(ignore_errors=False)
            except OSError as err:
                self._log.error(
                    f'Could not load configuration file "{self.get_file()}", using defaults!',
                    err=err,
                )
            self._loaded = True
        return super().get(name, default)

    def info(self, message, err=None):
        self._log.info(message, err)

    def debug(self, message, err=None):
        self._log.debug(message, err)

    def error(self, message, err=None):
        self._log.error(message, err)

    def send(self, eid, message_result):
        pass

    def warning(self, message, err=None):
        self._log.warning(message, err)

    def notify(self, title, message=None, icon=None):
        pass

    def get_config(self, name, default=None, save=False):
        result = self.get(name, default)
        if save:
            try:
                self.write(ignore_errors=False, perms=0o640)
            except OSError as err:
                self.error(
                    f'Could not save configuration file "{self.get_file()}"!', err=err
                )
        return result

    def set_config(self, name, value, save=False, only_not_exists=False):
        if not self._loaded:
            self._log.debug(f'Loading configuration from file "{self.get_file()}"..')
            try:
                self.read(ignore_errors=False)
            except OSError as err:
                self._log.error(
                    f'Could not load configuration file "{self.get_file()}", using defaults!',
                    err=err,
                )
            self._loaded = True
        result = self.set(name, value, only_not_exists)
        if save:
            try:
                self.write(ignore_errors=False, perms=0o640)
            except OSError as err:
                self.error(
                    f'Could not save configuration file "{self.get_file()}"!', err=err
                )
        return result

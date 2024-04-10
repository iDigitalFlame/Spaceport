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

# service.py
#   The Service class is the base object for Daemon threads that run
#   such as the client and system daemons. This allows the daemons to share
#   common functions, such as logging and dispatching.

import threading

from lib.util import nes
from pprint import pformat
from lib.util.file import perm_check
from lib.structs.logger import Logger
from lib.structs.storage import Storage
from signal import signal, SIGALRM, SIGINT
from os import getgid, getpid, getuid, kill
from lib.constants.config import LOG_PAYLOAD
from lib.structs.dispatcher import Dispatcher


class Service(object):
    __slots__ = ("config", "_log", "_pid", "_uid", "_read_only", "_dispatcher")

    def __init__(self, name, modules, config, level, log, ro=False, journal=False):
        self._uid, self._pid = getuid(), getpid()
        self._log = Logger(
            name,
            10,
            (
                log.replace("{uid}", f"{self._uid}")
                .replace("{pid}", f"{self._pid}")
                .replace("{name}", name)
                if nes(log)
                else None
            ),
            journal,
        )
        self._read_only = ro
        self._log.info(f'[service]: "{name}" starting up..')
        self._log.set_level(level)
        self._dispatcher = Dispatcher(self, modules)
        self.config = Storage(config)
        signal(SIGALRM, self._watchdog)
        threading.excepthook = self._thread_except

    def save(self):
        if self._read_only:
            return self._log.debug(
                f'[service]: Not saving configuration to "{self.config.path()}" as "read_only" is True.'
            )
        self._log.debug(f'[service]: Saving configuration to "{self.config.path()}"..')
        try:
            self.config.save(perms=0o0640)
        except (ValueError, OSError) as err:
            self._log.error(
                f'[service]: Cannot save configuration file "{self.config.path()}"!',
                err,
            )

    def load(self):
        self._log.debug(
            f'[service]: Loading configuration from "{self.config.path()}"..'
        )
        try:
            # NOTE(dij): Allow SGID here.
            perm_check(self.config.path(), 0o4137, self._uid, getgid())
            self.config.load()
            if self.config.is_read_only() and not self._read_only:
                self._read_only = True
        except (ValueError, OSError) as err:
            self._log.error(
                f'[service]: Cannot load configuration "{self.config.path()}", using default values!',
                err,
            )

    def is_server(self):
        return False

    def cancel(self, event):
        return self._dispatcher.cancel_task(event)

    def forward(self, message):
        if message is None:
            return
        message.set_forward(self._pid, self._uid)
        self._log.debug(
            f"[service]: Forwarding message 0x{message.header():02X} to internal Hooks."
        )
        if LOG_PAYLOAD:
            self._log.error(f"[dump]: FWD > {message}")
        self._dispatcher.add(None, message)

    def set(self, name, value):
        return self.config.set(name, value)

    def _watchdog(self, _, frame):
        self._log.error(
            f'[service]: Received a Watchdog timeout for "{frame.f_code.co_name}" '
            f"({frame.f_code.co_filename}:{frame.f_lineno}) [{pformat(frame.f_locals, indent=4)}]"
        )

    def _thread_except(self, args):
        self._log.error(
            f"[service]: Received a Thread error {args.exc_type} ({args.exc_value})!",
            err=args.exc_value,
        )
        kill(self._pid, SIGINT)

    def info(self, message, err=None):
        self._log.info(message, err)

    def debug(self, message, err=None):
        self._log.debug(message, err)

    def error(self, message, err=None):
        self._log.error(message, err)

    def set_log_level(self, log_level):
        self._log.set_level(log_level)

    def warning(self, message, err=None):
        self._log.warning(message, err)

    def watch(self, proc, func=None, args=(), kwargs={}):
        self._dispatcher.watch_process(proc, func, args, kwargs)

    def get(self, name, default=None, set_non_exist=False):
        return self.config.get(name, default, set_non_exist)

    def task(self, timeout, func, args=(), kwargs={}, priority=10):
        return self._dispatcher.add_task(timeout, func, args, kwargs, priority)

#!/usr/bin/false
# Module: Polybar (User)
#
# Manages the Polybar process.
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

from os import environ
from lib.util import stop
from signal import SIGCONT, SIGSTOP
from subprocess import Popen, DEVNULL, SubprocessError
from lib.constants import (
    EMPTY,
    HOOK_LOCK,
    HOOK_DAEMON,
    HOOK_ROTATE,
    HOOK_RELOAD,
    ROTATE_LEFT,
    ROTATE_RIGHT,
    HOOK_DISPLAY,
    HOOK_SHUTDOWN,
    ROTATE_NORMAL,
    ROTATE_INVERTED,
    DEFAULT_POLYBAR_NAME,
)

HOOKS = {
    HOOK_LOCK: "Polybar.freeze",
    HOOK_DAEMON: "Polybar.thread",
    HOOK_ROTATE: "Polybar.update",
    HOOK_RELOAD: "Polybar.reload",
    HOOK_DISPLAY: "Polybar.update",
    HOOK_SHUTDOWN: "Polybar.update",
}


class Polybar(object):
    def __init__(self):
        self.bars = dict()
        self.failures = 5
        self.current = None
        self.process = None
        self.default = None
        self.stopped = False

    def setup(self, server):
        self.default = server.get_config("polybar.default", DEFAULT_POLYBAR_NAME, True)
        server.get_config("polybar.bars", dict(), True)
        self.bars = {
            ROTATE_LEFT: server.get_config("polybar.bars.left", EMPTY, True),
            ROTATE_RIGHT: server.get_config("polybar.bars.right", EMPTY, True),
            ROTATE_NORMAL: server.get_config("polybar.bars.normal", EMPTY, True),
            ROTATE_INVERTED: server.get_config("polybar.bars.inverted", EMPTY, True),
        }
        b = self.bars[ROTATE_NORMAL]
        if not isinstance(b, str) or len(b) == 0:
            self.current = self.default
        else:
            self.current = b
        del b

    def thread(self, server):
        if self.process is None or (
            self.process is not None and self.process.poll() is not None
        ):
            self._setup_bar(server, self.stopped)

    def reload(self, server):
        self.failures = 5
        self.stopped = True
        self._setup_bar(server, True)
        self.setup(server)
        self.stopped = False

    def _get_bar(self, message):
        if message is None or message.header() != HOOK_ROTATE:
            return self.default
        if message.position == ROTATE_LEFT:
            return self.bars.get(ROTATE_LEFT)
        elif message.position == ROTATE_RIGHT:
            return self.bars.get(ROTATE_RIGHT)
        elif message.position == ROTATE_NORMAL:
            return self.bars.get(ROTATE_NORMAL)
        elif message.position == ROTATE_INVERTED:
            return self.bars.get(ROTATE_INVERTED)
        return self.default

    def freeze(self, server, message):
        if self.process is None or self.process.poll() is not None:
            return
        if message.trigger is not None:
            try:
                self.process.send_signal(SIGSTOP)
            except OSError as err:
                server.error(
                    "Attempting to freeze Polybar raised an exception!", err=err
                )
            else:
                server.debug("Freezing Polybar due to lockscreen.")
            return
        try:
            self.process.send_signal(SIGCONT)
        except OSError as err:
            server.error(
                "Attempting to un-freeze Polybar raised an exception!", err=err
            )
        else:
            server.debug("Unfreezing Polybar due to lockscreen removal.")

    def update(self, server, message):
        if message.header() == HOOK_ROTATE:
            self.current = self._get_bar(message)
            if self.current is None or len(self.current) == 0:
                self.current = self.default
        if message.header() == HOOK_SHUTDOWN:
            self.failures = 0
            self.stopped = True
            return self._setup_bar(server, True)
        self._setup_bar(server, False)

    def _setup_bar(self, server, kill=False):
        if self.process is not None and self.process.poll() is None:
            stop(self.process)
            self.process = None
        if kill:
            return
        if self.failures <= 0:
            return
        if self.process is not None and self.process.returncode != 0:
            self.failures -= 1
            if self.failures <= 0:
                return server.error(
                    "Max number of Polybar errors occurred! Use the reload command to restart Polybar!"
                )
            else:
                server.warning(
                    f"Polybar returned an error upon close! Will restart again {self.failures} "
                    f"times before a reload is required!"
                )
        server.debug(f'Attempting to start Polybar with bar "{self.current}"..')
        try:
            self.process = Popen(
                ["/usr/bin/polybar", "-q", self.current],
                env=environ,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
        except (OSError, SubprocessError) as err:
            server.error("Attempting to start Polybar raised an exception!", err=err)

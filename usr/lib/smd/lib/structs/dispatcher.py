#!/usr/bin/false
# The Dispatcher class functions simple in a way to help manage
# Hook and function calls by the hosting Service object.
#
# This class is a thread that waits until an order is given and will
# then process the messages in a FIFO order.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2023 iDigitalFlame
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

from threading import Thread, Event
from lib.loader import load_modules
from lib.structs.hook import HookDaemon
from lib.structs.message import Message
from lib.constants import (
    HOOK_OK,
    HOOK_LOG,
    LOG_LEVEL,
    HOOK_DAEMON,
    HOOK_RELOAD,
    HOOK_STARTUP,
    HOOK_SHUTDOWN,
)


class Dispatcher(Thread):
    def __init__(self, service, directory):
        Thread.__init__(self, name="SMDDispatcherThread", daemon=False)
        self._hooks = None
        self._daemons = None
        self._dir = directory
        self._running = False
        self._service = service
        self._messages = list()
        self._waiting = Event()

    def run(self):
        self._running = True
        self._waiting.clear()
        self._service.debug("Starting Dispatcher processing thread..")
        self._hooks = load_modules(self._service, self._dir)
        if HOOK_STARTUP in self._hooks:
            self._service.debug("Running Startup Hooks..")
            r = self._hooks[HOOK_STARTUP].run(self._service, Message(HOOK_STARTUP))
            if len(r) > 0:
                self._service.send(None, r)
            del r
        try:
            self._service.write()
        except OSError as err:
            self._service.error(
                f'Error saving configuration "{self._service.get_file()}"!', err=err
            )
        if HOOK_DAEMON in self._hooks:
            self._daemons = HookDaemon(self._service, self._hooks[HOOK_DAEMON])
            self._daemons.start()
        while self._running:
            if len(self._messages) == 0:
                self._waiting.clear()
            self._waiting.wait()
            while len(self._messages) > 0:
                m = self._messages.pop()
                if not m.is_valid():
                    self._service.warning("Received an invalid Message!")
                    del m
                    continue
                if m.message.header() == HOOK_LOG:
                    self
                    self._service.set_level(m.message.get("level", LOG_LEVEL))
                    if self._service.is_server() and not m.message.is_multicast():
                        self._service.info("Forwarding log message to clients..")
                        self._service.send(None, m.message.set_multicast())
                    del m
                    continue
                if m.message.header() == HOOK_RELOAD:
                    self._service.debug(
                        f'Reloading the configuration from "{self._service.get_file()}"..'
                    )
                    try:
                        self._service.read()
                    except OSError as err:
                        self._service.error(
                            f'Error reading configuration "{self._service.get_file()}"!',
                            err=err,
                        )
                if m.message.header() not in self._hooks:
                    if m.message.header() != HOOK_OK:
                        self._service.warning(
                            f"Received an un-hooked Message 0x{m.message.header():02X}!"
                        )
                    del m
                    continue
                try:
                    self._service.debug(
                        f"Running Hooks for 0x{m.message.header():02X}."
                    )
                    r = self._hooks[m.message.header()].run(self._service, m.message)
                    if len(r) > 0:
                        self._service.send(m.eid, r)
                    del r
                except Exception as err:
                    self._service.error("Error processing Message request!", err=err)
                finally:
                    del m
        if not self._running:
            return
        self.stop()

    def stop(self):
        self._service.debug("Stopping Dispatcher thread..")
        if HOOK_SHUTDOWN in self._hooks:
            self._service.debug("Running shutdown hooks..")
            self._hooks[HOOK_SHUTDOWN].run(self._service, Message(header=HOOK_SHUTDOWN))
        try:
            self._service.write()
        except OSError as err:
            self._service.error(
                f'Could not save configuration "{self._service.get_file()}"!', err=err
            )
        self._running = False
        self._waiting.set()
        if self._daemons is None:
            return
        self._daemons.stop()

    def add(self, eid, message):
        if not self._running:
            return
        self._messages.append(DispatchMessage(eid, message))
        self._waiting.set()


class DispatchMessage(object):
    def __init__(self, eid, message):
        self.eid = eid
        self.message = message

    def is_valid(self):
        return isinstance(self.message, Message) and isinstance(
            self.message.header(), int
        )

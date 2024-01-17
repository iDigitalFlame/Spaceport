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

# dispatcher.py
#   The Dispatcher allows for dynamic and asynchronous calling of various functions
#   loaded. The Dispatcher also manages the scheduler and any process functions.

from signal import alarm
from sched import scheduler
from time import time, sleep
from lib.util.exec import stop
from threading import Thread, Event
from lib.loader import load_modules
from lib.structs.message import Message
from lib.constants.config import LOG_LEVEL, TIMEOUT_SEC_STOP, TIMEOUT_SEC_HOOK
from lib.constants import (
    HOOK_OK,
    HOOK_LOG,
    HOOK_DAEMON,
    HOOK_RELOAD,
    HOOK_STARTUP,
    HOOK_SHUTDOWN,
)


class Dispatcher(Thread):
    __slots__ = (
        "_dir",
        "_hooks",
        "_service",
        "_running",
        "_waiting",
        "_messages",
        "_complete",
        "_executer",
    )

    def __init__(self, service, directory):
        Thread.__init__(self, name="SMD_Dispatcher", daemon=False)
        self._dir = directory
        self._hooks = None
        self._service = service
        self._running = Event()
        self._waiting = Event()
        self._messages = list()
        self._complete = Event()
        self._executer = DispatchExecuter(service)

    def run(self):
        self._service.debug("[dispatch]: Starting processing Thread..")
        self._service.load()
        self._hooks = load_modules(self._service, self._dir)
        if HOOK_DAEMON in self._hooks:
            self._executer._hooks = self._hooks[HOOK_DAEMON]
            del self._hooks[HOOK_DAEMON]
        if HOOK_STARTUP in self._hooks:
            self._service.debug("[dispatch]: Running Startup Hooks..")
            r = self._hooks[HOOK_STARTUP].run(self._service, Message(HOOK_STARTUP))
            if len(r) > 0:
                self._service.send(None, r)
            del r
        self._service.save()
        # NOTE(dij): Don't trigger the daemon until now.
        self._executer.start()
        while not self._running.is_set():
            if len(self._messages) == 0:
                self._waiting.clear()
            self._waiting.wait()
            while len(self._messages) > 0:
                self._process(self._messages.pop())
        self._service.debug("[dispatch]: Stopping processing Thread..")
        if HOOK_SHUTDOWN in self._hooks:
            self._service.debug("[dispatch]: Running shutdown Hooks..")
            self._hooks[HOOK_SHUTDOWN].run(self._service, Message(HOOK_SHUTDOWN))
        self._service.save()
        self._executer.stop()
        self._complete.set()

    def stop(self):
        self._running.set()
        self._waiting.set()
        self._complete.wait(TIMEOUT_SEC_STOP)

    def _process(self, msg):
        if not msg.is_valid():
            return self._service.warning("[dispatch]: Invalid Message received!")
        if msg.header() == HOOK_LOG:
            self._service.set_log_level(msg.data.get("level", LOG_LEVEL))
            if self._service.is_server() and not msg.data.is_multicast():
                self._service.info(
                    f"[dispatch/0x{msg.header():02X}]: Forwarding Log request to clients.."
                )
                self._service.send(None, msg.data.multicast())
            return
        if msg.header() == HOOK_RELOAD:
            self._service.debug(
                f'[dispatch/0x{msg.header():02X}]: Reloading the configuration "{self._service.config.path()}"..'
            )
            self._service.load()
        if msg.header() not in self._hooks:
            if msg.header() != HOOK_OK:
                self._service.warning(
                    f"[dispatch/0x{msg.header():02X}]: Received an un-hooked request 0x{msg.header():02X}!"
                )
            return
        try:
            self._service.debug(f"[dispatch/0x{msg.header():02X}]: Running Hooks..")
            r = self._hooks[msg.header()].run(self._service, msg.data)
            if len(r) > 0:
                self._service.send(msg.eid, r)
            del r
        except Exception as err:
            self._service.error(
                f"[dispatch/0x{msg.header():02X}]: Cannot process request!",
                err,
            )

    def add(self, eid, message):
        if self._running.is_set():
            return
        self._messages.append(DispatchMessage(eid, message))
        self._waiting.set()

    def cancel_task(self, event):
        if (
            event is None
            or self._executer is None
            or self._executer._sched is None
            or self._executer._sched.empty()
        ):
            return False
        try:
            self._executer._sched.cancel(event)
        except ValueError:
            return False
        return True

    def watch_process(self, proc, func=None, args=(), kwargs={}):
        if proc is None or self._running.is_set():
            return
        if not callable(func):
            self._executer._watch.append((proc, None, None, None))
        else:
            self._executer._watch.append((proc, func, args, kwargs))

    def add_task(self, timeout, func, args=(), kwargs={}, priority=10):
        if self._running.is_set():
            return
        if self._executer._sched is None:
            self._executer._sched = scheduler(timefunc=time, delayfunc=sleep)
        return self._executer._sched.enter(timeout, priority, func, args, kwargs)


class DispatchMessage(object):
    __slots__ = ("eid", "data")

    def __init__(self, eid, message):
        self.eid = eid
        self.data = message

    def header(self):
        return self.data.header()

    def is_valid(self):
        return isinstance(self.data, Message) and isinstance(self.data.header(), int)


class DispatchExecuter(Thread):
    __slots__ = ("_sched", "_hooks", "_watch", "_service", "_signal", "_complete")

    def __init__(self, service):
        Thread.__init__(self, name="SMD_DispatchExecuter", daemon=False)
        self._sched = None
        self._hooks = None
        self._watch = list()
        self._signal = Event()
        self._service = service
        self._complete = Event()

    def run(self):
        self._service.debug("[dispatch/exec]: Starting processing Thread..")
        while not self._signal.is_set():
            for h in self._hooks:
                h.run(self._service, None, None)
            self._run_sched()
            self._check_entries()
            self._signal.wait(1)
        self._service.debug("[dispatch/exec]: Stopping processing Thread..")
        if self._sched is not None:
            for i in self._sched.queue:
                self._sched.cancel(i)
            self._sched = None
            del self._sched
        if len(self._watch) > 0:
            for i in self._watch:
                stop(i)
            self._watch.clear()
        self._complete.set()

    def stop(self):
        self._signal.set()
        self._complete.wait(TIMEOUT_SEC_STOP)

    def start(self):
        if self._hooks is not None and len(self._hooks) == 0:
            raise RuntimeError()
        if self._hooks is None:
            self._hooks = list()
        super(__class__, self).start()

    def _run_sched(self):
        if self._sched is None or self._sched.empty():
            return
        alarm(TIMEOUT_SEC_HOOK)
        self._sched.run(blocking=False)
        alarm(0)

    def _check_entries(self):
        if len(self._watch) == 0:
            return
        alarm(TIMEOUT_SEC_HOOK)
        for i in self._watch:
            if not isinstance(i, tuple):
                self._watch.remove(i)
                continue
            if i[0].poll() is None:
                continue
            # NOTE(dij): Call a "stop" function if it exists.
            try:
                f = getattr(i[0], "stop")
                if callable(f):
                    f()
                del f
            except (AttributeError, TypeError):
                pass
            stop(i[0])
            self._watch.remove(i)
            if not callable(i[1]):
                continue
            try:
                i[1](*i[2], **i[3])
            except Exception as err:
                self._service.error(
                    "[dispatch/exec]: Cannot execute process callback!", err
                )
        alarm(0)

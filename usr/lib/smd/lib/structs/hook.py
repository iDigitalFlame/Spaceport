#!/usr/bin/false
# The Hook class contains all the primary functions for storing and running hook
# functions.  This class container allows for invocation of multiple hooks using
# a single function call.
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

from signal import alarm
from threading import Thread, Event
from lib.structs.message import Message, send_exception
from lib.constants import HOOK_OK, HOOK_THREAD_TIMEOUT, LOG_TICKS


class Hook(object):
    def __init__(self, hook_object, hook_func, hook_class):
        self._func = hook_func
        self._class = hook_class
        self._argcount = hook_func.__code__.co_argcount
        if hook_object is None:
            self._argcount += 1

    def run(self, service, message, queue):
        if LOG_TICKS:
            service.debug(
                f'Running function "{self._func.__name__}" of "{self._class.__name__}".'
            )
        if self._func is None or not callable(self._func):
            service.warning(
                f'Hook for "{self._class.__name__}" has a missing function!'
            )
            return False
        if self._argcount == 5:
            try:
                service.warning(
                    f'Function "{self._func.__name__}" of Hook for "{self._class.__name__}" '
                    f"is using the old format, please convert it!"
                )
                r = self._func(service, None, queue, message)
            except Exception as err:
                service.error(
                    f'Error calling function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err=err,
                )
                if isinstance(queue, list):
                    queue.append(send_exception(message.header(), err))
                return False
        elif self._argcount == 4:
            try:
                r = self._func(service, message, queue)
            except Exception as err:
                service.error(
                    f'Error calling function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err=err,
                )
                if isinstance(queue, list):
                    queue.append(send_exception(message.header(), err))
                return False
        elif self._argcount == 3:
            try:
                r = self._func(service, message)
            except Exception as err:
                service.error(
                    f'Error calling function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err=err,
                )
                if isinstance(queue, list):
                    queue.append(send_exception(message.header(), err))
                return False
        elif self._argcount == 2:
            try:
                r = self._func(service)
            except Exception as err:
                service.error(
                    f'Error calling function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err=err,
                )
                if isinstance(queue, list):
                    queue.append(send_exception(message.header(), err))
                return False
        else:
            try:
                r = self._func()
            except Exception as err:
                service.error(
                    f'Error calling function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err=err,
                )
                if isinstance(queue, list):
                    queue.append(send_exception(message.header(), err))
                return False
        if r is None:
            return True
        if isinstance(r, Message):
            queue.append(r)
        elif isinstance(r, dict):
            queue.append(Message(message.header(), r))
        elif isinstance(r, str):
            queue.append(Message(message.header(), {"result": r}))
        elif isinstance(r, bool):
            if r:
                queue.append(Message(HOOK_OK))
            else:
                queue.append(Message(HOOK_OK, {"error": "An unknown error occurred"}))
        elif isinstance(r, int):
            queue.append(Message(header=r))
        elif isinstance(r, list) or isinstance(r, tuple):
            for s in r:
                if isinstance(s, Message):
                    queue.append(s)
                elif isinstance(s, dict):
                    queue.append(Message(message.header(), s))
                elif isinstance(s, str):
                    queue.append(Message(message.header(), {"result": s}))
        else:
            service.warning(
                f'The return result for function "{self._func.__name__}" of Hook '
                f'for "{self._class.__name__}" was not able to be parsed!'
            )
        del r
        return True


class HookList(list):
    def __init__(self):
        list.__init__(self)

    def run(self, service, message):
        q = list()
        alarm(HOOK_THREAD_TIMEOUT)
        for h in self:
            h.run(service, message, q)
        alarm(0)
        return q


class HookDaemon(Thread):
    def __init__(self, service, hooks):
        Thread.__init__(self, name="SMBHooksThread", daemon=False)
        self._hooks = hooks
        self._service = service
        self._running = Event()

    def run(self):
        self._running.clear()
        self._service.debug("Starting Hooks Thread..")
        while not self._running.is_set():
            for h in self._hooks:
                h.run(self._service, None, None)
            self._running.wait(1)
        self._service.debug("Stopping Hooks Thread..")

    def stop(self):
        self._running.set()

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

# hook.py
#   Hooks contains all the primary functions for storing and running hook or loaded
#   functions. This class container allows for invocation of multiple hooks using
#   a single function call.

from signal import alarm
from lib.constants import HOOK_OK, HOOK_ERROR
from lib.structs.message import Message, as_exception
from lib.constants.config import TIMEOUT_SEC_HOOK, LOG_TICKS


class Hook(object):
    __slots__ = ("_args", "_func", "_class")

    def __init__(self, obj, func, cls):
        self._func = func
        self._args = func.__code__.co_argcount
        self._class = cls
        if obj is None:
            self._args += 1

    def run(self, service, message, queue):
        if LOG_TICKS:
            service.debug(
                f'[hook]: Running function "{self._func.__name__}" of "{self._class.__name__}".'
            )
        r, s = self._exec(service, message, queue)
        if not s:
            return False
        if r is None:
            return True
        if isinstance(r, Message):
            queue.append(r)
        elif isinstance(r, bool):
            if r:
                queue.append(Message(HOOK_OK))
            else:
                queue.append(Message(HOOK_ERROR, {"error": "unknown error occurred"}))
        elif isinstance(r, int):
            queue.append(Message(r))
        elif isinstance(r, dict):
            queue.append(Message(message.header(), r))
        elif isinstance(r, str):
            queue.append(Message(message.header(), {"result": r}))
        elif isinstance(r, list) or isinstance(r, tuple):
            for i in r:
                if isinstance(i, Message):
                    queue.append(i)
                elif isinstance(i, int):
                    queue.append(Message(i))
                elif isinstance(i, dict):
                    queue.append(Message(message.header(), i))
                elif isinstance(i, str):
                    queue.append(Message(message.header(), {"result": i}))
        else:
            service.warning(
                f'[hook]: The return result for function "{self._func.__name__}" (type: {type(r)}) of Hook '
                f'for "{self._class.__name__}" was not able to be parsed!'
            )
        del r, s
        return True

    def _exec(self, service, message, queue):
        if not callable(self._func):
            service.warning(
                f'[hook]: Hook for "{self._class.__name__}" is missing a function!'
            )
            return None, False
        if self._args == 5:
            try:
                service.warning(
                    f'[hook]: Function "{self._func.__name__}" of Hook for "{self._class.__name__}" '
                    f"is using the old format, please convert it!"
                )
                return self._func(service, None, queue, message), True
            except Exception as err:
                service.error(
                    f'[hook]: Cannot execute function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err,
                )
                if queue is not None:
                    queue.append(as_exception(message.header(), err))
            return False, False
        if self._args == 4:
            try:
                return self._func(service, message, queue), True
            except Exception as err:
                service.error(
                    f'[hook]: Cannot execute function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err,
                )
                if queue is not None:
                    queue.append(as_exception(message.header(), err))
            return False, False
        if self._args == 3:
            try:
                return self._func(service, message), True
            except Exception as err:
                service.error(
                    f'[hook]: Cannot execute function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err,
                )
                if queue is not None:
                    queue.append(as_exception(message.header(), err))
            return False, False
        if self._args == 2:
            try:
                return self._func(service), True
            except Exception as err:
                service.error(
                    f'[hook]: Cannot execute function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                    err,
                )
                if queue is not None:
                    queue.append(as_exception(message.header(), err))
            return False, False
        try:
            return self._func(), True
        except Exception as err:
            service.error(
                f'[hook]: Cannot execute function "{self._func.__name__}" of Hook for "{self._class.__name__}"!',
                err,
            )
            if queue is not None:
                queue.append(as_exception(message.header(), err))
        return False, False


class HookList(list):
    __slots__ = []

    def __init__(self):
        list.__init__(self)

    def run(self, service, message):
        q = list()
        alarm(TIMEOUT_SEC_HOOK)
        for h in self:
            h.run(service, message, q)
        alarm(0)
        return q

#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Dispatcher class functions simple in a way to help manage
# Hook and function calls by the hosting Service object.
# This class is a thread that waits untill an order is given and will
# then process the messages in a FIFO order.

from threading import Thread, Event
from lib.loader import load_modules
from lib.structs.hook import HookDaemon
from lib.structs.message import Message
from lib.constants import HOOK_STARTUP, HOOK_DAEMON, HOOK_SHUTDOWN, HOOK_RELOAD


class Dispatcher(Thread):
    def __init__(self, service, directory):
        Thread.__init__(self)
        self._daemons = None
        self._running = False
        self._service = service
        self._messages = list()
        self._waiting = Event()
        self._hooks = load_modules(service, directory)

    def run(self):
        self._running = True
        self._waiting.clear()
        self._service.debug("Starting Dispatcher processing thread..")
        if HOOK_STARTUP in self._hooks:
            self._service.debug("Running Startup Hooks..")
            result = self._hooks[HOOK_STARTUP].run(
                self._service, Message(header=HOOK_STARTUP)
            )
            if len(result) > 0:
                self._service.send(None, result)
            del result
        try:
            self._service.write(ignore_errors=False)
        except OSError as err:
            self._service.error(
                'Could not save configuration file "%s"!' % self._service.get_file(),
                err=err,
            )
        if HOOK_DAEMON in self._hooks:
            self._daemons = HookDaemon(self._service, self._hooks[HOOK_DAEMON])
            self._daemons.start()
        while self._running:
            if len(self._messages) == 0:
                self._waiting.clear()
            self._waiting.wait()
            while len(self._messages) > 0:
                message = self._messages.pop()
                try:
                    if message.is_valid() and message.message.header() == HOOK_RELOAD:
                        self._service.debug(
                            'Reloading from the configuration file "%s"..'
                            % self._service.get_file()
                        )
                        try:
                            self._service.read(ignore_errors=False)
                        except OSError as err:
                            self._service.error(
                                'Could not read configuration file "%s"!'
                                % self._service.get_file(),
                                err=err,
                            )
                    if message.is_valid() and message.message.header() in self._hooks:
                        self._service.debug(
                            'Running Hooks for "%s".' % message.message.header()
                        )
                        result = self._hooks[message.message.header()].run(
                            self._service, message.message
                        )
                        if len(result) > 0:
                            self._service.send(message.eid, result)
                        del result
                    else:
                        self._service.warning(
                            'Received an invalid or un-hooked Message "%s"!'
                            % message.message.header()
                        )
                except Exception as err:
                    self._service.error(
                        "An exception was raised when attempting to process a message request!",
                        err=err,
                    )
                finally:
                    del message
        if self._running:
            self.stop()

    def stop(self):
        self._service.debug("Stopping Dispatcher Thread..")
        if HOOK_SHUTDOWN in self._hooks:
            self._service.debug("Running Shutdown Hooks..")
            self._hooks[HOOK_SHUTDOWN].run(self._service, Message(header=HOOK_SHUTDOWN))
        try:
            self._service.write(ignore_errors=False)
        except OSError as err:
            self._service.error(
                'Could not save configuration file "%s"!' % self._service.get_file(),
                err=err,
            )
        self._running = False
        self._waiting.set()
        if self._daemons is not None:
            self._daemons.stop()

    def add(self, eid, message):
        if self._running:
            self._messages.append(DispatchMessage(eid, message))
            self._waiting.set()


class DispatchMessage(object):
    def __init__(self, eid, message):
        self.eid = eid
        self.message = message

    def is_valid(self):
        return isinstance(self.message, Message) and self.message.header() is not None

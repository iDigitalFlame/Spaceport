#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Hook class contains all the primary functions for storing and running hook
# functions.  This class container allows for invocation of multiple hooks using
# a single function call.

from threading import Thread, Event
from lib.structs.message import Message, send_exception


class Hook(object):
    def __init__(self, hook_object, hook_func, hook_class):
        self._func = hook_func
        self._class = hook_class
        self._argcount = hook_func.__code__.co_argcount
        if hook_object is None:
            self._argcount += 1

    def run(self, service, message, qeue):
        service.debug(
            'Running function "%s" of "%s".'
            % (self._func.__name__, self._class.__name__)
        )
        if self._func is None or not callable(self._func):
            service.warning(
                'Hook for "%s" has a missing function!' % self._class.__name__
            )
            return False
        if self._argcount == 5:
            try:
                service.warning(
                    'Function "%s" of Hook for "%s" is using the old format, please comvert it!'
                    % (self._func.__name__, self._class.__name__)
                )
                result = self._func(service, None, qeue, message)
            except Exception as err:
                service.error(
                    'Function "%s" of Hook for "%s" raised an exception while running!'
                    % (self._func.__name__, self._class.__name__),
                    err=err,
                )
                if isinstance(qeue, list):
                    qeue.append(send_exception(message.header(), err))
                return False
        elif self._argcount == 4:
            try:
                result = self._func(service, message, qeue)
            except Exception as err:
                service.error(
                    'Function "%s" of Hook for "%s" raised an exception while running!'
                    % (self._func.__name__, self._class.__name__),
                    err=err,
                )
                if isinstance(qeue, list):
                    qeue.append(send_exception(message.header(), err))
                return False
        elif self._argcount == 3:
            try:
                result = self._func(service, message)
            except Exception as err:
                service.error(
                    'Function "%s" of Hook for "%s" raised an exception while running!'
                    % (self._func.__name__, self._class.__name__),
                    err=err,
                )
                if isinstance(qeue, list):
                    qeue.append(send_exception(message.header(), err))
                return False
        elif self._argcount == 2:
            try:
                result = self._func(service)
            except Exception as err:
                service.error(
                    'Function "%s" of Hook for "%s" raised an exception while running!'
                    % (self._func.__name__, self._class.__name__),
                    err=err,
                )
                if isinstance(qeue, list):
                    qeue.append(send_exception(message.header(), err))
                return False
        else:
            try:
                result = self._func()
            except Exception as err:
                service.error(
                    'Function "%s" of Hook for "%s" raised an Exception while running!'
                    % (self._func.__name__, self._class.__name__),
                    err=err,
                )
                if isinstance(qeue, list):
                    qeue.append(send_exception(message.header(), err))
                return False
        if result is not None:
            if isinstance(result, Message):
                qeue.append(result)
            elif isinstance(result, dict):
                qeue.append(Message(header=message.header(), payload=result))
            elif isinstance(result, str):
                qeue.append(
                    Message(header=message.header(), payload={"result": result})
                )
            elif isinstance(result, list) or isinstance(result, tuple):
                for sub_result in result:
                    if isinstance(sub_result, Message):
                        qeue.append(sub_result)
                    elif isinstance(sub_result, dict):
                        qeue.append(
                            Message(header=message.header(), payload=sub_result)
                        )
                    elif isinstance(sub_result, str):
                        qeue.append(
                            Message(
                                header=message.header(), payload={"result": sub_result}
                            )
                        )
            else:
                service.warning(
                    'The return result for function "%s" of Hook for "%s" was not able to be parsed!'
                    % (self._func.__name__, self._class.__name__)
                )
            del result
        return True


class HookList(list):
    def __init__(self):
        list.__init__(self)

    def run(self, service, message):
        qeue = list()
        service.debug('Running Hooks for Message "%s".' % message.header())
        for hook in self:
            hook.run(service, message, qeue)
        return qeue


class HookDaemon(Thread):
    def __init__(self, service, hooks):
        Thread.__init__(self)
        self._hooks = hooks
        self._service = service
        self._running = Event()

    def run(self):
        self._running.clear()
        self._service.debug("Starting Hooks Thread..")
        while not self._running.is_set():
            for hook in self._hooks:
                hook.run(self._service, None, None)
            self._running.wait(1)
        self._service.debug("Stopping Hooks Thread..")

    def stop(self):
        self._running.set()

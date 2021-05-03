#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Service class is the base object for Daemon threads that run
# such as the client and system daemons. This allows the daemons to share
# common functions, such as logging and dispatching.

from os import getpid
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
        self._log.info('Service "%s" starting up init functions..' % name)
        self._dispatcher = Dispatcher(self, modules)

    def is_server(self):
        return False

    def forward(self, message):
        message["forward"] = True
        self._log.debug('Sending message "%s" to internal Hooks.' % message.header())
        self._dispatcher.add(None, message)

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

    def set(self, name, value, save=True):
        if not self._loaded:
            self._log.debug('Loading configuration from file "%s"..' % self.get_file())
            try:
                self.read(ignore_errors=False)
            except OSError as err:
                self._log.error(
                    'Could not load configuration file "%s", using defaults!'
                    % self.get_file(),
                    err=err,
                )
            self._loaded = True
        self.__setitem__(name, value)
        if save:
            try:
                self.write(ignore_errors=False)
            except OSError as err:
                self.error(
                    'Could not save configuration file "%s"!' % self.get_file(), err=err
                )
        return value

    def config(self, name, default=None, save=True):
        if not self._loaded:
            self._log.debug('Loading configuration from file "%s"..' % self.get_file())
            try:
                self.read(ignore_errors=False)
            except OSError as err:
                self._log.error(
                    'Could not load configuration file "%s", using defaults!'
                    % self.get_file(),
                    err=err,
                )
            self._loaded = True
        value = self.get(name, default)
        if save:
            try:
                self.write(ignore_errors=False)
            except OSError as err:
                self.error(
                    'Could not save configuration file "%s"!' % self.get_file(), err=err
                )
        return value

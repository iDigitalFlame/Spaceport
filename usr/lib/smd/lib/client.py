#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Client class is the daemon responsible for the primary un-privileged functions
# executed by the System Management Client Daemon. This class extends the Service class and
# is executed as a thread for socket processing.

from os import environ
from os.path import exists
from lib.structs.service import Service
from lib.structs.message import Message
from select import epoll, EPOLLERR, EPOLLHUP, EPOLLIN
from socket import (
    socket,
    AF_UNIX,
    SOCK_STREAM,
    SO_REUSEADDR,
    SOL_SOCKET,
    error as socket_err,
)
from lib.constants import (
    NAME_CLIENT,
    LOG_FILE_CLIENT,
    LOG_LEVEL,
    LOG_PAYLOAD,
    SOCKET,
    VERSION,
    CONFIG_CLIENT,
    DIRECTORY_MODULES,
)


class Client(Service):
    def __init__(
        self,
        config=CONFIG_CLIENT,
        socket_path=SOCKET,
        log_level=LOG_LEVEL,
        log_file=LOG_FILE_CLIENT,
    ):
        Service.__init__(
            self,
            NAME_CLIENT,
            DIRECTORY_MODULES,
            config.replace("{home}", environ["HOME"]),
            log_level,
            log_file,
        )
        self._socket = None
        self._messages = list()
        self._socket_path = socket_path

    def stop(self):
        self.info("Stopping System Management Daemon Client..")
        self._dispatcher.stop()
        try:
            if self._socket is not None:
                self._socket.close()
        except (OSError, socket_err) as err:
            self.error(
                'Attempting to close the UNIX socket "%s" connection raised an exception!'
                % self._socket_path,
                err=err,
            )

    def start(self):
        self.info(
            "Starting System Management Daemon Client (version: %s) primary thread.."
            % VERSION
        )
        if not exists(self._socket_path):
            self.error('Server UNIX socket "%s" does not exist!' % self._socket_path)
            return False
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.connect(self._socket_path)
            self._socket.setblocking(0)
        except (OSError, socket_err) as err:
            self.error(
                'Attempting to connect to the UNIX socket "%s" raised an exception!'
                % self._socket_path,
                err=err,
            )
            return False
        running = True
        poll = epoll()
        poll.register(self._socket.fileno(), EPOLLIN)
        self._dispatcher.start()
        try:
            while running:
                if self._socket is None:
                    running = False
                    break
                for _, event in poll.poll(1):
                    if event & EPOLLIN:
                        try:
                            self._socket.setblocking(1)
                            message = Message(stream=self._socket)
                            self._socket.setblocking(0)
                            self._dispatcher.add(None, message)
                            self.debug(
                                'Received a message type "%s" from the server.'
                                % message.header()
                            )
                            if LOG_PAYLOAD and len(message) > 0:
                                self.error("[RECV <] MESSAGE DUMP: %s" % str(message))
                            del message
                        except OSError as err:
                            if err.errno == 1000 or err.errno == 104:
                                self.debug("Disconnecting from the server..")
                                running = False
                                break
                            else:
                                self.error(
                                    "Server connection raised an Exception!", err=err
                                )
                        finally:
                            self._socket.setblocking(0)
                    elif event & EPOLLHUP or event & EPOLLERR:
                        self.debug("Disconnecting from the server..")
                        running = False
                        break
        except KeyboardInterrupt:
            self.debug("Stopping Client Thread..")
            return True
        except Exception as err:
            self.error("Exception was rised during thread operation!", err=err)
            return False
        finally:
            poll.unregister(self._socket.fileno())
            self.stop()
            del poll
            del running
        return True

    def send(self, eid, message_result):
        if isinstance(message_result, Message):
            message_result = [message_result]
        elif not isinstance(message_result, list) and not isinstance(
            message_result, tuple
        ):
            return
        while len(message_result) > 0:
            message = message_result.pop()
            try:
                message.send(self._socket)
                self.debug('Message "%s" was sent to the server.' % message.header())
                if LOG_PAYLOAD and len(message) > 0:
                    self.error("[SEND >] MESSAGE DUMP: %s" % str(message))
            except OSError as err:
                if err.errno == 32:
                    self.warning("Server has been disconnected!")
                else:
                    self.error(
                        'Attempting to send Message "%s" to the server raised an exception!'
                        % message.header(),
                        err=err,
                    )
            except Exception as err:
                self.error(
                    'Attempting to send Message "%s" to the server raised an exception!'
                    % message.header(),
                    err=err,
                )
            finally:
                del message

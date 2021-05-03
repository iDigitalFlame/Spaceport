#!/usr/bin/false
# The Client class is the daemon responsible for the primary un-privileged functions
# executed by the System Management Client Daemon. This class extends the Service class and
# is executed as a thread for socket processing.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2021 iDigitalFlame
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

from uuid import uuid4
from os.path import exists
from lib.util import eval_env
from lib.structs.service import Service
from lib.structs.message import Message
from select import epoll, EPOLLERR, EPOLLHUP, EPOLLIN
from socket import (
    socket,
    AF_UNIX,
    SHUT_RDWR,
    SOL_SOCKET,
    SOCK_STREAM,
    SO_REUSEADDR,
    error as socket_err,
)
from lib.constants import (
    SOCKET,
    VERSION,
    LOG_LEVEL,
    NAME_CLIENT,
    LOG_PAYLOAD,
    CONFIG_CLIENT,
    LOG_PATH_CLIENT,
    DIRECTORY_MODULES,
    HOOK_NOTIFICATION,
)


class Client(Service):
    def __init__(
        self,
        config=CONFIG_CLIENT,
        socket_path=SOCKET,
        log_level=LOG_LEVEL,
        log_file=LOG_PATH_CLIENT,
    ):
        Service.__init__(
            self,
            NAME_CLIENT,
            DIRECTORY_MODULES,
            eval_env(config),
            log_level,
            eval_env(log_file),
        )
        self._uuid = str(uuid4())
        self._socket = None
        self._messages = list()
        self._socket_path = socket_path

    def stop(self):
        self.info("Stopping System Management Daemon Client..")
        self._dispatcher.stop()
        try:
            if self._socket is not None:
                self._socket.shutdown(SHUT_RDWR)
                self._socket.close()
        except (OSError, socket_err) as err:
            self.error(
                f'Attempting to close the UNIX socket "{self._socket_path}" connection raised an exception!',
                err=err,
            )

    def start(self):
        self.info(
            f"Starting System Management Daemon Client (v{VERSION}) primary thread.."
        )
        if not exists(self._socket_path):
            self.error(f'Server UNIX socket "{self._socket_path}" does not exist!')
            return False
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.connect(self._socket_path)
            self._socket.setblocking(False)
        except (OSError, socket_err) as err:
            self.error(
                f'Attempting to connect to the UNIX socket "{self._socket_path}" raised an exception!',
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
                            self._socket.setblocking(True)
                            message = Message(stream=self._socket)
                            self._socket.setblocking(False)
                            self._dispatcher.add(None, message)
                            self.debug(
                                f"Received a message type 0x{message.header():02X} from the server."
                            )
                            if LOG_PAYLOAD and len(message) > 0:
                                self.error(f"[RECV <] MESSAGE DUMP: {message}")
                            del message
                        except OSError as err:
                            if err.errno == 1000 or err.errno == 104:
                                self.debug("Disconnecting from the server..")
                                running = False
                                break
                            else:
                                self.error(
                                    "Server connection raised an exception!", err=err
                                )
                        finally:
                            self._socket.setblocking(False)
                    elif event & EPOLLHUP or event & EPOLLERR:
                        self.debug("Disconnecting from the server..")
                        running = False
                        break
        except KeyboardInterrupt:
            self.debug("Stopping client thread..")
            return True
        except Exception as err:
            self.error("Exception was raised during thread operation!", err=err)
            return False
        finally:
            poll.unregister(self._socket.fileno())
            self.stop()
            del poll
            del running
        return True

    def send(self, _, message_result):
        if isinstance(message_result, Message):
            message_result = [message_result]
        elif not isinstance(message_result, list) and not isinstance(
            message_result, tuple
        ):
            return
        while len(message_result) > 0:
            message = message_result.pop()
            if "id" not in message:
                message["id"] = self._uuid
            try:
                message.send(self._socket)
                self.debug(f"Message 0x{message.header():02X} was sent to the server.")
                if LOG_PAYLOAD and len(message) > 0:
                    self.error(f"[SEND >] MESSAGE DUMP: {message}")
            except OSError as err:
                if err.errno == 32:
                    self.info("Server has disconnected!")
                else:
                    self.error(
                        f"Attempting to send message 0x{message.header():02X} to the server raised an exception!",
                        err=err,
                    )
            except Exception as err:
                self.error(
                    f"Attempting to send message 0x{message.header():02X} to the server raised an exception!",
                    err=err,
                )
            finally:
                del message

    def notify(self, title, message=None, icon=None):
        self.forward(
            Message(
                header=HOOK_NOTIFICATION,
                payload={"icon": icon, "title": title, "message": message},
            )
        )

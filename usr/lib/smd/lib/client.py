#!/usr/bin/false
# The Client class is the daemon responsible for the primary un-privileged functions
# executed by the System Management Client Daemon. This class extends the Service class and
# is executed as a thread for socket processing.
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

from uuid import uuid4
from lib.structs.service import Service
from lib.structs.message import Message
from os.path import exists, expandvars, expanduser
from select import epoll, EPOLLERR, EPOLLHUP, EPOLLIN
from socket import (
    socket,
    AF_UNIX,
    SHUT_RDWR,
    SOL_SOCKET,
    SOCK_STREAM,
    SO_REUSEADDR,
)
from lib.constants import (
    VERSION,
    NAME_CLIENT,
    LOG_PAYLOAD,
    DIRECTORY_MODULES,
    HOOK_NOTIFICATION,
)


class Client(Service):
    def __init__(self, config, sock, level, log, read_only):
        Service.__init__(
            self,
            NAME_CLIENT,
            DIRECTORY_MODULES,
            expandvars(expanduser(config)),
            level,
            expandvars(expanduser(log)),
            read_only,
        )
        self._socket = None
        self._messages = list()
        self._socket_path = sock
        self._uuid = str(uuid4())

    def stop(self):
        self.info("Stopping System Management Daemon Client..")
        self._dispatcher.stop()
        if self._socket is None:
            return
        try:
            self._socket.shutdown(SHUT_RDWR)
            self._socket.close()
        except OSError as err:
            self.error(f'Error closing UNIX socket "{self._socket_path}"!', err=err)
        self._socket = None

    def start(self):
        self.info(
            f"Starting System Management Daemon client (v{VERSION}) base thread.."
        )
        if not exists(self._socket_path):
            self.error(f'Server UNIX socket "{self._socket_path}" does not exist!')
            return False
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.connect(self._socket_path)
            self._socket.setblocking(False)
        except OSError as err:
            self.error(
                f'Error connecting to UNIX socket "{self._socket_path}"!', err=err
            )
            return False
        r = True
        p = epoll()
        p.register(self._socket.fileno(), EPOLLIN)
        self._dispatcher.start()
        try:
            while r:
                if self._socket is None:
                    r = False
                    break
                for _, e in p.poll(1):
                    if e & EPOLLIN:
                        try:
                            self._socket.setblocking(True)
                            m = Message(stream=self._socket)
                            self._socket.setblocking(False)
                            self._dispatcher.add(None, m)
                            self.debug(
                                f"Received a message type 0x{m.header():02X} from the server."
                            )
                            if LOG_PAYLOAD and len(m) > 0:
                                self.error(f"[RECV <] MESSAGE DUMP: {m}")
                            del m
                        except OSError as err:
                            if err.errno == 1000 or err.errno == 104:
                                self.debug("Disconnecting from the server..")
                                r = False
                                break
                            else:
                                self.error("Server connection error!", err=err)
                        finally:
                            self._socket.setblocking(False)
                    elif e & EPOLLHUP or e & EPOLLERR:
                        self.debug("Disconnecting from the server..")
                        r = False
                        break
        except KeyboardInterrupt:
            self.debug("Stopping client thread..")
        except Exception as err:
            self.error("Exception during thread operation!", err=err)
            return False
        finally:
            p.unregister(self._socket.fileno())
            p.close()
            self.stop()
            del p
            del r
        return True

    def send(self, _, result):
        if isinstance(result, Message):
            result = [result]
        elif not isinstance(result, list) and not isinstance(result, tuple):
            return
        while len(result) > 0:
            m = result.pop()
            if "id" not in m:
                m["id"] = self._uuid
            try:
                m.send(self._socket)
                self.debug(f"Message 0x{m.header():02X} was sent to the server.")
                if LOG_PAYLOAD and len(m) > 0:
                    self.error(f"[SEND >] MESSAGE DUMP: {m}")
            except OSError as err:
                if err.errno == 32:
                    self.info("Server has disconnected!")
                else:
                    self.error(
                        f"Error sending message 0x{m.header():02X} to the server!",
                        err=err,
                    )
            except Exception as err:
                self.error(
                    f"Error sending message 0x{m.header():02X} to the server!",
                    err=err,
                )
            finally:
                del m

    def notify(self, title, message=None, icon=None):
        self.forward(
            Message(
                header=HOOK_NOTIFICATION,
                payload={"icon": icon, "title": title, "message": message},
            )
        )

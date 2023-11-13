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

# client.py
#   The Client class is the daemon responsible for the primary un-privileged
#   functions executed by SMD.

from uuid import uuid4
from os.path import exists
from lib.util.file import expand
from lib.structs import Service, Message
from lib.constants import VERSION, HOOK_NOTIFICATION
from select import epoll, EPOLLERR, EPOLLHUP, EPOLLIN
from lib.constants.config import NAME_CLIENT, LOG_PAYLOAD, DIRECTORY_MODULES
from socket import socket, AF_UNIX, SHUT_RDWR, SOL_SOCKET, SOCK_STREAM, SO_REUSEADDR


class Client(Service):
    __slots__ = ("_path", "_uuid", "_socket", "_messages")

    def __init__(self, config, sock, level, log, read_only, journal):
        Service.__init__(
            self,
            NAME_CLIENT,
            DIRECTORY_MODULES,
            expand(config),
            level,
            expand(log),
            read_only,
            journal,
        )
        self._path = sock
        self._socket = None
        self._messages = list()
        self._uuid = str(uuid4())

    def stop(self):
        self._dispatcher.stop()
        if self._socket is None:
            return
        try:
            self._socket.shutdown(SHUT_RDWR)
            self._socket.close()
        except OSError as err:
            self.error(f'[main]: Cannot close the socket "{self._path}"!', err)
        self._socket = None

    def start(self):
        self.info(f"[main]: Starting System Management Daemon Client (v{VERSION})..")
        if not exists(self._path):
            return self.error(f'[main]: Socket "{self._path}" does not exist!')
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.connect(self._path)
            self._socket.setblocking(False)
        except OSError as err:
            if self._socket is not None:
                self._socket.close()
            return self.error(
                f'[main]: Cannot connect to the socket "{self._path}"!', err
            )
        self.debug(f'[main]: Connection UUID is "{self._uuid}".')
        r, p = True, epoll()
        p.register(self._socket.fileno(), EPOLLIN)
        self._dispatcher.start()
        try:
            while r:
                if self._socket is None:
                    break
                for _, e in p.poll(None):
                    r = self._process(e)
                    if r:
                        continue
                    break
        except KeyboardInterrupt:
            self.debug("[main]: Stopping Client Thread..")
        except Exception as err:
            return self.error("[main]: Unexpected runtime error!", err)
        finally:
            self.info("[main]: Stopping System Management Daemon Client..")
            p.unregister(self._socket.fileno())
            p.close()
            self.stop()
            del p, r
        return True

    def send(self, _, message):
        if isinstance(message, Message):
            return self._send_one(message)
        if not isinstance(message, list) and not isinstance(message, tuple):
            return
        if len(message) == 0:
            return
        for i in message:
            if not isinstance(i, Message):
                continue
            self._send_one(i)

    def _send_one(self, message):
        message["id"] = self._uuid
        try:
            message.send(self._socket)
            self.debug(f"[conn]: Message 0x{message.header():02X} was sent.")
            if LOG_PAYLOAD:
                self.error(f"[dump]: OUT > {message}")
        except OSError as err:
            if err.errno == 0x20:
                return self.info("[conn]: Server has disconnected!")
            self.error(f"[conn]: Cannot send message 0x{message.header():02X}!", err)
        except Exception as err:
            self.error(f"[conn]: Cannot send message 0x{message.header():02X}!", err)

    def _process(self, poll_msg):
        if poll_msg & EPOLLHUP or poll_msg & EPOLLERR:
            return self.debug("[conn]: Disconnecting..")
        if not (poll_msg & EPOLLIN):
            return True
        try:
            self._socket.setblocking(True)
            m = Message(stream=self._socket)
            self._dispatcher.add(None, m)
            self.debug(f"[conn]: Received Message 0x{m.header():02X}.")
            if LOG_PAYLOAD:
                self.error(f"[dump]:  IN < {m}")
            del m
        except OSError as err:
            if err.errno == 0x3E8 or err.errno == 0x68:
                return self.debug("[main]: Disconnecting..")
            self.error("[conn]: Unexpected connection error!", err)
        finally:
            self._socket.setblocking(False)
        return True

    def notify(self, title, message=None, icon=None):
        self.forward(
            Message(
                HOOK_NOTIFICATION, {"icon": icon, "title": title, "message": message}
            )
        )

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

# server.py
#   The Server class is the daemon responsible for the primary privileged functions
#   executed by SMD.

from grp import getgrnam
from threading import Event
from os.path import exists, dirname
from lib.util.file import ensure_dir
from lib.structs import Service, Message
from os import getpid, remove, chmod, chown, stat
from select import epoll, EPOLLERR, EPOLLHUP, EPOLLIN
from lib.constants import VERSION, HOOK_SHUTDOWN, HOOK_NOTIFICATION
from socket import (
    socket,
    AF_UNIX,
    SHUT_RDWR,
    SOL_SOCKET,
    SOCK_STREAM,
    SO_PEERCRED,
    SO_REUSEADDR,
)
from lib.constants.config import (
    NAME_SERVER,
    LOG_PAYLOAD,
    SOCKET_GROUP,
    SOCKET_BACKLOG,
    TIMEOUT_SEC_STOP,
    DIRECTORY_MODULES,
)


class Conn(object):
    __slots__ = ("_uid", "_pid", "_sock", "_queue")

    def __init__(self, sock):
        self._sock = sock
        self._sock.setblocking(False)
        self._queue = list()
        try:
            self._pid = int(self._sock.getsockopt(SOL_SOCKET, SO_PEERCRED))
            self._uid = stat(f"/proc/{self._pid}").st_uid
        except (ValueError, OSError):
            self._pid, self._uid = None, None

    def read(self):
        self._sock.setblocking(True)
        try:
            return Message(stream=self._sock, pid=self._pid, uid=self._uid)
        finally:
            self._sock.setblocking(False)

    def close(self):
        if self._sock is None:
            return
        self._sock.shutdown(SHUT_RDWR)
        self._sock.close()
        self._queue.clear()
        self._sock, self._queue, self._uid, self._pid = None, None, None, None

    def add(self, message):
        if self._sock is None:
            return
        self._queue.append(message)

    def flush(self, server):
        if self._sock is None or self._queue is None:
            return
        try:
            while len(self._queue) > 0:
                self._flush(server)
        except (TypeError, AttributeError):
            # NOTE(dij): Catch race condition that happens when a client disconnects
            #            during a flush operation.
            pass

    def _flush(self, server):
        m = self._queue.pop()
        m["server_pid"] = server._pid
        try:
            m.send(self._sock)
            server.debug(
                f"[conn]: Message 0x{m.header():02X} was sent to socket FD({self._sock.fileno()})."
            )
            if LOG_PAYLOAD:
                server.error(f"[dump]: OUT > {m}")
        except OSError as err:
            if err.errno == 0x20 or err.errno == 0x9:
                if self._sock.fileno() == -1:
                    return
                return server.debug(
                    f"[conn]: Socket FD({self._sock.fileno()}) has disconnected!"
                )
            server.error(
                f"[conn]: Cannot send message 0x{m.header():02X} to socket FD({self._sock.fileno()})!",
                err,
            )
        except Exception as err:
            server.error(
                f"[conn]: Cannot send message 0x{m.header():02X} to socket FD({self._sock.fileno()})!",
                err,
            )
        finally:
            del m

    def setblocking(self, blocking):
        self._sock.setblocking(blocking)


class Server(Service):
    __slots__ = ("_pid", "_path", "_socket", "_clients", "_running", "_complete")

    def __init__(self, config, sock, level, log, read_only, journal):
        Service.__init__(
            self, NAME_SERVER, DIRECTORY_MODULES, config, level, log, read_only, journal
        )
        self._pid = getpid()
        self._path = sock
        self._socket = None
        self._clients = dict()
        self._running = Event()
        self._complete = Event()

    def stop(self):
        self._running.set()
        self._complete.wait(TIMEOUT_SEC_STOP)

    def start(self):
        self.info(f"[main]: Starting System Management Daemon Server (v{VERSION})..")
        if exists(self._path):
            try:
                remove(self._path)
            except OSError as err:
                self.error(f'[main]: Cannot remove the socket "{self._path}"!', err)
                return self._stop()
        try:
            ensure_dir(self._path, mode=0o0750)
        except OSError as err:
            self.error(
                f'[main]: Cannot create the socket directory for "{self._path}"!',
                err,
            )
            return self._stop()
        try:
            g = getgrnam(SOCKET_GROUP).gr_gid
        except Exception as err:
            self.error(f'[main]: Cannot resolve the group "{SOCKET_GROUP}"!', err)
            return self._stop()
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.bind(self._path)
            self._socket.listen(SOCKET_BACKLOG)
            chown(self._path, 0, g)
            chown(dirname(self._path), 0, g)
            chmod(self._path, 0o0660)
            self._socket.setblocking(False)
        except OSError as err:
            self.error(f'[main]: Cannot listen on socket "{self._path}"!', err)
            return self.stop()
        finally:
            del g
        self._dispatcher.start()
        p = epoll()
        p.register(self._socket.fileno(), EPOLLIN | EPOLLHUP | EPOLLERR)
        try:
            while not self._running.is_set():
                for f, e in p.poll(None):
                    if not self._poll(p, f, e):
                        break
        except KeyboardInterrupt:
            self.debug("[main]: Stopping Server Thread..")
        except Exception as err:
            return self.error("[main]: Unexpected runtime error!", err)
        finally:
            if self._socket is not None and self._socket.fileno() != -1:
                p.unregister(self._socket.fileno())
            p.close()
            del p
            self._stop()
        return True

    def _stop(self):
        self._send_one(None, Message(HOOK_SHUTDOWN))
        self._dispatcher.stop()
        self.info("[main]: Stopping System Management Daemon Server..")
        self._running.set()
        c = list(self._clients.values())
        for i in c:
            try:
                i.close()
            except OSError:
                pass
        del c
        self._clients.clear()
        try:
            if self._socket is not None:
                self._socket.shutdown(SHUT_RDWR)
                self._socket.close()
            self._socket = None
        except OSError as err:
            self.error(f'[main]: Cannot close the socket "{self._path}"!', err)
        if exists(self._path):
            try:
                remove(self._path)
            except OSError as err:
                self.error(f'[main]: Cannot remove the socket "{self._path}"!', err)
        self.debug("[main]: Server shutdown complete.")
        self._complete.set()

    def _flush(self):
        c = list(self._clients.values())
        for i in c:
            i.flush(self)
        del c

    def __hash__(self):
        return hash(NAME_SERVER)

    def is_server(self):
        return True

    def _read(self, poll, file):
        try:
            m = self._clients[file].read()
            self._dispatcher.add(file, m)
            self.debug(
                f"[conn]: Received Message type 0x{m.header():02X} from client "
                f"PID({m.pid()})/UID({m.uid()})/FD({file})."
            )
            if LOG_PAYLOAD:
                self.error(f"[dump]:  IN < {m}")
            del m
            return
        except OSError as err:
            if err.errno != 0x3E8:
                return self.error(
                    f"[conn]: Cannot read from client on FD({file})!", err
                )
        finally:
            self._clients[file].setblocking(False)
        self.debug(f"[conn]: Client on FD({file}) disconnected!")
        poll.unregister(file)
        self._clients[file].close()
        del self._clients[file]

    def send(self, eid, message):
        if isinstance(message, Message):
            return self._send_one(eid, message)
        if not isinstance(message, list) and not isinstance(message, tuple):
            return
        if len(message) == 0:
            return
        for i in message:
            if not isinstance(i, Message):
                continue
            self._send_one(eid, i, flush=False)
        self._flush()

    def broadcast(self, message):
        self.send(None, message)

    def _poll(self, poll, file, event):
        if file == self._socket.fileno():
            if event & EPOLLHUP:
                self.debug("[conn]: Received socket shutdown event.")
                return self._running.set()
            c, _ = self._socket.accept()
            poll.register(c, EPOLLIN)
            self._clients[c.fileno()] = Conn(c)
            self.debug(f"[conn]: Client connected on socket FD({c.fileno()}).")
            del c
            return True
        if file not in self._clients:
            return True
        if event & EPOLLIN:
            self._read(poll, file)
        elif event & (EPOLLHUP | EPOLLERR):
            self.error(
                f"[conn]: Client on socket FD({file}) has disconnected with errors!"
            )
            poll.unregister(file)
            self._clients[file].close()
            del self._clients[file]
        return True

    def _send_one(self, eid, message, flush=True):
        if eid is None or message.is_multicast():
            c = list(self._clients.values())
            for i in c:
                i.add(message)
            del c
        elif eid is not None and eid in self._clients:
            self._clients[eid].add(message)
        else:
            return
        if flush:
            self._flush()

    def notify(self, title, message=None, icon=None):
        self._send_one(
            None,
            Message(HOOK_NOTIFICATION, {"icon": icon, "title": title, "body": message}),
        )

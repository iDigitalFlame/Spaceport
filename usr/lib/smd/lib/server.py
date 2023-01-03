#!/usr/bin/false
# The Server class is the daemon responsible for the primary privileged functions
# executed by the System Management Daemon. This class extends the Service class and
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

from grp import getgrnam
from threading import Thread, Event
from lib.structs.service import Service
from lib.structs.message import Message
from os.path import exists, isdir, dirname
from os import remove, chmod, chown, makedirs
from select import epoll, EPOLLERR, EPOLLHUP, EPOLLIN
from socket import (
    socket,
    AF_UNIX,
    SHUT_RDWR,
    SOL_SOCKET,
    SOCK_STREAM,
    SO_PEERCRED,
    SO_REUSEADDR,
)
from lib.constants import (
    VERSION,
    NAME_SERVER,
    LOG_PAYLOAD,
    SOCKET_GROUP,
    HOOK_SHUTDOWN,
    SOCKET_BACKLOG,
    HOOK_NOTIFICATION,
    DIRECTORY_MODULES,
)


class ServerClient(object):
    def __init__(self, client):
        self._pid = 0
        self._queue = list()
        self._client = client
        self._client.setblocking(False)
        try:
            self._pid = int(client.getsockopt(SOL_SOCKET, SO_PEERCRED))
        except OSError:
            pass

    def read(self):
        self._client.setblocking(True)
        m = Message(stream=self._client)
        m["pid"] = self._pid
        self._client.setblocking(False)
        return m

    def close(self):
        self._client.shutdown(SHUT_RDWR)
        self._client.close()

    def socket(self):
        return self._client

    def add(self, message):
        self._queue.append(message)

    def flush(self, server):
        while len(self._queue) > 0:
            self._flush(server)

    def _flush(self, server):
        m = self._queue.pop()
        try:
            m.send(self._client)
            server.debug(
                f"Message 0x{m.header():02X} was sent to client socket FD({self._client.fileno()})."
            )
            if LOG_PAYLOAD and len(m) > 0:
                server.error(f"[SEND >] MESSAGE DUMP: {m}")
        except OSError as err:
            if err.errno == 32 or err.errno == 9:
                if self._client.fileno() == -1:
                    return
                return server.debug(
                    f"Client socket FD({self._client.fileno()}) has disconnected!"
                )
            server.error(
                f"Error sending message 0x{m.header():02X} to client socket FD({self._client.fileno()})!",
                err=err,
            )
        except Exception as err:
            server.error(
                f"Error sending message 0x{m.header():02X} to client socket FD({self._client.fileno()})!",
                err=err,
            )
        finally:
            del m


class Server(Service, Thread):
    def __init__(self, config, sock, level, log, read_only):
        Thread.__init__(self, name="SMDServerThread", daemon=False)
        Service.__init__(
            self, NAME_SERVER, DIRECTORY_MODULES, config, level, log, read_only
        )
        self._path = sock
        self._socket = None
        self._done = Event()
        self._clients = dict()
        self._running = Event()

    def run(self):
        self.info(
            f"Starting System Management Daemon Server (v{VERSION}) listening thread.."
        )
        if exists(self._path):
            try:
                remove(self._path)
            except OSError as err:
                self.error(f'Error removing UNIX socket "{self._path}"!', err=err)
                return self._stop()
        d = dirname(self._path)
        if not isdir(d) or not exists(d):
            try:
                makedirs(d, exist_ok=True)
            except OSError as err:
                self.error(
                    f'Error creating UNIX socket directory for "{self._path}"!', err=err
                )
                return self._stop()
        del d
        try:
            g = getgrnam(SOCKET_GROUP).gr_gid
        except Exception as err:
            self.error(f'Error resolving UNIX socket group "{SOCKET_GROUP}"!', err=err)
            return self._stop()
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.bind(self._path)
            self._socket.listen(SOCKET_BACKLOG)
            chown(self._path, 0, g)
            chmod(self._path, 0o0660)
            self._socket.setblocking(False)
        except OSError as err:
            self.error(f'Error listining on UNIX socket "{self._path}"!', err=err)
            return self.stop()
        del g
        self._done.clear()
        self._running.clear()
        self._dispatcher.start()
        p = epoll()
        p.register(self._socket.fileno(), EPOLLIN | EPOLLHUP)
        try:
            while not self._running.is_set():
                self._poll(p)
        except Exception as err:
            self.error("Error during server thread operation!", err=err)
        if self._socket is not None and self._socket.fileno() != -1:
            p.unregister(self._socket.fileno())
        p.close()
        del p
        self._stop()

    def stop(self):
        self._running.set()
        if self._socket is not None:
            try:
                self._socket.shutdown(SHUT_RDWR)
            except OSError as err:
                return self.error("Error stopping the server thread!", err=err)
        self._done.wait()

    def wait(self):
        self._done.wait()

    def _stop(self):
        self.info("Stopping System Management Daemon server thread..")
        self.send(None, [Message(header=HOOK_SHUTDOWN)])
        self._dispatcher.stop()
        try:
            if self._socket is not None:
                self._socket.shutdown(SHUT_RDWR)
                self._socket.close()
            self._socket = None
        except OSError as err:
            self.error(f'Error closing the UNIX socket "{self._path}"!', err=err)
        if exists(self._path):
            try:
                remove(self._path)
            except OSError as err:
                self.error(f'Error removing the UNIX socket "{self._path}"!', err=err)
        self.debug("Server Thread shutdown complete.")
        self._done.set()

    def _flush(self):
        e = list(self._clients.keys())
        for c in e:
            if c in self._clients:
                self._clients[c].flush(self)
        del e

    def __hash__(self):
        return hash(NAME_SERVER)

    def is_server(self):
        return True

    def _poll(self, poll):
        for f, e in poll.poll(None):
            if f == self._socket.fileno():
                if e & EPOLLHUP:
                    self.debug("Received socket shutdown event.")
                    return self._running.set()
                c, _ = self._socket.accept()
                poll.register(c, EPOLLIN)
                self._clients[c.fileno()] = ServerClient(c)
                self.debug(f"Client connected to server on socket FD({c.fileno()}).")
                del c
                continue
            if f not in self._clients:
                continue
            if e & EPOLLIN:
                self._read_client(poll, f)
                continue
            if e & (EPOLLHUP | EPOLLERR):
                self.error(
                    f"Client on socket FD({f}) has been disconnected due to errors!"
                )
                poll.unregister(f)
                self._clients[f].close()
                del self._clients[f]

    def send(self, eid, result):
        if isinstance(result, Message):
            result = [result]
        elif not isinstance(result, list) and not isinstance(result, tuple):
            return
        for m in result:
            if eid is None or m.is_multicast():
                e = list(self._clients.keys())
                for c in e:
                    if c in self._clients:
                        self._clients[c].add(m)
                del e
            elif eid is not None and eid in self._clients:
                self._clients[eid].add(m)
        self._flush()

    def _read_client(self, poll, f):
        try:
            m = self._clients[f].read()
            self._dispatcher.add(f, m)
            self.debug(
                f"Received message type 0x{m.header():02X} from client "
                f"socket PID({m.get('pid', -1)})/FD({f})."
            )
            if LOG_PAYLOAD and len(m) > 0:
                self.error(f"[RECV <] MESSAGE DUMP: {m}")
            del m
            return
        except OSError as err:
            if err.errno != 1000:
                self._clients[f].socket().setblocking(False)
                return self.error(
                    f"Error reading from client on socket FD({f})!", err=err
                )
        self.debug(f"Client on socket FD({f}) disconnected!")
        poll.unregister(f)
        self._clients[f].close()
        del self._clients[f]

    def notify(self, title, message=None, icon=None):
        self.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={"icon": icon, "title": title, "body": message},
            ),
        )

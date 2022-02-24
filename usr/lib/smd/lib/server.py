#!/usr/bin/false
# The Server class is the daemon responsible for the primary privileged functions
# executed by the System Management Daemon. This class extends the Service class and
# is executed as a thread for socket processing.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2022 iDigitalFlame
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
        self._client.setblocking(0)
        try:
            self._pid = int(client.getsockopt(SOL_SOCKET, SO_PEERCRED))
        except OSError:
            pass

    def read(self):
        self._client.setblocking(1)
        m = Message(stream=self._client)
        m["pid"] = self._pid
        self._client.setblocking(0)
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
        self._socket = None
        self._clients = dict()
        self._running = Event()
        self._socket_path = sock

    def run(self):
        self.info(
            f"Starting System Management Daemon Server (v{VERSION}) listening thread.."
        )
        if exists(self._socket_path):
            try:
                remove(self._socket_path)
            except OSError as err:
                self.error(
                    f'Error removing UNIX socket "{self._socket_path}"!', err=err
                )
                return self.stop()
        d = dirname(self._socket_path)
        if not isdir(d) or not exists(d):
            try:
                makedirs(d, exist_ok=True)
            except OSError as err:
                self.error(
                    f'Error creating UNIX socket "{self._socket_path}"!',
                    err=err,
                )
                return self.stop()
        del d
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.bind(self._socket_path)
            self._socket.listen(SOCKET_BACKLOG)
            chown(self._socket_path, 0, 8008)
            chmod(self._socket_path, 0o760)
            self._socket.setblocking(False)
        except OSError as err:
            self.error(
                f'Error listining on UNIX socket "{self._socket_path}"!', err=err
            )
            return self.stop()
        self._running.clear()
        self._dispatcher.start()
        p = epoll()
        p.register(self._socket.fileno(), EPOLLIN)
        try:
            while not self._running.is_set():
                for f, e in p.poll(1):
                    if f == self._socket.fileno():
                        c, _ = self._socket.accept()
                        p.register(c.fileno(), EPOLLIN)
                        self._clients[c.fileno()] = ServerClient(c)
                        self.debug(
                            f"Client connected to server on socket FD({c.fileno()})."
                        )
                        del c
                        continue
                    if e & EPOLLIN and f in self._clients:
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
                            continue
                        except OSError as err:
                            self._clients[f].socket().setblocking(0)
                            if err.errno == 1000:
                                self.debug(f"Client on socket FD({f}) disconnected!")
                                p.unregister(f)
                                self._clients[f].close()
                                del self._clients[f]
                                continue
                            self.error(
                                f"Error reading from client socket FD({f}) !", err=err
                            )
                            continue
                    if e & EPOLLHUP or e & EPOLLERR:
                        self.error(
                            f"Client on socket FD({f}) has been disconnected due to errors!"
                        )
                        p.unregister(f)
                        self._clients[f].close()
                        del self._clients[f]
        except Exception as err:
            self.error("Error during server thread operation!", err=err)
        finally:
            p.unregister(self._socket.fileno())
            p.close()
            del p
        self._stop_server()

    def stop(self):
        self._running.set()
        self._running.wait()

    def wait(self):
        self._running.wait()

    def flush(self):
        e = list(self._clients.keys())
        for c in e:
            if c in self._clients:
                self._clients[c].flush(self)
        del e

    def __hash__(self):
        return hash(NAME_SERVER)

    def is_server(self):
        return True

    def _stop_server(self):
        self.info("Stopping System Management Daemon server thread..")
        self.send(None, [Message(header=HOOK_SHUTDOWN)])
        self._dispatcher.stop()
        try:
            if self._socket is not None:
                self._socket.shutdown(SHUT_RDWR)
                self._socket.close()
            remove(self._socket_path)
        except OSError as err:
            self.error(f'Error closing the UNIX socket "{self._socket_path}"!', err=err)
        self.debug("Server Thread shutdown complete.")
        self._running.set()

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
        self.flush()

    def notify(self, title, message=None, icon=None):
        self.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={"icon": icon, "title": title, "body": message},
            ),
        )

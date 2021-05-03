#!/usr/bin/false
# The Server class is the daemon responsible for the primary privileged functions
# executed by the System Management Daemon. This class extends the Service class and
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
    error as socket_err,
)
from lib.constants import (
    SOCKET,
    VERSION,
    LOG_LEVEL,
    NAME_SERVER,
    LOG_PAYLOAD,
    CONFIG_SERVER,
    HOOK_SHUTDOWN,
    SOCKET_BACKLOG,
    LOG_PATH_SERVER,
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
        message = Message(stream=self._client)
        message["pid"] = self._pid
        self._client.setblocking(0)
        return message

    def close(self):
        self._client.shutdown(SHUT_RDWR)
        self._client.close()

    def socket(self):
        return self._client

    def add(self, message):
        self._queue.append(message)

    def flush(self, server):
        while len(self._queue) > 0:
            message = self._queue.pop()
            try:
                message.send(self._client)
                server.debug(
                    f"Message 0x{message.header():02X} was sent to client socket FD({self._client.fileno()})."
                )
                if LOG_PAYLOAD and len(message) > 0:
                    server.error(f"[SEND >] MESSAGE DUMP: {message}")
            except OSError as err:
                if err.errno == 32 or err.errno == 9:
                    if self._client.fileno() == -1:
                        continue
                    server.debug(
                        f"Client socket FD({self._client.fileno()}) has disconnected!"
                    )
                    continue
                server.error(
                    (
                        f"Attempting to send message 0x{message.header():02X} "
                        "to client socket FD({self._client.fileno()}) raised an exception!"
                    ),
                    err=err,
                )
            except Exception as err:
                server.error(
                    (
                        f"Attempting to send message 0x{message.header():02X} "
                        "to client socket FD({self._client.fileno()}) raised an unexpected exception!"
                    ),
                    err=err,
                )
            finally:
                del message


class Server(Service, Thread):
    def __init__(
        self,
        config=CONFIG_SERVER,
        socket_path=SOCKET,
        log_level=LOG_LEVEL,
        log_file=LOG_PATH_SERVER,
    ):
        Thread.__init__(self, name="SMDServerThread", daemon=False)
        Service.__init__(
            self, NAME_SERVER, DIRECTORY_MODULES, config, log_level, log_file
        )
        self._socket = None
        self._clients = dict()
        self._running = Event()
        self._socket_path = socket_path

    def run(self):
        self.info(
            f"Starting System Management Daemon Server (v{VERSION}) listening thread.."
        )
        if exists(self._socket_path):
            try:
                remove(self._socket_path)
            except OSError as err:
                self.error(
                    f'Attempting to remove the UNIX socket "{self._socket_path}" raised an exception!',
                    err=err,
                )
                self.stop()
                return
        else:
            socket_dir = dirname(self._socket_path)
            if not isdir(socket_dir) or not exists(socket_dir):
                try:
                    makedirs(socket_dir, exist_ok=True)
                except OSError as err:
                    self.error(
                        f'Attempting to create the UNIX socket "{self._socket_path}" raised an exception!',
                        err=err,
                    )
                    self.stop()
                    return
            del socket_dir
        try:
            self._socket = socket(AF_UNIX, SOCK_STREAM)
            self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self._socket.bind(self._socket_path)
            self._socket.listen(SOCKET_BACKLOG)
            chown(self._socket_path, 0, 8008)
            chmod(self._socket_path, 0o760)
            self._socket.setblocking(False)
        except (OSError, socket_err) as err:
            self.error(
                f'Attempting to listen on the UNIX socket "{self._socket_path}" raised an exception!',
                err=err,
            )
            self.stop()
            return
        self._running.clear()
        self._dispatcher.start()
        poll = epoll()
        poll.register(self._socket.fileno(), EPOLLIN)
        try:
            while not self._running.is_set():
                for file, event in poll.poll(1):
                    if file == self._socket.fileno():
                        client, _ = self._socket.accept()
                        poll.register(client.fileno(), EPOLLIN)
                        self._clients[client.fileno()] = ServerClient(client)
                        self.debug(
                            f"Client connected to server on socket FD({client.fileno()})."
                        )
                        del client
                        continue
                    if event & EPOLLIN and file in self._clients:
                        try:
                            message = self._clients[file].read()
                            self._dispatcher.add(file, message)
                            self.debug(
                                f"Received message type 0x{message.header():02X} from client "
                                f"socket PID({message.get('pid', -1)})/FD({file})."
                            )
                            if LOG_PAYLOAD and len(message) > 0:
                                self.error(f"[RECV <] MESSAGE DUMP: {message}")
                            del message
                            continue
                        except OSError as err:
                            self._clients[file].socket().setblocking(0)
                            if err.errno == 1000:
                                self.debug(f"Client on socket FD({file}) disconnected!")
                                poll.unregister(file)
                                self._clients[file].close()
                                del self._clients[file]
                                continue
                            else:
                                self.error(
                                    f"Client connection on socket FD({file}) raised an exception!",
                                    err=err,
                                )
                                continue
                    if event & EPOLLHUP or event & EPOLLERR:
                        self.error(
                            f"Client on socket FD({file}) has been disconnected due to errors!"
                        )
                        poll.unregister(file)
                        self._clients[file].close()
                        del self._clients[file]
                        continue
        except Exception as err:
            self.error(
                "An exception was raised during server thread operation!", err=err
            )
        finally:
            poll.unregister(self._socket.fileno())
            del poll
        self._stop_server()

    def stop(self):
        self._running.set()

    def wait(self):
        self._running.wait()

    def flush(self):
        clients = list(self._clients.keys())
        for client in clients:
            if client in self._clients:
                self._clients[client].flush(self)
        del clients

    def __hash__(self):
        return hash(NAME_SERVER)

    def is_server(self):
        return True

    def _stop_server(self):
        self.info("Stopping System Management Daemon Server Thread..")
        self.send(None, [Message(header=HOOK_SHUTDOWN)])
        self._dispatcher.stop()
        self._running.set()
        try:
            if self._socket is not None:
                self._socket.shutdown(SHUT_RDWR)
                self._socket.close()
            remove(self._socket_path)
        except (OSError, socket_err) as err:
            self.error(
                f'Attempting to close the UNIX socket "{self._socket_path}" raised an exception!',
                err=err,
            )
        self.debug("Server Thread shutdown complete.")

    def send(self, eid, message_result):
        if isinstance(message_result, Message):
            message_result = [message_result]
        elif not isinstance(message_result, list) and not isinstance(
            message_result, tuple
        ):
            return
        for message in message_result:
            if eid is None or message.is_multicast():
                clients = list(self._clients.keys())
                for client in clients:
                    if client in self._clients:
                        self._clients[client].add(message)
                del clients
            elif eid is not None and eid in self._clients:
                self._clients[eid].add(message)
        self.flush()

    def notify(self, title, message=None, icon=None):
        self.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={"icon": icon, "title": title, "body": message},
            ),
        )

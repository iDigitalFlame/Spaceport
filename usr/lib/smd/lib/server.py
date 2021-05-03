#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# The Server class is the daemon responsible for the primary privileged functions
# executed by the System Management Daemon. This class extends the Service class and
# is executed as a thread for socket processing.


from threading import Thread, Event
from lib.structs.service import Service
from lib.structs.message import Message
from os.path import exists, isdir, dirname
from os import remove, chmod, chown, makedirs
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
    NAME_SERVER,
    LOG_FILE_SERVER,
    LOG_LEVEL,
    LOG_PAYLOAD,
    SOCKET,
    VERSION,
    CONFIG_SERVER,
    HOOK_SHUTDOWN,
    DIRECTORY_MODULES,
    SOCKET_BACKLOG,
)


class ServerClient(object):
    def __init__(self, client):
        self._qeue = list()
        self._client = client
        self._client.setblocking(0)

    def read(self):
        self._client.setblocking(1)
        message = Message(stream=self._client)
        self._client.setblocking(0)
        return message

    def close(self):
        self._client.close()

    def socket(self):
        return self._client

    def add(self, message):
        self._qeue.append(message)

    def flush(self, server):
        while len(self._qeue) > 0:
            message = self._qeue.pop()
            try:
                message.send(self._client)
                server.debug(
                    'Message "%s" was sent to client socket FD(%d).'
                    % (message.header(), self._client.fileno())
                )
                if LOG_PAYLOAD and len(message) > 0:
                    server.error("[SEND >] MESSAGE DUMP: %s" % str(message))
            except OSError as err:
                if err.errno == 32 or err.errno == 9:
                    server.warning(
                        "Client socket FD(%d) has been disconnected!"
                        % self._client.fileno()
                    )
                else:
                    server.error(
                        'Attempting to send Message "%s" to client socket FD(%d) raised an exception!'
                        % (message.header(), self._client.fileno()),
                        err=err,
                    )
            except Exception as err:
                server.error(
                    'Attempting to send Message "%s" to client socket FD(%d) raised an exception!'
                    % (message.header(), self._client.fileno()),
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
        log_file=LOG_FILE_SERVER,
    ):
        Thread.__init__(self)
        Service.__init__(
            self, NAME_SERVER, DIRECTORY_MODULES, config, log_level, log_file
        )
        self._swap = dict()
        self._socket = None
        self._clients = dict()
        self._running = Event()
        self._socket_path = socket_path

    def run(self):
        self.info(
            "Starting System Management Daemon Server (version: %s) listening thread.."
            % VERSION
        )
        if exists(self._socket_path):
            try:
                remove(self._socket_path)
            except OSError as err:
                self.error(
                    'Attempting to remove the UNIX socket "%s" raised an exception!'
                    % self._socket_path,
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
                        'Attempting to create the UNIX socket "%s" raised an exception!'
                        % self._socket_path,
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
            chown(self._socket_path, 0, 0)
            chmod(self._socket_path, 754)
            self._socket.setblocking(0)
        except (OSError, socket_err) as err:
            self.error(
                'Attempting to create the UNIX socket "%s" raised an exception!'
                % self._socket_path,
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
                        self.info(
                            "Client connected to server on socket FD(%d)."
                            % client.fileno()
                        )
                        del client
                        continue
                    if event & EPOLLIN and file in self._clients:
                        try:
                            message = self._clients[file].read()
                            self._dispatcher.add(file, message)
                            self.debug(
                                'Received message type "%s" from client socket FD(%d).'
                                % (message.header(), file)
                            )
                            if LOG_PAYLOAD and len(message) > 0:
                                self.error("[RECV <] MESSAGE DUMP: %s" % str(message))
                            del message
                            continue
                        except OSError as err:
                            self._clients[file].socket().setblocking(0)
                            if err.errno == 1000:
                                self.debug(
                                    "Client on socket FD(%d) disconnected!" % file
                                )
                                poll.unregister(file)
                                self._clients[file].close()
                                del self._clients[file]
                                continue
                            else:
                                self.error(
                                    "Client connection on socket FD(%d) raised an exception!"
                                    % file,
                                    err=err,
                                )
                                continue
                    if event & EPOLLHUP or event & EPOLLERR:
                        self.error(
                            "Client on socket FD(%d) has been disconnected due to errors!"
                            % file
                        )
                        poll.unregister(file)
                        self._clients[file].close()
                        del self._clients[file]
                        continue
        except Exception as err:
            self.error(
                "An exception was rised during server thread operation!", err=err
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
            if isinstance(self._socket, socket):
                self._socket.close()
            remove(self._socket_path)
        except (OSError, socket_err) as err:
            self.error(
                'Attempting to close the UNIX socket "%s" raised an exception!'
                % self._socket_path,
                err=err,
            )
        self.debug("Server Thread shutdown complete.")

    def set_swap(self, name, value):
        self._swap[name] = value
        return value

    def swap(self, name, value=None):
        if name not in self._swap and value is not None:
            self._swap[name] = value
        return self._swap.get(name, value)

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

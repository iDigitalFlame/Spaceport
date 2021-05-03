#!/usr/bin/false
# The Message class is a subclass of the "Storage" class that is designed specifically
# to be passed between client and server in binary format quickly.
#
# While using the Storage class to be internally flexable, the Message class also focuses
# on the ability to be written directly to a stream and read quickly.
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

from os import getpid
from traceback import format_exc
from lib.util import get_pid_uid
from struct import unpack_from, pack
from lib.structs.storage import SafeStorage
from json import loads, dumps, JSONDecodeError
from socket import socket, AF_UNIX, SHUT_RDWR, SOCK_STREAM, timeout as socket_timeout
from lib.constants import (
    HOOK_ERROR,
    SOCKET_READ_ERRNO,
    HOOK_TRANSLATIONS,
    SOCKET_READ_INT_SIZE,
)


def send_exception(header, err):
    return Message(
        header=HOOK_ERROR,
        payload={
            "hook": header,
            "error": str(err),
            "trace": format_exc(limit=3),
            "result": "Received an exception when attempting to process a request!",
        },
    )


def send_message(sock, header, wait=None, timeout=0, payload=None, ignore_errors=False):
    data = None
    if payload is not None:
        if isinstance(payload, dict):
            data = payload
        elif isinstance(payload, str):
            try:
                data = loads(payload)
            except JSONDecodeError as err:
                raise OSError(
                    f'Paramater "payload" must be properly JSON formatted! ({err})'
                )
        else:
            raise OSError('Paramater "payload" must be a Python dict or JSON string!')
    try:
        server = socket(AF_UNIX, SOCK_STREAM)
        server.connect(sock)
        server.setblocking(True)
    except OSError as err:
        if not ignore_errors:
            raise err
        return None
    message = Message(header=header)
    if isinstance(data, dict):
        message.update(data)
    del data
    message["pid"] = getpid()
    try:
        time = None
        message.send(server)
        if wait is None:
            return None
        if isinstance(timeout, int) and timeout > 0:
            time = timeout
            server.settimeout(time)
        header = str(wait)
        keyword = None
        if (isinstance(wait, list) or isinstance(wait, tuple)) and len(wait) >= 2:
            header = str(wait[0])
            keyword = str(wait[1])
        try:
            header = int(header)
        except ValueError:
            if str(header).lower() in HOOK_TRANSLATIONS:
                header = HOOK_TRANSLATIONS[str(header).lower()]
        try:
            while True:
                try:
                    response = Message(stream=server)
                    if response.header() == header:
                        if keyword is None:
                            return response
                        elif keyword in response:
                            return response
                    server.setblocking(True)
                    server.settimeout(time)
                except BlockingIOError:
                    pass
        except (KeyboardInterrupt, socket_timeout) as err:
            raise err
        finally:
            del header
            del keyword
    except OSError as err:
        if not ignore_errors:
            raise err
        return None
    finally:
        server.shutdown(SHUT_RDWR)
        server.close()
        del server
        del message


class Message(SafeStorage):
    def __init__(self, header=None, payload=None, stream=None):
        if not isinstance(stream, socket) and not isinstance(header, int):
            raise OSError('Paramater "header" must be a integer!')
        self._header = header
        self._multicast = False
        if payload is not None and not isinstance(payload, dict):
            raise OSError('Paramater "payload" must be a Python dict!')
        elif isinstance(payload, dict):
            self.update(payload)
        if isinstance(stream, socket):
            self.recv(stream)

    def header(self):
        return self._header

    def __str__(self):
        return f"0x{self._header:02X} {super.__str__(self)}"

    def get_user(self):
        if "pid" not in self:
            return None
        return get_pid_uid(self.pid)

    def multicast(self):
        return self._multicast

    def get_header(self):
        return self._header

    def recv(self, stream):
        if not isinstance(stream, socket):
            raise OSError('Parameter "stream" must be a Python socket!')
        size_bytes = stream.recv(SOCKET_READ_INT_SIZE)
        if not isinstance(size_bytes, bytes) or len(size_bytes) == 0:
            raise OSError(SOCKET_READ_ERRNO, None)
        if not isinstance(size_bytes, bytes) or len(size_bytes) != SOCKET_READ_INT_SIZE:
            raise OSError(
                "Attempting to read a Message returned an incorrect header length!"
            )
        self._header = unpack_from("I", size_bytes)[0]
        if not isinstance(self._header, int) or self._header <= 0:
            raise OSError("Attempting to read a Message returned an incorrect header!")
        size_bytes = stream.recv(SOCKET_READ_INT_SIZE)
        if not isinstance(size_bytes, bytes) or len(size_bytes) != SOCKET_READ_INT_SIZE:
            raise OSError(
                "Attempting to read a Message returned an incorrect payload length!"
            )
        payload_size = unpack_from("I", size_bytes)[0]
        if not isinstance(payload_size, int) or payload_size < 0:
            raise OSError(
                "Attempting to read a Message returned an incorrect payload length!"
            )
        if payload_size > 0:
            payload_bytes = stream.recv(payload_size)
            if (
                not isinstance(payload_bytes, bytes)
                or len(payload_bytes) != payload_size
            ):
                raise OSError(
                    "Attempting to read a Message returned an incorrect payload!"
                )
            try:
                payload = loads(payload_bytes.decode("UTF-8"))
                if isinstance(payload, dict):
                    self.update(payload)
                else:
                    raise OSError(
                        "Attempting to read a Message payload returned a non-dict object!"
                    )
                del payload
            except (UnicodeDecodeError, JSONDecodeError) as err:
                raise OSError(
                    f"Attempting to read a Message payload raised an exception! ({err})"
                )
            del payload_bytes
        del size_bytes
        del payload_size
        stream.setblocking(False)

    def send(self, stream):
        if not isinstance(stream, socket):
            raise OSError('Parameter "stream" must be a Python socket!')
        stream.sendall(pack("I", self._header))
        if super().__len__() > 0:
            try:
                payload = dumps(self)
                stream.sendall(pack("I", len(payload)))
                stream.sendall(payload.encode("UTF-8"))
                del payload
            except (UnicodeEncodeError, JSONDecodeError) as err:
                raise OSError(
                    f"Received an exception attempting to encode Message payload! ({err})"
                )
        else:
            stream.sendall(pack("I", 0))

    def is_multicast(self):
        return self._multicast

    def is_from_root(self):
        if "pid" not in self:
            return False
        return get_pid_uid(self["pid"]) == 0

    def is_from_client(self):
        return self.get("id") is not None

    def set_header(self, header):
        self._header = header

    def set_multicast(self, multicast=True):
        self._multicast = multicast
        return self

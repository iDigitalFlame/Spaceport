#!/usr/bin/false
# The Message class is a subclass of the "Storage" class that is designed specifically
# to be passed between client and server in binary format quickly.
#
# While using the Storage class to be internally flexable, the Message class also focuses
# on the ability to be written directly to a stream and read quickly.
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

from os import getpid
from traceback import format_exc
from struct import unpack_from, pack
from lib.structs.storage import Storage
from json import loads, dumps, JSONDecodeError
from socket import socket, AF_UNIX, SHUT_RDWR, SOCK_STREAM, timeout as socket_timeout
from lib.constants import (
    HOOK_ERROR,
    SOCKET_READ_ERRNO,
    HOOK_TRANSLATIONS,
    SOCKET_READ_INT_SIZE,
)


def as_error(err):
    return {"error": err}


def send_exception(header, err):
    return Message(
        header=HOOK_ERROR,
        payload={
            "hook": header,
            "error": str(err),
            "trace": format_exc(limit=3),
            "result": "Error when attempting to process a request!",
        },
    )


def send_message(sock, header, wait=None, timeout=0, payload=None, errors=True):
    d = None
    if payload is not None:
        if isinstance(payload, dict):
            d = payload
        elif isinstance(payload, str):
            try:
                d = loads(payload)
            except JSONDecodeError as err:
                raise OSError(f'"payload" must be JSON formatted: {err}')
        else:
            raise OSError('"payload" must be a Dict or JSON string')
    try:
        s = socket(AF_UNIX, SOCK_STREAM)
        s.connect(sock)
        s.settimeout(5)
        s.setblocking(True)
    except OSError as err:
        if errors:
            raise err
        return None
    m = Message(header=header)
    if isinstance(d, dict):
        m.update(d)
    del d
    m["pid"] = getpid()
    try:
        m.send(s)
        if wait is None:
            return None
        t = None
        if isinstance(timeout, int) and timeout > 0:
            t = timeout
            s.settimeout(timeout)
        else:
            s.settimeout(None)
        k = None
        header = wait
        if (isinstance(wait, list) or isinstance(wait, tuple)) and len(wait) >= 2:
            header = str(wait[0])
            k = str(wait[1])
        try:
            header = int(header)
        except ValueError:
            z = str(header).lower()
            if z in HOOK_TRANSLATIONS:
                header = HOOK_TRANSLATIONS[z]
            del z
        try:
            while True:
                try:
                    r = Message(stream=s)
                    if r.header() == header:
                        if k is None:
                            return r
                        elif k in r:
                            return r
                    s.setblocking(True)
                    s.settimeout(t)
                except BlockingIOError:
                    pass
        except (KeyboardInterrupt, socket_timeout) as err:
            raise err
        finally:
            del k
            del header
    except OSError as err:
        if errors:
            raise err
        return None
    finally:
        s.shutdown(SHUT_RDWR)
        s.close()
        del s
        del m


class Message(Storage):
    def __init__(self, header=None, payload=None, stream=None):
        Storage.__init__(self, no_fail=True)
        if not isinstance(stream, socket) and not isinstance(header, int):
            raise OSError('"header" must be a Integer')
        self._header = header
        self._multicast = False
        if payload is not None and not isinstance(payload, dict):
            raise OSError('"payload" must be a Dict')
        elif isinstance(payload, dict):
            self.update(payload)
        if isinstance(stream, socket):
            self.recv(stream)

    def header(self):
        return self._header

    def __str__(self):
        return f"0x{self._header:02X} {super.__str__(self)}"

    def is_error(self):
        if not self.__contains__("error"):
            return False
        return isinstance(self.get("error"), str) and len(self.get("error")) > 0

    def recv(self, stream):
        if not isinstance(stream, socket):
            raise OSError('"stream" must be a Socket')
        n = stream.recv(SOCKET_READ_INT_SIZE)
        if not isinstance(n, bytes) or len(n) == 0:
            raise OSError(SOCKET_READ_ERRNO, None)
        if not isinstance(n, bytes) or len(n) != SOCKET_READ_INT_SIZE:
            raise OSError("Read an incorrect header length")
        self._header = unpack_from("I", n)[0]
        if not isinstance(self._header, int) or self._header <= 0:
            raise OSError("Read an incorrect header value")
        n = stream.recv(SOCKET_READ_INT_SIZE)
        if not isinstance(n, bytes) or len(n) != SOCKET_READ_INT_SIZE:
            raise OSError("Read an incorrect payload length")
        s = unpack_from("I", n)[0]
        if not isinstance(s, int) or s < 0:
            raise OSError("Read an incorrect payload value")
        if s > 0:
            p = stream.recv(s)
            if not isinstance(p, bytes) or len(p) != s:
                raise OSError("Read an incorrect payload length")
            try:
                d = loads(p.decode("UTF-8"))
                if isinstance(d, dict):
                    self.update(d)
                else:
                    raise OSError("Read payload returned a non-Dict object")
                del d
            except (UnicodeDecodeError, JSONDecodeError) as err:
                raise OSError(err)
            del p
        del n
        del s
        stream.setblocking(False)

    def send(self, stream):
        if not isinstance(stream, socket):
            raise OSError('"stream" must be a Socket')
        stream.sendall(pack("I", self._header))
        if super().__len__() == 0:
            return stream.sendall(pack("I", 0))
        try:
            p = dumps(self)
            stream.sendall(pack("I", len(p)))
            stream.sendall(p.encode("UTF-8"))
            del p
        except (UnicodeEncodeError, JSONDecodeError) as err:
            raise OSError(err)

    def is_multicast(self):
        return self._multicast

    def is_from_client(self):
        return self.__contains__("id") and isinstance(self["id"], str)

    def set_header(self, header):
        self._header = header

    def set_multicast(self, multicast=True):
        self._multicast = multicast
        return self

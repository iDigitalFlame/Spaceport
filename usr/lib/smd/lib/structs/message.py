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

# message.py
#   The Message class is a subclass of the "Storage" class that is designed specifically
#   to be passed between client and server in binary format quickly.

from os import getuid
from lib.util import num, nes
from struct import unpack, pack
from traceback import format_exc
from lib.constants import HOOK_ERROR
from lib.structs.storage import Flex
from json import loads, dumps, JSONDecodeError
from socket import socket, AF_UNIX, SHUT_RDWR, SOCK_STREAM
from lib.constants.config import HOOK_TRANSLATIONS, LOG_FRAME_LIMIT, TIMEOUT_SEC_MESSAGE


def as_error(err):
    if not nes(err):
        return {"error": ""}
    if err[-1] == "\n":
        return {"error": err[:-1]}
    return {"error": err}


def as_exception(header, err):
    return Message(
        HOOK_ERROR,
        {
            "hook": header,
            "error": f"{err}",
            "trace": format_exc(limit=LOG_FRAME_LIMIT),
            "result": "Error processing request!",
        },
    )


def _wait_for(sock, wait, timeout):
    t, k, h = timeout, None, wait
    sock.settimeout(t)
    if (isinstance(wait, list) or isinstance(wait, tuple)) and len(wait) >= 2:
        h, k = f"{wait[0]}", f"{wait[1]}"
    if nes(h) and h in HOOK_TRANSLATIONS:
        h = HOOK_TRANSLATIONS[h]
    else:
        try:
            h = num(h)
        except (TypeError, ValueError):
            h = HOOK_TRANSLATIONS.get(f"{h}".lower())
    try:
        while True:
            try:
                r = Message(stream=sock)
                if h is None and k is None:
                    return r
                if h is None and k is not None and k in r:
                    return r
                if r.header() == h and (k is None or k in r):
                    return r
                sock.setblocking(True)
                sock.settimeout(t)
                del r
            except BlockingIOError:
                pass
            except KeyboardInterrupt:
                break
    finally:
        del t, k, h
    return None


def send_message(sock, header, wait=None, timeout=None, payload=None, errors=True):
    if payload is not None:
        if isinstance(payload, dict):
            d = payload
        elif isinstance(payload, str):
            try:
                d = loads(payload)
            except JSONDecodeError as err:
                raise ValueError(f'"payload" is not properly formatted JSON: {err}')
        else:
            raise ValueError('"payload" must be a dict or JSON string')
    else:
        d = None
    try:
        s = socket(AF_UNIX, SOCK_STREAM)
        s.connect(sock)
        s.settimeout(TIMEOUT_SEC_MESSAGE if not isinstance(timeout, int) else timeout)
        s.setblocking(True)
    except OSError as err:
        if errors:
            raise err
        return None
    m = Message(header, d)
    del d
    try:
        m.send(s)
        if wait is not None:
            return _wait_for(s, wait, timeout)
    except OSError as err:
        if errors:
            raise err
        return None
    finally:
        s.shutdown(SHUT_RDWR)
        s.close()
        del s, m
    return None


class Message(Flex):
    __slots__ = ("_pid", "_uid", "_header", "_multicast")

    def __init__(self, header=None, payload=None, stream=None, pid=None, uid=None):
        if not isinstance(stream, socket) and not isinstance(header, int):
            raise ValueError('"header" must be an integer')
        Flex.__init__(self)
        self._pid, self._uid = pid, uid
        self._header, self._multicast = header, False
        if payload is not None:
            self.update(payload)
        if isinstance(stream, socket):
            self.recv(stream)

    def uid(self):
        return self._uid

    def pid(self):
        return self._pid

    def header(self):
        return self._header

    def __str__(self):
        if super().__len__() == 0:
            return f"0x{self._header:02X} {'{}'}"
        return f"0x{self._header:02X} {super().__str__()}"

    def is_error(self):
        v = self.get("error", None)
        return v if nes(v) else False

    def recv(self, stream):
        if not isinstance(stream, socket):
            raise OSError('"stream" must be a socket')
        b = stream.recv(5)
        if not isinstance(b, bytes):
            raise OSError("invalid header")
        if len(b) == 0:
            raise OSError(0x3E8, None)
        if len(b) != 5:
            raise OSError("invalid header length")
        try:
            self._header, n = unpack(">BI", b)
        except Exception:
            raise OSError("invalid header value")
        del b
        if not isinstance(self._header, int) or self._header <= 0:
            raise OSError("invalid header value")
        if not isinstance(n, int) or n < 0:
            raise OSError("invalid payload length value")
        if n > 0:
            p = stream.recv(n)
            if not isinstance(p, bytes) or len(p) != n:
                raise OSError("invalid payload length (EOF?)")
            try:
                d = loads(p.decode("UTF-8"))
                if not isinstance(d, dict):
                    raise OSError("payload data is an invalid type")
                self.update(d)
                del d
            except (UnicodeDecodeError, JSONDecodeError) as err:
                raise OSError(f"payload data is malformed: {err}")
            finally:
                del p
        del n
        stream.setblocking(False)

    def send(self, stream):
        if not isinstance(stream, socket):
            raise OSError('"stream" must be a socket')
        if super().__len__() == 0:
            return stream.sendall(pack(">BI", self._header, 0))
        try:
            p = dumps(self._data)
            if len(p) > 0xFFFFFFFF:
                raise ConnectionError("payload data is too large")
            stream.sendall(pack(">BI", self._header, len(p)))
            stream.sendall(p.encode("UTF-8"))
            del p
        except (UnicodeEncodeError, JSONDecodeError) as err:
            raise OSError(f"cannot convert message payload to JSON: {err}")

    def is_multicast(self):
        return self._multicast

    def is_same_client(self):
        try:
            return (
                isinstance(self._uid, int) and self._uid >= 0 and self._uid == getuid()
            )
        except OSError:
            return False

    def multicast(self, multicast=True):
        self._multicast = multicast
        return self

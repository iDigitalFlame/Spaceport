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

# sway.py
#   Interface to the Sway WM, can only be used in a user context.

from os import getenv
from os.path import exists
from struct import pack, unpack
from lib.util import nes, boolean
from collections import namedtuple
from json import loads, dumps, JSONDecodeError
from socket import (
    socket,
    AF_UNIX,
    SHUT_RDWR,
    SOL_SOCKET,
    SOCK_STREAM,
    SO_REUSEADDR,
)

Window = namedtuple(
    "Window", ["id", "pid", "app", "name", "focused", "sticky", "fullscreen"]
)
Display = namedtuple(
    "Display",
    [
        "x",
        "y",
        "id",
        "name",
        "make",
        "nodes",
        "power",
        "width",
        "height",
        "active",
    ],
)
Workspace = namedtuple(
    "Workspace",
    [
        "id",
        "num",
        "name",
        "text",
        "output",
        "urgent",
        "focused",
        "visible",
    ],
)

_MAGIC = b"i3-ipc"
_WINDOW_TYPES = ["con", "floating_con"]


def _nodes(w, n):
    if not isinstance(n, dict) or len(n) == 0:
        return
    if "pid" in n and n.get("type") in _WINDOW_TYPES:
        c = n.get("app_id")
        if (
            not nes(c)
            and "window_properties" in n
            and "class" in n["window_properties"]
        ):
            c = n["window_properties"]["class"]
        w.append(
            Window(
                int(n["id"]) if "id" in n else None,
                int(n["pid"]),
                c.lower(),
                n.get("name", "").lower(),
                boolean(n.get("focused", False)),
                boolean(n.get("sticky", False)),
                boolean(n.get("fullscreen_mode", 0)),
            )
        )
        del c
    if "nodes" in n:
        if isinstance(n["nodes"], list):
            for i in n["nodes"]:
                _nodes(w, i)
    if "floating_nodes" in n:
        if isinstance(n["floating_nodes"], list):
            for i in n["floating_nodes"]:
                _nodes(w, i)


def focused(sock=None):
    for i in windows(sock):
        if i.focused:
            return i
    return None


def windows(sock=None):
    _, r = swaymsg(4, sock=sock)
    w = list()
    try:
        _nodes(w, r)
    except ValueError as err:
        raise OSError(f"invalid window attribute: {err}")
    del r
    return w


def workspaces(sock=None):
    _, r = swaymsg(1, sock=sock)
    o = list()
    if not isinstance(r, list) or len(r) == 0:
        return o
    for i in r:
        if "name" not in i or i.get("type") != "workspace":
            continue
        try:
            o.append(
                Workspace(
                    int(i["id"]) if "id" in i else None,
                    int(i["num"]) if "num" in i else None,
                    i["name"],
                    i.get("representation"),
                    i.get("output"),
                    boolean(i.get("urgent", False)),
                    boolean(i.get("focused", False)),
                    boolean(i.get("visible", False)),
                )
            )
        except ValueError as err:
            raise OSError(f"invalid workspace attribute: {err}")
    del r
    return o


def displays(nodes=False, sock=None):
    _, r = swaymsg(3, sock=sock)
    o = list()
    if not isinstance(r, list) or len(r) == 0:
        return o
    for i in r:
        if "name" not in i or i.get("type") != "output":
            continue
        if "rect" not in i or "width" not in i["rect"] or "height" not in i["rect"]:
            continue
        n = None
        if nodes:
            n = i.get("nodes")
        try:
            o.append(
                Display(
                    i["rect"].get("x", 0),
                    i["rect"].get("y", 0),
                    int(i["id"]) if "id" in i else None,
                    i["name"],
                    i.get("make"),
                    n,
                    boolean(i.get("power", False)),
                    int(i["rect"]["width"]),
                    int(i["rect"]["height"]),
                    boolean(i.get("active", False)),
                )
            )
        except ValueError as err:
            raise OSError(f"invalid display attribute: {err}")
        del n
    del r
    return o


def swaymsg(command, payload=None, sock=None):
    if sock is not None:
        v = sock
    else:
        v = getenv("SWAYSOCK")
        if not nes(v):
            raise OSError('could not find a valid "SWAYSOCK" environment var')
    if not exists(v):
        raise OSError(f'socket path "{v}" does not exist')
    if not isinstance(command, int):
        raise ValueError('"command" must be a number')
    p = None
    if payload is not None:
        if isinstance(payload, str):
            p = payload
        elif isinstance(payload, dict):
            try:
                p = dumps(payload)
            except (TypeError, JSONDecodeError, OverflowError) as err:
                raise OSError(f'cannot convert "obj" to JSON: {err}')
        else:
            raise ValueError('"payload" must be a dict or JSON string')
    n = 0
    if p is not None:
        n = len(p)
    s = None
    try:
        s = socket(AF_UNIX, SOCK_STREAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.connect(v)
        s.setblocking(True)
    except OSError as err:
        if s is not None:
            s.close()
            del s
        raise OSError(f'cannot connect to socket "{v}": {err}')
    del v
    b = _MAGIC + pack("=II", n, command)
    if p is not None:
        b += p.encode("UTF-8")
    del p
    try:
        s.sendall(b)
        r = s.recv(14)
        if len(r) != 14:
            raise IOError("header size is invalid")
        v, c = unpack("=II", r[6:14])
        if v > 0:
            x = s.recv(v)
            if len(x) != v:
                raise IOError("payload size is invalid")
            p = loads(x.decode("UTF-8"))
        else:
            p = None
        del v, r
    except (OSError, JSONDecodeError, UnicodeDecodeError) as err:
        raise OSError(f"socket communication failed: {err}")
    finally:
        s.shutdown(SHUT_RDWR)
        s.close()
        del s
    return (c, p)

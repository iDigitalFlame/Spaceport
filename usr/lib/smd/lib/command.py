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

# command.py
#   Main helper for powerctl. Loads modules and provides command-line utility
#   functions.

from os import listdir
from lib.util import nes
from traceback import format_exc
from argparse import ArgumentParser
from importlib import import_module
from lib.util.file import perm_check
from sys import exit, stderr, _getframe
from lib.args import ARGS, DESCRIPTIONS
from os.path import basename, isdir, relpath
from lib.constants import EMPTY, NEWLINE, VERSION
from lib.constants.config import (
    NAME,
    SOCKET,
    NAME_CLIENT,
    NAME_SERVER,
    NAME_POWERCTL,
    DIRECTORY_BASE,
    LOG_FRAME_LIMIT,
    DIRECTORY_POWERCTL,
)


def powerctl():
    try:
        b = basename(_getframe(1).f_code.co_filename).lower()
    except (AttributeError, ValueError):
        b = None
    x = ArgumentParser(description="SMD Manager", usage="%(prog)s [options]")
    try:
        e = _load_powerctl(x, DIRECTORY_POWERCTL)
    except Exception as err:
        return print_error("Cannot load Modules!", err)
    if nes(b) and b != NAME_POWERCTL:
        if b.endswith("ctl"):
            b = b[:-3]
        if b in e:
            m = e[b]
            m.usage = f"{b} [options]"
        else:
            m = x
    else:
        m = x
    del x, b, e
    m.add_argument(
        "-S",
        type=str,
        dest="socket",
        help="socket to use for messages",
        action="store",
        default=SOCKET,
        metavar="socket",
        required=False,
    )
    m.add_argument(
        "--version",
        dest="version",
        help="show version information.",
        action="store_true",
        default=False,
        required=False,
    )
    a = m.parse_args()
    if a.version:
        print(
            f"System Management Daemon (v{VERSION})\n- iDigitalFlame (c) 2016 - 2023\n\n"
            f"System: {NAME} ({NAME_SERVER} / {NAME_CLIENT})"
        )
        exit(0)
    if hasattr(a, "subs") and isinstance(a.subs, dict) and len(a.subs) > 0:
        try:
            r = _exec_subs(a)
        except Exception as err:
            return print_error("Error during runtime!", err)
    else:
        r = False
    if not r:
        if "func" in a and callable(a.func):
            try:
                a.func(a)
            except Exception as err:
                return print_error("Error during runtime!", err)
        else:
            m.print_help()
            exit(2)
    del r, a, m


def _exec_subs(args):
    f = list()
    for n, i in args.subs.items():
        if not callable(i) or i in f:
            continue
        try:
            if not bool(getattr(args, n)):
                continue
        except AttributeError:
            continue
        f.append(i)
    if len(f) == 0:
        return False
    for i in f:
        r = i(args)
        if isinstance(r, bool):
            break
        del r
    del f
    return True


def module_base(path):
    if path == DIRECTORY_BASE:
        raise OSError(f'invalid sub-path "{path}"')
    p = relpath(path, DIRECTORY_BASE)
    if not nes(p):
        raise OSError(f'invalid path "{path}"')
    n = ord(p[0])
    if not (0x61 <= n <= 0x7A or 0x41 <= n <= 0x5A):
        raise OSError(f'invalid path "{path}" relative to "{DIRECTORY_BASE}"')
    del n
    if "/" not in p or "." in p:
        raise OSError(f'invalid path "{p}"')
    for x in range(0, len(p)):
        v = ord(p[x])
        if v == 0x2F or 0x61 <= v <= 0x7A or 0x41 <= v <= 0x5A or v == 0x5F:
            continue
        if 0x30 <= v <= 0x39 and x > 0 and ord(p[x - 1]) != 0x2F:
            continue
        del v
        raise OSError(f'invalid path "{p}"')
    return p.replace("/", ".")


def check_error(msg, message=None):
    if msg is None:
        return
    e = msg.is_error()
    if not nes(e):
        return
    if nes(message):
        return print_error(f"{message}: {e}!")
    return print_error(f"{e}!")


def try_get_attr(obj, name, call):
    if not nes(name):
        return None
    x = None
    try:
        x = getattr(obj, name)
    except AttributeError:
        try:
            x = getattr(obj, name.lower())
        except AttributeError:
            try:
                x = getattr(obj, name.upper())
            except AttributeError:
                try:
                    x = getattr(obj, name.capitalize())
                except AttributeError:
                    pass
    if callable(x) and call:
        try:
            return x()
        except TypeError:
            pass
    return x


def _load_powerctl(parser, directory):
    if not isdir(directory):
        raise OSError(f'path "{directory}" is not a directory')
    e, s = dict(), parser.add_subparsers(title="SMD Management Modules")
    x, b = listdir(directory), module_base(directory)
    for m in x:
        if not m.endswith(".py"):
            continue
        perm_check(f"{directory}/{m}", 0o7022, 0, 0)
        n = m[:-3].lower()
        if "/" in n or "\\" in n:
            n = basename(n)
        try:
            i = import_module(f"{b}.{n}")
        except ImportError as err:
            raise ImportError(f'error loading module "{directory}/{m}": {err}')
        d = try_get_attr(i, "DESCRIPTION", True)
        if not isinstance(d, str):
            d = DESCRIPTIONS.get(n)
        if not isinstance(d, str):
            d = f"{n.capitalize()} Power Module"
        a = try_get_attr(i, "ARGS", True)
        if a is None:
            a = ARGS.get(n)
        f = try_get_attr(i, "DEFAULT", False)
        if not callable(f):
            raise ValueError(
                f'error loading module "{directory}/{m}": missing "default" function'
            )
        w, r = dict(), s.add_parser(n, description=d)
        try:
            if isinstance(a, list) and len(a) > 0:
                for v in a:
                    if len(v) < 2:
                        continue
                    r.add_argument(v[0], **v[1])
                    if len(v) != 3:
                        continue
                    g = v[2]
                    if isinstance(g, str):
                        g = try_get_attr(i, g, False)
                    if callable(g):
                        if "dest" in v[1]:
                            w[v[1]["dest"]] = g
                        elif "metavar" in v[1]:
                            w[v[1]["metavar"]] = g
                        else:
                            w[v[0].replace("-", EMPTY)] = g
                    del g
        except (IndexError, TypeError) as err:
            raise ValueError(
                f'error loading module "{directory}/{m}": bad arguments ({err})'
            )
        r.set_defaults(func=f, subs=w)
        e[n] = r
        del w, r, f, i, a, d, n
    del x
    m = s.add_parser("modules", description="Loaded Modules List")
    m.set_defaults(func=lambda _: print(NEWLINE.join(e.keys())))
    del m, s
    return e


def print_error(message, error=None, quit=True, limit=LOG_FRAME_LIMIT):
    print(f"{message}\n", file=stderr)
    if error is not None:
        print(format_exc(limit=limit), file=stderr)
    if quit:
        exit(1)
    return False

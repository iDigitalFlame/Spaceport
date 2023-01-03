#!/usr/bin/false
# PowerCTL Module: Wireless
#  powerctl wifi, wifictl, wifi
#
# PowerCTL command line user module to configure wireless options.
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

from os import listdir
from os.path import exists, isdir
from lib.structs.message import send_message
from lib.util import read, boolean, print_error
from lib.constants import (
    EMPTY,
    NEWLINE,
    BOOLEANS,
    HOOK_RADIO,
    RADIO_PATH_WIFI,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_CONFIG,
)


def _is_enabled():
    for d in listdir(RADIO_PATH_WIFI):
        p = f"{RADIO_PATH_WIFI}/{d}/flags"
        w = f"{RADIO_PATH_WIFI}/{d}/wireless"
        del d
        if not exists(p) or not isdir(w):
            del p
            del w
            continue
        f = read(p, errors=False)
        del p
        del w
        if isinstance(f, str) and f.replace(NEWLINE, EMPTY) == "0x1003":
            return True
    return False


def config(arguments):
    set_config(arguments, "wireless", _is_enabled)


def command(arguments):
    if set_command(arguments, "wireless"):
        return
    default(arguments)


def default(arguments):
    try:
        if _is_enabled():
            return print("Wireless is enabled.")
    except OSError as err:
        return print_error("Error retriving Wireless status!", err)
    print("Wireless is disabled.")


def set_command(arguments, radio):
    c = arguments.command.lower()
    if c in BOOLEANS:
        _set(arguments.socket, radio, None, boolean(c))
        return True
    if arguments.args is not None and len(arguments.args) > 0:
        if c == "set":
            _set(arguments.socket, radio, None, boolean(arguments.args[0]))
        elif c == "boot":
            _set(arguments.socket, radio, arguments.args[0])
        else:
            return False
        return True
    return False


def set_config(arguments, radio, toggle=None):
    if toggle is not None and callable(toggle) and arguments.toggle:
        return _set(arguments.socket, radio, None, not toggle())
    if arguments.boot:
        return _set(arguments.socket, radio, arguments.boot)
    return _set(arguments.socket, radio, None, arguments.enable, arguments.disable)


def _set(socket, radio, boot=None, enable=False, disable=False):
    m = {"radio": radio}
    if boot is not None:
        m["type"] = MESSAGE_TYPE_CONFIG
        m["boot"] = boolean(boot)
        print(
            f'Setting "{radio}" boot status to "{"Enabled" if m["boot"] else "Disabled"}"!'
        )
    else:
        m["type"] = MESSAGE_TYPE_ACTION
        m["enabled"] = enable and not disable
        print(
            f'Setting "{radio}" status to "{"Enabled" if m["enabled"] else "Disabled"}"!'
        )
    try:
        send_message(socket, HOOK_RADIO, payload=m)
    except OSError as err:
        return print_error(f'Error setting "{radio}" status!', err)
    del m

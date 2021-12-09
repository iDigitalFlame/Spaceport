#!/usr/bin/false
# PowerCTL Module: Wireless
#  powerctl wifi, wifictl, wifi
#
# PowerCTL command line user module to configure wireless options.
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

from os import listdir
from os.path import exists, isdir
from lib.structs.message import send_message
from lib.util import read, boolean, print_error
from lib.constants import (
    EMPTY,
    BOOLEANS,
    HOOK_RADIO,
    RADIO_PATH_WIFI,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_CONFIG,
)


def _is_enabled():
    for device in listdir(RADIO_PATH_WIFI):
        path = f"{RADIO_PATH_WIFI}/{device}/flags"
        wireless = f"{RADIO_PATH_WIFI}/{device}/wireless"
        if not exists(path) or not isdir(wireless):
            del path
            del wireless
            continue
        flags = read(path, ignore_errors=False)
        del path
        del wireless
        if isinstance(flags, str) and flags.replace("\n", EMPTY) == "0x1003":
            return True
    return False


def config(arguments):
    set_config(arguments, "wireless", _is_enabled)


def command(arguments):
    if not set_command(arguments, "wireless"):
        default(arguments)


def default(arguments):
    try:
        if _is_enabled():
            print("Wireless is enabled.")
            return
        print("Wireless is disabled.")
    except OSError as err:
        return print_error(
            "Attempting to retrive wireless device status raised an exception!",
            err,
            True,
        )


def set_command(arguments, radio):
    command = arguments.command.lower()
    if command in BOOLEANS:
        _set(arguments.socket, radio, None, boolean(command))
        return True
    if arguments.args is not None and len(arguments.args) > 0:
        if command == "set":
            _set(arguments.socket, radio, None, boolean(arguments.args[0]))
            return True
        if command == "boot":
            _set(arguments.socket, radio, arguments.args[0])
            return True
    return False


def set_config(arguments, radio, toggle=None):
    if toggle is not None and callable(toggle) and arguments.toggle:
        return _set(arguments.socket, radio, None, not toggle())
    if arguments.boot:
        return _set(arguments.socket, radio, arguments.boot)
    return _set(arguments.socket, radio, None, arguments.enable, arguments.disable)


def _set(socket, radio, boot=None, enable=False, disable=False):
    message = {"radio": radio}
    if boot is not None:
        message["type"] = MESSAGE_TYPE_CONFIG
        message["boot"] = boolean(boot)
        print(
            f'Setting "{radio}" boot status to "{"Enabled" if message["boot"] else "Disabled"}"!'
        )
    else:
        message["type"] = MESSAGE_TYPE_ACTION
        message["enabled"] = enable and not disable
        print(
            f'Setting "{radio}" status to "{"Enabled" if message["enabled"] else "Disabled"}"!'
        )
    try:
        send_message(socket, HOOK_RADIO, None, None, message)
    except OSError as err:
        print_error(
            'Attempting to set "{radio}" status raised an Exception!', err, True
        )
    del message

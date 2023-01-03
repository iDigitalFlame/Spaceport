#!/usr/bin/false
# Module: Brightness (System)
#
# Sets and changes the System Brightness.
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

from lib.util import read, write
from lib.constants import (
    HOOK_BRIGHTNESS,
    BRIGHTNESS_PATH,
    BRIGHTNESS_PATH_MAX,
    MESSAGE_TYPE_ACTION,
)

HOOKS_SERVER = {HOOK_BRIGHTNESS: "brightness"}


def brightness(server, message):
    if message.type != MESSAGE_TYPE_ACTION or message.level is None:
        return
    try:
        n = int(message.level)
        m = int(read(BRIGHTNESS_PATH_MAX), 10)
    except (OSError, ValueError) as err:
        return server.error(
            "Error changing Brightness, received a non-integer value!", err=err
        )
    if n < 0:
        return server.error("Client attempted to change Brightness to less than zero!")
    elif n > m:
        return server.error(
            "Client attempted to change Brightness highter than the max level!"
        )
    server.debug(f'Setting Brightness level to "{n}".')
    try:
        write(BRIGHTNESS_PATH, str(n))
    except OSError as err:
        server.error("Error setting the Brightness level!", err=err)
    del n
    del m

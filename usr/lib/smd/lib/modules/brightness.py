#!/usr/bin/false
# Module: Brightness (System)
#
# Sets and changes the System Brightness.
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
        level = int(message.level)
        level_max = int(read(BRIGHTNESS_PATH_MAX, ignore_errors=False))
    except (OSError, ValueError) as err:
        return server.error(
            "Error changing brightness, received a non-integer value!", err=err
        )
    if level < 0:
        return server.error(
            "Client attempted to change the brightness to less than zero!"
        )
    elif level > level_max:
        return server.error(
            "Client attempted to change the brightness highter than the max level!"
        )
    server.debug(f'Setting brightness level to "{level}".')
    try:
        write(BRIGHTNESS_PATH, str(level), ignore_errors=False)
    except OSError as err:
        server.error(
            "An exception was raised when attempting to set brightness level!", err=err
        )
    del level
    del level_max

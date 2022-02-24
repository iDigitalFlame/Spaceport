#!/usr/bin/false
# PowerCTL Module: Brightness
#  powerctl brightness, brightnessctl, brightness
#
# PowerCTL command line user module to configure Screen Brightness options.
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

from math import floor, ceil
from lib.util import read, print_error
from lib.structs.message import send_message
from lib.constants import (
    EMPTY,
    BRIGHTNESS_PATH,
    HOOK_BRIGHTNESS,
    BRIGHTNESS_PATH_MAX,
    MESSAGE_TYPE_ACTION,
)


def default(arguments):
    try:
        c = int(read(BRIGHTNESS_PATH), 10)
        m = int(read(BRIGHTNESS_PATH_MAX), 10)
    except (OSError, ValueError) as err:
        return print_error("Error retriving Brightness levels!", err)
    if arguments.level and len(arguments.level) >= 1:
        if arguments.level.lower()[0] == "i":
            arguments.increase = True
            arguments.level = None
        elif arguments.level.lower()[0] == "d":
            arguments.decrease = True
            arguments.level = None
    if arguments.brightness or arguments.level:
        try:
            n = arguments.level if arguments.level else arguments.brightness
            if "%" in n:
                n = floor(float(m) * float(int(n.replace("%", EMPTY), 10) / 100))
            else:
                n = int(n)
        except ValueError as err:
            return print_error("Brightness level must be a number or percentage!", err)
        if n < 0:
            return print_error("Brightness level cannot be less than zero!")
        elif n > m:
            return print_error(
                f'Brightness level "{n}" cannot be greater than the max brightness "{m}"!'
            )
        try:
            send_message(
                arguments.socket,
                HOOK_BRIGHTNESS,
                payload={"type": MESSAGE_TYPE_ACTION, "level": n},
            )
        except OSError as err:
            return print_error("Error setting the Brightness level!", err)
        del n
    elif arguments.increase or arguments.decrease:
        n = c + (25 * (-1 if arguments.decrease else 1))
        if n < 0:
            n = 0
        elif n > m:
            n = m
        try:
            send_message(
                arguments.socket,
                HOOK_BRIGHTNESS,
                payload={"type": MESSAGE_TYPE_ACTION, "level": int(n)},
            )
        except OSError as err:
            return print_error("Error setting the Brightness level!", err)
        del n
    else:
        print(f"Brightness: {c}/{m} ({ceil((float(c) / float(m)) * 100.0)}%)")
    del c
    del m

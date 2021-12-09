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
        level = int(read(BRIGHTNESS_PATH, ignore_errors=False))
        level_max = int(read(BRIGHTNESS_PATH_MAX, ignore_errors=False))
    except (OSError, ValueError) as err:
        return print_error(
            "Attempting to retrive Brightness levels raised an exception!", err
        )
    if arguments.level and len(arguments.level) >= 1:
        if arguments.level.lower()[0] == "i":
            arguments.increase = True
            arguments.level = None
        elif arguments.level.lower()[0] == "d":
            arguments.decrease = True
            arguments.level = None
    if arguments.brightness or arguments.level:
        try:
            level_set = arguments.level if arguments.level else arguments.brightness
            if "%" in level_set:
                level_set = floor(
                    float(level_max) * float(int(level_set.replace("%", EMPTY)) / 100)
                )
            else:
                level_set = int(level_set)
        except ValueError as err:
            return print_error("Brightness level must be a number or percentage!", err)
        if level_set < 0:
            return print_error(
                f'Brightness level "{level_set}" cannot be less than zero!'
            )
        elif level_set > level_max:
            return print_error(
                f'Brightness level "{level_set}" cannot be greater than the max brightness "{level_max}"!'
            )
        try:
            send_message(
                arguments.socket,
                HOOK_BRIGHTNESS,
                payload={"type": MESSAGE_TYPE_ACTION, "level": level_set},
            )
        except OSError as err:
            return print_error(
                "Attempting to set Brightness level raised an exception!", err, True
            )
        del level_set
    elif arguments.increase or arguments.decrease:
        level_set = level + (25 * (-1 if arguments.decrease else 1))
        if level_set < 0:
            level_set = 0
        elif level_set > level_max:
            level_set = level_max
        try:
            send_message(
                arguments.socket,
                HOOK_BRIGHTNESS,
                payload={"type": MESSAGE_TYPE_ACTION, "level": level_set},
            )
        except OSError as err:
            return print_error(
                "Attempting to set Brightness level raised an exception!", err
            )
        del level_set
    else:
        print(
            f"Brightness: {level}/{level_max} ({ceil((float(level) / float(level_max)) * 100.0)}%)"
        )
    del level
    del level_max

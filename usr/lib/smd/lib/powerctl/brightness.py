#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# PowerCTL Module: Brightness
#  powerctl brightness, brightnessctl, brightness
#
# PowerCTL command line user module to configure Screen Brightness options.

from math import floor, ceil
from lib.util import read, print_error
from lib.structs.message import send_message
from lib.constants import BRIGHTNESS_FILE, BRIGHTNESS_FILE_MAX, HOOK_POWER, EMPTY

ARGS = [
    (
        "-i",
        {
            "required": False,
            "dest": "increase",
            "action": "store_true",
            "help": "Increase the current brightness level by 25.",
        },
    ),
    (
        "-d",
        {
            "required": False,
            "dest": "decrease",
            "action": "store_true",
            "help": "Decrease the current brightness level by 25.",
        },
    ),
    (
        "-s",
        {
            "required": False,
            "dest": "brightness",
            "metavar": "level",
            "type": str,
            "action": "store",
            "help": "Set the current brightness level.",
        },
    ),
    (
        "level",
        {
            "nargs": "?",
            "action": "store",
            "default": None,
            "help": "Set the current brightness level.",
        },
    ),
]
DESCRIPTION = "System Display Brightness Manager"


def default(arguments):
    try:
        level = int(read(BRIGHTNESS_FILE, ignore_errors=False))
        level_max = int(read(BRIGHTNESS_FILE_MAX, ignore_errors=False))
    except (OSError, ValueError) as err:
        print_error(
            "Attempting to retrive Brightness levels raised an exception!", err, True
        )
    else:
        if arguments.brightness or arguments.level:
            try:
                level_set = arguments.level if arguments.level else arguments.brightness
                if "%" in level_set:
                    level_set = floor(
                        float(level_max)
                        * float(int(level_set.replace("%", EMPTY)) / 100)
                    )
                else:
                    level_set = int(level_set)
                if level_set < 0:
                    print_error(
                        'Brightness level "%d" cannot be less than zero!' % level_set,
                        None,
                        True,
                    )
                elif level_set > level_max:
                    print_error(
                        'Brightness level "%d" cannot be greater than the max brightness "%d"!'
                        % (level_set, level_max),
                        None,
                        True,
                    )
                else:
                    try:
                        send_message(
                            arguments.socket,
                            HOOK_POWER,
                            None,
                            None,
                            {"type": "brightness", "level": level_set},
                        )
                    except OSError as err:
                        print_error(
                            "Attempting to set Brightness level raised an exception!",
                            err,
                            True,
                        )
            except ValueError as err:
                print_error(
                    "Brightness level must be a number or percentage!", err, True
                )
            finally:
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
                    HOOK_POWER,
                    None,
                    None,
                    {"type": "brightness", "level": level_set},
                )
            except OSError as err:
                print_error(
                    "Attempting to set Brightness level raised an exception!", err, True
                )
            finally:
                del level_set
        else:
            print(
                "Brightness: %d/%d (%d%%)"
                % (level, level_max, ceil((float(level) / float(level_max)) * 100.0))
            )
        del level
        del level_max

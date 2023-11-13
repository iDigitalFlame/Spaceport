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

# PowerCTL Module: Brightness
#   Command line user module to configure Screen Brightness options.

from math import floor, ceil
from lib.util.file import read
from lib.util import num, boolean
from lib import print_error, send_message
from lib.constants import EMPTY, MSG_ACTION, HOOK_BRIGHTNESS
from lib.constants.config import BRIGHTNESS_PATH, BRIGHTNESS_PATH_MAX


def default(args):
    # NOTE(dij): Fixup the "i" and "d" values being used as positional args.
    if args.level and len(args.level) >= 1:
        v = args.level.lower()
        if v[0] == "i":
            args.increase, args.level = True, None
        elif v[0] == "d":
            args.decrease, args.level = True, None
        del v
    try:
        c = num(read(BRIGHTNESS_PATH), False)
    except (ValueError, OSError) as err:
        return print_error("Cannot read the current Brightness!", err)
    try:
        x = num(read(BRIGHTNESS_PATH_MAX), False)
    except (ValueError, OSError) as err:
        return print_error("Cannot read the max Brightness!", err)
    if args.increase or args.decrease:
        v = c + round(floor(float(x) * 0.05) * (-1.0 if args.decrease else 1.0))
        if v < 0:
            v = 0
        elif v > x:
            v = x
        try:
            send_message(
                args.socket, HOOK_BRIGHTNESS, payload={"type": MSG_ACTION, "level": v}
            )
        except Exception as err:
            print_error("Cannot set Brightness!", err)
        finally:
            del v, x, c
        return
    if args.brightness or args.level:
        try:
            v = args.level if args.level else args.brightness
            if "%" in v:
                n = floor(float(x) * float(num(v.replace("%", EMPTY), False) / 100))
            else:
                n = num(v)
        except ValueError as err:
            return print_error("Brightness must be a number or percentage!", err)
        if n < 0:
            return print_error("Brightness cannot be less than zero!")
        elif n > x:
            return print_error(
                f'Brightness "{n}" cannot be greater than the max brightness "{x}"!'
            )
        if n == 0:
            try:
                a = input("Are you sure you want the Brightness to be zero? [y/N]: ")
            except (OSError, KeyboardInterrupt):
                return
            if not boolean(a):
                return
        try:
            send_message(
                args.socket, HOOK_BRIGHTNESS, payload={"type": MSG_ACTION, "level": n}
            )
        except Exception as err:
            return print_error("Cannot set Brightness!", err)
        finally:
            del v, x, c
        return
    print(f"Brightness: {c}/{x} ({ceil((float(c) / float(x)) * 100.0)}%)")
    del c, x

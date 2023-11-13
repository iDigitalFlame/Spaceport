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

# Module: System/Brightness
#   Sets and changes the System Brightness. Allows Brightness to be controlled
#   from userspace.

from lib.util import num
from lib.util.file import read, write
from lib.constants import MSG_ACTION, HOOK_BRIGHTNESS
from lib.constants.config import BRIGHTNESS_PATH, BRIGHTNESS_PATH_MAX

HOOKS_SERVER = {HOOK_BRIGHTNESS: "brightness"}


def brightness(server, message):
    if message.type != MSG_ACTION or message.level is None:
        return
    try:
        v = num(message.level, False)
    except ValueError:
        return server.error(
            "[m/brightness]: Received an invalid level value (it must be a number)!"
        )
    try:
        x = num(read(BRIGHTNESS_PATH_MAX), False)
    except (ValueError, OSError) as err:
        return server.error(
            "[m/brightness]: Cannot read or parse the max Brightness level!", err
        )
    if v > x:
        return server.error(
            f"[m/brightness]: Cannot set the Brightness level ({v}) to highter than the max level ({x})!"
        )
    server.debug(f'[m/brightness]: Setting Brightness level to "{v}".')
    try:
        write(BRIGHTNESS_PATH, f"{v}")
    except OSError as err:
        server.error("[m/brightness]: Cannot set the Brightness level!", err)
    del v, x

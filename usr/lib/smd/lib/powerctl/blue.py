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

# PowerCTL Module: Bluetooth
#   Command line user module to configure Bluetooth options.

from glob import glob
from lib.util import nes
from lib import print_error
from lib.util.file import read
from lib.constants.config import RADIO_PATH_BLUE
from lib.shared.radio import set_command, set_config


def default(_):
    try:
        if _bluetooth_enabled():
            return print("Bluetooth is enabled.")
    except OSError as err:
        return print_error("Cannot retrive Bluetooth status!", err)
    print("Bluetooth is disabled.")


def config(args):
    set_config(args, "bluetooth", _bluetooth_enabled)


def command(args):
    if set_command(args, "bluetooth"):
        return True
    default(args)


def _bluetooth_enabled():
    for i in glob(RADIO_PATH_BLUE):
        v = read(i, strip=True, errors=False)
        if nes(v) and v == "1":
            return True
        del v
        continue
    return False

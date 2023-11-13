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

# PowerCTL Module: Wireless
#   Command line user module to configure wireless options.

from glob import glob
from lib.util import nes
from lib import print_error
from lib.util.file import read
from os.path import dirname, isfile
from lib.constants.config import RADIO_PATH_WIFI
from lib.shared.wireless import set_command, set_config


def default(_):
    try:
        if _wifi_enabled():
            return print("Wireless is enabled.")
    except OSError as err:
        return print_error("Cannot retrive Wireless status!", err)
    print("Wireless is disabled.")


def config(args):
    set_config(args, "wireless", _wifi_enabled)


def command(args):
    if set_command(args, "wireless"):
        return True
    default(args)


def _wifi_enabled():
    for i in glob(f"{RADIO_PATH_WIFI}/*/wireless", recursive=False):
        p = f"{dirname(i)}/flags"
        if isfile(p):
            v = read(p, strip=True, errors=False)
            if nes(v) and v == "0x1003":
                return True
            del v
        del p
        continue
    return False

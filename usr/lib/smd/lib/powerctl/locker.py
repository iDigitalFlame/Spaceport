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

# PowerCTL Module: Locker
#   Command line user module to configure system sleep and hibernate inhibitors
#   using the Locker framework.

from lib.shared.locker import pase_locker
from lib.util import time_to_str, seconds
from lib import send_message, print_error, check_error
from lib.constants.config import LOCKER_TYPE_NAMES, TIMEOUT_SEC_MESSAGE
from lib.constants import (
    MSG_STATUS,
    MSG_ACTION,
    HOOK_LOCKER,
    LOCKER_TYPE_LID,
    LOCKER_TYPE_KEY,
    LOCKER_TYPE_LOCK,
    LOCKER_TYPE_BLANK,
    LOCKER_TYPE_SUSPEND,
    LOCKER_TYPE_HIBERNATE,
)


def config(args):
    v = list()
    pase_locker(v, LOCKER_TYPE_LID, args.lid, args.lid_force)
    pase_locker(v, LOCKER_TYPE_KEY, args.key, args.key_force)
    pase_locker(v, LOCKER_TYPE_BLANK, args.blank, args.blank_force)
    pase_locker(v, LOCKER_TYPE_SUSPEND, args.suspend, args.suspend_force)
    pase_locker(v, LOCKER_TYPE_LOCK, args.lockscreen, args.lockscreen_force)
    pase_locker(v, LOCKER_TYPE_HIBERNATE, args.hibernate, args.hibernate_force)
    if len(v) > 0:
        try:
            send_message(
                args.socket, HOOK_LOCKER, payload={"type": MSG_ACTION, "list": v}
            )
        except Exception as err:
            return print_error("Cannot update Lockers!", err)
    del v


def default(args):
    try:
        r = send_message(
            args.socket,
            HOOK_LOCKER,
            (HOOK_LOCKER, "lockers"),
            TIMEOUT_SEC_MESSAGE,
            {"type": MSG_STATUS},
        )
    except Exception as err:
        return print_error("Cannot retrive Lockers!", err)
    check_error(r, "Cannot retrive Lockers")
    if isinstance(r.lockers, dict) and len(r.lockers) > 0:
        n = seconds()
        print(f'{"Locker":15}{"Expires":8}\n{"="*32}')
        for i, s in r.lockers.items():
            print(f"{LOCKER_TYPE_NAMES.get(i, i):15}{time_to_str(s, n):<8}")
        del n
    else:
        return print("No Lockers are enabled.")
    del r

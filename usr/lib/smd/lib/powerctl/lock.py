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

# PowerCTL Module: Lock
#   Command line user module to lock the screen and optionally add some inhibitors
#   using the Locker framework to execute before locking.

from lib import print_error, send_message
from lib.shared.locker import pase_locker
from lib.constants import (
    HOOK_LOCK,
    MSG_ACTION,
    HOOK_LOCKER,
    TRIGGER_LOCK,
    LOCKER_TYPE_SUSPEND,
    LOCKER_TYPE_HIBERNATE,
)


def default(args):
    if args.timeout:
        args.suspend = args.timeout
    v = list()
    pase_locker(v, LOCKER_TYPE_SUSPEND, args.suspend, args.suspend_force)
    pase_locker(v, LOCKER_TYPE_HIBERNATE, args.hibernate, args.hibernate_force)
    if len(v) > 0:
        try:
            send_message(
                args.socket, HOOK_LOCKER, payload={"type": MSG_ACTION, "list": v}
            )
        except Exception as err:
            return print_error("Cannot update Lockers!", err)
    del v
    try:
        send_message(
            args.socket,
            HOOK_LOCK,
            payload={"force": args.force, "trigger": TRIGGER_LOCK},
        )
    except Exception as err:
        return print_error("Cannot trigger the Lockscreen!", err)

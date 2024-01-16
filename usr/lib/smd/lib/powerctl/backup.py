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

# PowerCTL Module: Backup
#   Command line user module to start/stop/pause/resume Backups.

from lib.util import nes
from datetime import datetime
from lib.constants.config import TIMEOUT_SEC_MESSAGE
from lib import print_error, send_message, check_error
from lib.constants import (
    EMPTY,
    MSG_PRE,
    MSG_POST,
    MSG_USER,
    MSG_STATUS,
    MSG_CONFIG,
    MSG_ACTION,
    HOOK_BACKUP,
)


def config(args):
    p = dict()
    if args.start or ((nes(args.dir) or nes(args.path)) and not args.stop):
        p["force"], p["type"], p["action"] = args.force, MSG_ACTION, MSG_PRE
        if nes(args.dir):
            p["dir"] = args.dir
        elif nes(args.path):
            p["dir"] = args.path
        p["full"] = args.full
    elif args.pause:
        p["type"], p["action"] = MSG_CONFIG, MSG_PRE
    elif args.resume:
        p["type"], p["action"] = MSG_CONFIG, MSG_POST
    elif args.stop:
        p["type"], p["action"] = MSG_ACTION, MSG_POST
        if nes(args.dir):
            p["dir"] = args.dir
        elif nes(args.path):
            p["dir"] = args.path
    elif args.clear:
        p["type"] = MSG_USER
    else:
        return default(args)
    try:
        r = send_message(args.socket, HOOK_BACKUP, HOOK_BACKUP, TIMEOUT_SEC_MESSAGE, p)
    except Exception as err:
        return print_error("Cannot configure Backup Plans!", err)
    check_error(r)
    m = r.result
    if nes(m):
        print(m)
    del m, r


def default(args):
    try:
        r = send_message(
            args.socket,
            HOOK_BACKUP,
            HOOK_BACKUP,
            TIMEOUT_SEC_MESSAGE,
            {"type": MSG_STATUS},
        )
    except Exception as err:
        return print_error("Cannot retrive Backup Plans!", err)
    check_error(r, "Cannot retrive Backup Plans")
    d = r.plans
    del r
    if isinstance(d, list):
        d.sort(key=lambda p: (p["path"], p["id"]))
    _print(d, args.advanced)
    del d


def _print(plans, adv):
    if not adv:
        print(f'{"ID":11}{"Status":11}{"Last":15}{"Last Size":9} Path\n{"="*70}')
    for i in plans:
        x = i.get("id")
        if not nes(x) or len(x) < 10:
            continue
        v = i["state"]
        if adv:
            print(f'{i["id"]} - {i["path"]}\n{"="*60}')
            print(f'{"ID":<12}: {x}\n{"Path":<12}: {i["path"]}')
            print(f'{"Description":<12}: {i["description"]}\n{"UUID":<12}: {i["uuid"]}')
            if len(i["status"]) > 0:
                print(f'{"Status":<12}: {i["status"]}', end="")
                if v == "W":
                    print("(Paused)")
            elif v == "Q":
                print(f'{"Status":<12}: Queued')
            elif len(v) > 0:
                print(f'{"Status":<12}: {v}')
        else:
            if len(v) == 0:
                v = " "
            elif v != "Q" and i.get("error"):
                v = "F"
            print(f'{x:11}{v} {i["status"]:<9}', end="")
        del x, v
        if nes(i["last"]) and nes(i["size"]):
            try:
                x = datetime.fromisoformat(i["last"]).strftime("%m/%d/%y %H:%M")
            except ValueError:
                x = EMPTY
            v = i["size"]
        else:
            x, v = EMPTY, EMPTY
        if adv:
            if len(x) == 0 or len(v) == 0:
                print()
                continue
            print(f'{"Last Run":<12}: {x}{"(Failed)" if i.get("error") else EMPTY}')
            print(f'{"Last Size":<12}: {v}\n')
        else:
            print(f'{x:<15}{v:>9} {i["path"]}', end="")
            if nes(i["description"]) and len(i["description"]) <= 32:
                print(f' ({i["description"]})')
            else:
                print()
        del x, v

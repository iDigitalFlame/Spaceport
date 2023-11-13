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
        if "dir" in p and p["dir"][-1] != "/":
            p["dir"] = f'{p["dir"]}/'
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
    print(f'{"UUID":9}{"Status":18}{"Last Backup":25}{"Last Size":9} Path\n{"="*65}')
    if not isinstance(r.plans, list) or len(r.plans) == 0:
        return
    for p in r.plans:
        if len(p["uuid"]) < 8:
            continue
        t = EMPTY
        if isinstance(p["last"], str) and len(p["last"]) > 0:
            try:
                f = datetime.fromisoformat(p["last"])
                t = f.strftime("%m/%d/%y %H:%M:%S")
                del f
            except ValueError:
                pass
        v = EMPTY
        if p.get("error", False):
            v = "FAIL "
        t = f"{v}{t}"
        del v
        s = p["size"]
        if not nes(s):
            s = ""
        else:
            s = s[:-2]
        print(f'{p["uuid"][:8]:9}{p["status"]:<18}{t:<25}{s:>9} {p["path"]}')
        del t, s
    del r

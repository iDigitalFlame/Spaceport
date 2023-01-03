#!/usr/bin/false
# PowerCTL Module: Rotate
#  powerctl rotate, rotatectl, rotate
#
# PowerCTL command line user module to configure screen rotaion options.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2023 iDigitalFlame
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

from datetime import datetime
from lib.util import print_error
from lib.structs.message import send_message
from lib.constants import (
    EMPTY,
    HOOK_BACKUP,
    MESSAGE_TYPE_PRE,
    MESSAGE_TYPE_POST,
    MESSAGE_TYPE_STATUS,
    MESSAGE_TYPE_CONFIG,
    MESSAGE_TYPE_ACTION,
    BACKUP_STATUS_UPLOADING,
)


def config(arguments):
    q = dict()
    if arguments.start or arguments.dir or arguments.path:
        q["force"] = arguments.force
        q["type"] = MESSAGE_TYPE_ACTION
        if isinstance(arguments.dir, str) and len(arguments.dir) > 0:
            q["path"] = arguments.dir
        if isinstance(arguments.path, str) and len(arguments.path) > 0:
            q["path"] = arguments.path
    elif arguments.pause:
        q["type"] = MESSAGE_TYPE_PRE
    elif arguments.resume:
        q["type"] = MESSAGE_TYPE_POST
    elif arguments.stop:
        q["type"] = MESSAGE_TYPE_CONFIG
    elif arguments.clear:
        q["type"] = BACKUP_STATUS_UPLOADING
    else:
        return default(arguments)
    try:
        r = send_message(arguments.socket, HOOK_BACKUP, HOOK_BACKUP, 5, q)
    except OSError as err:
        return print_error("Error retriving Backup Plans!", err)
    del q
    if r.is_error():
        return print_error(f"Error retriving Backup Plans: {r.error}!")
    if not isinstance(r.result, str) or len(r.result) == 0:
        return
    print(r.result)
    del r


def default(arguments):
    try:
        r = send_message(
            arguments.socket, HOOK_BACKUP, HOOK_BACKUP, 5, {"type": MESSAGE_TYPE_STATUS}
        )
    except OSError as err:
        return print_error("Error retriving Backup Plans!", err)
    if r.is_error():
        return print_error(f"Error retriving Backup Plans: {r.error}!")
    print(f'{"UUID":9}{"Status":18}{"Last Backup":25} Path\n{"="*65}')
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
        elif p.get("stop", False):
            v = "STOP "
        t = f"{v}{t}"
        del v
        print(f'{p["uuid"][:8]:9}{p["status"]:<18}{t:<25} {p["path"]}')
        del t
    del r

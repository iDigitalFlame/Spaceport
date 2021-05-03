#!/usr/bin/false
# PowerCTL Module: Rotate
#  powerctl rotate, rotatectl, rotate
#
# PowerCTL command line user module to configure screen rotaion options.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2021 iDigitalFlame
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
    payload = dict()
    if arguments.start or arguments.dir or arguments.path:
        payload["force"] = arguments.force
        payload["type"] = MESSAGE_TYPE_ACTION
        if isinstance(arguments.dir, str) and len(arguments.dir) > 0:
            payload["path"] = arguments.dir
        if isinstance(arguments.path, str) and len(arguments.path) > 0:
            payload["path"] = arguments.path
    elif arguments.pause:
        payload["type"] = MESSAGE_TYPE_PRE
    elif arguments.resume:
        payload["type"] = MESSAGE_TYPE_POST
    elif arguments.stop:
        payload["type"] = MESSAGE_TYPE_CONFIG
    elif arguments.clear:
        payload["type"] = BACKUP_STATUS_UPLOADING
    else:
        return default(arguments)
    try:
        out = send_message(arguments.socket, HOOK_BACKUP, HOOK_BACKUP, None, payload)
    except OSError as err:
        return print_error(
            "Attempting to query Backup Plans raised an exception!", err, True
        )
    if "error" in out:
        return print_error(out["error"])
    if "result" not in out or len(out["result"]) == 0:
        return
    print(out["result"])
    del out


def default(arguments):
    try:
        query = send_message(
            arguments.socket,
            HOOK_BACKUP,
            HOOK_BACKUP,
            payload={"type": MESSAGE_TYPE_STATUS},
        )
    except OSError as err:
        return print_error(
            "Attempting to query Backup Plans raised an exception!", err, True
        )
    if "error" in query:
        return print_error(query["error"])
    print(f'{"UUID":9}{"Status":18}{"Last Backup":25} Path\n{"="*65}')
    if "plans" not in query or not isinstance(query["plans"], list):
        return
    for plan in query["plans"]:
        if len(plan["uuid"]) < 8:
            continue
        last = EMPTY
        if isinstance(plan["last"], str) and len(plan["last"]) > 0:
            try:
                val = datetime.fromisoformat(plan["last"])
                last = val.strftime("%m/%d/%y %H:%M:%S")
                del val
            except ValueError:
                pass
        pre = EMPTY
        if plan.get("error", False):
            pre = "FAIL "
        if plan.get("stop", False):
            pre = "STOP "
        last = f"{pre}{last}"
        del pre
        print(f'{plan["uuid"][:8]:9}{plan["status"]:<18}{last:<25} {plan["path"]}')
        del last
    del query

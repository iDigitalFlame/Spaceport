#!/usr/bin/false
# PowerCTL Module: Locker
#  powerctl locker, lockerctl, locker
#
# PowerCTL command line user module to configure system sleep and hibernate options.
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

from time import time
from lib.util import print_error, boolean
from lib.modules.locker import time_to_str
from lib.structs.message import send_message
from lib.constants import (
    HOOK_LOCKER,
    LOCKER_TYPE_LID,
    LOCKER_TYPE_KEY,
    LOCKER_TYPE_LOCK,
    LOCKER_TYPE_BLANK,
    LOCKER_TYPE_NAMES,
    MESSAGE_TYPE_STATUS,
    LOCKER_TYPE_SUSPEND,
    MESSAGE_TYPE_ACTION,
    LOCKER_TYPE_HIBERNATE,
)


def config(arguments):
    e = list()
    get_locker(e, LOCKER_TYPE_LID, arguments.lid, arguments.lid_force)
    get_locker(e, LOCKER_TYPE_KEY, arguments.key, arguments.key_force)
    get_locker(e, LOCKER_TYPE_BLANK, arguments.blank, arguments.blank_force)
    get_locker(e, LOCKER_TYPE_LOCK, arguments.lockscreen, arguments.lockscreen_force)
    get_locker(e, LOCKER_TYPE_SUSPEND, arguments.suspend, arguments.suspend_force)
    get_locker(e, LOCKER_TYPE_HIBERNATE, arguments.hibernate, arguments.hibernate_force)
    if len(e) == 0:
        return
    try:
        send_message(
            arguments.socket,
            HOOK_LOCKER,
            payload={"type": MESSAGE_TYPE_ACTION, "list": e},
        )
    except OSError as err:
        print_error("Error updating Lockers!", err)
    del e


def default(arguments):
    try:
        r = send_message(
            arguments.socket,
            HOOK_LOCKER,
            (HOOK_LOCKER, "lockers"),
            5,
            {"type": MESSAGE_TYPE_STATUS},
        )
    except OSError as err:
        return print_error("Error retriving Lockers!", err)
    if r.is_error():
        print_error(f"Error retriving Lockers: {r.error}!")
    if not isinstance(r.lockers, dict) or len(r.lockers) == 0:
        return print("No Lockers are enabled.")
    print(f'{"Locker":15}{"Expires":8}\n{"="*32}')
    t = time()
    for n, s in r.lockers.items():
        print(f"{LOCKER_TYPE_NAMES.get(n, n):15}{time_to_str(t, s):<8}")
    del t
    del r


def _parse_time(value):
    try:
        v = int(value)
        return v if v >= 0 else None
    except ValueError:
        pass
    return None if boolean(value) else 0


def get_locker(list, locker, arg, force):
    if arg is None and force is None:
        return
    try:
        e = _parse_time(force if force is not None else arg)
    except ValueError as err:
        return print_error(f"{LOCKER_TYPE_NAMES.get(locker, locker)}: {err}")
    list.append({"name": locker, "time": e, "force": force is not None})
    del e

#!/usr/bin/false
# PowerCTL Module: Locker
#  powerctl locker, lockerctl, locker
#
# PowerCTL command line user module to configure system sleep and hibernate options.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2022 iDigitalFlame
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
    lockers = list()
    _parse_locker(lockers, LOCKER_TYPE_LID, arguments.lid, arguments.lid_force)
    _parse_locker(lockers, LOCKER_TYPE_KEY, arguments.key, arguments.key_force)
    _parse_locker(lockers, LOCKER_TYPE_BLANK, arguments.blank, arguments.blank_force)
    _parse_locker(
        lockers, LOCKER_TYPE_LOCK, arguments.lockscreen, arguments.lockscreen_force
    )
    _parse_locker(
        lockers, LOCKER_TYPE_SUSPEND, arguments.suspend, arguments.suspend_force
    )
    _parse_locker(
        lockers, LOCKER_TYPE_HIBERNATE, arguments.hibernate, arguments.hibernate_force
    )
    if len(lockers) == 0:
        return
    try:
        send_message(
            arguments.socket,
            HOOK_LOCKER,
            payload={"type": MESSAGE_TYPE_ACTION, "list": lockers},
        )
    except OSError as err:
        print_error("Attempting to update the Lockers raised an exception!", err)
    del lockers


def default(arguments):
    try:
        query = send_message(
            arguments.socket,
            HOOK_LOCKER,
            (HOOK_LOCKER, "lockers"),
            payload={"type": MESSAGE_TYPE_STATUS},
        )
    except OSError as err:
        return print_error("Attempting to query Lockers raised an exception!", err)
    if "error" in query:
        print_error(
            f'Attempting to query Lockers returned an exception: {query["error"]}!',
            None,
            True,
        )
    print(f'{"Locker":15}{"Expires":8}\n{"="*32}')
    if not isinstance(query["lockers"], dict) or len(query["lockers"]) == 0:
        return
    now = time()
    for name, seconds in query["lockers"].items():
        if name not in LOCKER_TYPE_NAMES:
            print(f"{name:15}{time_to_str(now, seconds):<8}")
            continue
        print(f"{LOCKER_TYPE_NAMES[name]:15}{time_to_str(now, seconds):<8}")
    del now
    del query


def _parse_time(value):
    try:
        number = int(value)
        return number if number >= 0 else None
    except ValueError:
        pass
    return None if boolean(value) else 0


def _parse_locker(list, locker, arg, force):
    if arg is None and force is None:
        return
    try:
        expires = _parse_time(force if force is not None else arg)
    except ValueError as err:
        return print_error(f"{LOCKER_TYPE_NAMES[locker]}: {err}")
    list.append({"name": locker, "time": expires, "force": force is not None})
    del expires

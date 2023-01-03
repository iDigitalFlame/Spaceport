#!/usr/bin/false
# PowerCTL Module: Lock
#  powerctl lock, lockctl, lock
#
# PowerCTL command line user module to lock the screen session.
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

from lib.util import print_error
from lib.powerctl.locker import get_locker
from lib.structs.message import send_message
from lib.constants import (
    HOOK_LOCK,
    HOOK_LOCKER,
    LOCKER_TRIGGER_LOCK,
    MESSAGE_TYPE_ACTION,
    LOCKER_TYPE_SUSPEND,
    LOCKER_TYPE_HIBERNATE,
)


def default(arguments):
    e = list()
    if arguments.timeout:
        arguments.suspend = arguments.timeout
    get_locker(e, LOCKER_TYPE_SUSPEND, arguments.suspend, arguments.suspend_force)
    get_locker(e, LOCKER_TYPE_HIBERNATE, arguments.hibernate, arguments.hibernate_force)
    if len(e) > 0:
        try:
            send_message(
                arguments.socket,
                HOOK_LOCKER,
                payload={"type": MESSAGE_TYPE_ACTION, "list": e},
            )
        except OSError as err:
            return print_error("Error updating Lockers!", err)
    del e
    try:
        send_message(
            arguments.socket,
            HOOK_LOCK,
            payload={"force": arguments.force, "trigger": LOCKER_TRIGGER_LOCK},
        )
    except OSError as err:
        print_error("Error triggering the Lockscreen!", err)

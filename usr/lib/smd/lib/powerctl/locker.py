#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# PowerCTL Module: Locker
#  powerctl locker, lockerctl, locker
#
# PowerCTL command line user module to configure system sleep and hibernate options.

from time import time
from sys import stderr
from lib.util import print_error, boolean
from lib.modules.locker import time_to_str
from lib.structs.message import send_message
from lib.constants import HOOK_POWER, LOCKER_NAMES, LOCKER_CONTROL_QUERY

ARGS = [
    (
        "-b",
        {
            "required": False,
            "action": "store",
            "dest": "blank",
            "type": str,
            "metavar": "seconds",
            "help": "Set the screen blank locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
    (
        "-l",
        {
            "required": False,
            "action": "store",
            "dest": "lock_screen",
            "type": str,
            "metavar": "seconds",
            "help": "Set the lock screen locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
    (
        "-s",
        {
            "required": False,
            "action": "store",
            "dest": "hibernate",
            "type": str,
            "metavar": "seconds",
            "help": "Set the hibernate locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
    (
        "-d",
        {
            "required": False,
            "action": "store",
            "dest": "lid",
            "type": str,
            "metavar": "seconds",
            "help": "Set the lid locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
    (
        "-kb",
        {
            "required": False,
            "action": "store",
            "dest": "blank_force",
            "type": str,
            "metavar": "seconds",
            "help": "Force the screen blank locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
    (
        "-kl",
        {
            "required": False,
            "action": "store",
            "dest": "lock_screen_force",
            "type": str,
            "metavar": "seconds",
            "help": "Force the lock screen locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
    (
        "-ks",
        {
            "required": False,
            "action": "store",
            "dest": "hibernate_force",
            "type": str,
            "metavar": "seconds",
            "help": "Force the hibernate locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
    (
        "-kd",
        {
            "required": False,
            "action": "store",
            "dest": "lid_force",
            "type": str,
            "metavar": "seconds",
            "help": "Force the lid locker time (Seconds, True - Until Reboot, False - Disable).",
        },
        "config",
    ),
]
DESCRIPTION = "System Locker Management Module"


def _time(value):
    try:
        number = int(value)
    except ValueError:
        try:
            return None if boolean(value) else 0
        except ValueError:
            pass
    else:
        return number if number >= 0 else -1
    return -1


def config(arguments):
    message = {"type": "locker", "action": "set", "list": []}
    try:
        if arguments.blank or arguments.blank_force:
            blank = _time(
                arguments.blank_force if arguments.blank_force else arguments.blank
            )
            if blank == -1:
                raise ValueError(
                    "Blank time must be True, False or an integer greater than zero!"
                )
            else:
                message["list"].append(
                    {
                        "name": "blank",
                        "expire": blank,
                        "force": arguments.blank_force is not None,
                    }
                )
            del blank
        if arguments.lock_screen or arguments.lock_screen_force:
            lock = _time(
                arguments.lock_screen_force
                if arguments.lock_screen_force
                else arguments.lock_screen
            )
            if lock == -1:
                raise ValueError(
                    "Lock screen time must be True, False or an integer greater than zero!"
                )
            else:
                message["list"].append(
                    {
                        "name": "lock-screen",
                        "expire": lock,
                        "force": arguments.lock_screen_force is not None,
                    }
                )
            del lock
        if arguments.hibernate or arguments.hibernate_force:
            hibernate = _time(
                arguments.hibernate_force
                if arguments.hibernate_force
                else arguments.hibernate
            )
            if hibernate == -1:
                raise ValueError(
                    "Hibernate time must be True, False or an integer greater than zero!"
                )
            else:
                message["list"].append(
                    {
                        "name": "hibernate",
                        "expire": hibernate,
                        "force": arguments.hibernate_force is not None,
                    }
                )
            del hibernate
        if arguments.lid or arguments.lid_force:
            lid = _time(arguments.lid_force if arguments.lid_force else arguments.lid)
            if lid == -1:
                raise ValueError(
                    "Lid time must be True, False or an integer greater than zero!"
                )
            else:
                message["list"].append(
                    {
                        "name": "lid",
                        "expire": lid,
                        "force": arguments.lid_force is not None,
                    }
                )
            del lid
    except ValueError as err:
        print(str(err), file=stderr)
    else:
        try:
            send_message(arguments.socket, HOOK_POWER, None, None, message)
        except OSError as err:
            print_error(
                "Attempting to update the Lockers raised an exception!", err, True
            )
    finally:
        del message


def default(arguments):
    try:
        query = send_message(
            arguments.socket,
            HOOK_POWER,
            (HOOK_POWER, "lockers"),
            None,
            LOCKER_CONTROL_QUERY,
        )
    except OSError as err:
        print_error("Attempting to query Lockers raised an exception!", err, True)
    else:
        print("%-15s%-8s\n%s" % ("Locker", "Expires", "=" * 32))
        if isinstance(query["lockers"], dict) and len(query["lockers"]) > 0:
            now_time = time()
            for name, lock_time in query["lockers"].items():
                if name in LOCKER_NAMES:
                    print(
                        "%-15s%-8s"
                        % (LOCKER_NAMES[name], time_to_str(now_time, lock_time))
                    )
                else:
                    print("%-15s%-8s" % (name, time_to_str(now_time, lock_time)))
            del now_time
        del query

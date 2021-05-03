#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# Module: Brightness (System)
#
# Sets and changes the System Brightness.

from lib.util import read, write
from lib.constants import HOOK_POWER, BRIGHTNESS_FILE_MAX, BRIGHTNESS_FILE

HOOKS = None
HOOKS_SERVER = {HOOK_POWER: "brightness"}


def brightness(server, message):
    if message.get("type") == "brightness" and message.get("level") is not None:
        try:
            level = int(message["level"])
            level_max = int(read(BRIGHTNESS_FILE_MAX, ignore_errors=False))
        except (OSError, ValueError) as err:
            server.error(
                "Error changing brightness, received a non-integer value!", err=err
            )
        else:
            if level < 0:
                server.error(
                    "Client attempted to change the brightness to less than zero!"
                )
            elif level > level_max:
                server.error(
                    "Client attempted to change the brightness highter than the max level!"
                )
            else:
                server.debug('Setting brightness level to "%d".' % level)
                try:
                    write(BRIGHTNESS_FILE, str(level), ignore_errors=False)
                except OSError as err:
                    server.error(
                        "An exception was raised when attempting to set brightness level!",
                        err=err,
                    )
            del level
            del level_max

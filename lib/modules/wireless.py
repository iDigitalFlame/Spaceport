#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# Module: Wireless (System)
#
# Sets and changes the System Wireless Radio settings.
# Updated 10/2018

from lib.util import run
from lib.constants import WIRELESS_COMMANDS, HOOK_STARTUP, HOOK_POWER, HOOK_HIBERNATE

HOOKS = None
HOOKS_SERVER = {
    HOOK_POWER: "wireless_hook",
    HOOK_STARTUP: "wireless_startup",
    HOOK_HIBERNATE: "wireless_hibernate",
}


def wireless_startup(server):
    _wireless_set(server, "wireless", server.config("wireless_boot", True))
    _wireless_set(server, "bluetooth", server.config("bluetooth_boot", True))


def wireless_hook(server, message):
    if message.get("type") == "bluetooth" or message.get("type") == "wireless":
        if message.get("action") == "boot":
            server.set("%s_boot" % message["type"], bool(message.get("boot", True)))
        elif message.get("action") == "set":
            _wireless_set(server, message["type"], message.get("set", True))


def wireless_hibernate(server, message):
    if message["state"] == "post" and server.config("bluetooth_enabled", False):
        _wireless_set(server, "bluetooth", True)


def _wireless_set(server, wireless_type, enable):
    wireless_commands = None
    wireless_name = "%s_%s" % (wireless_type.lower(), "enable" if enable else "disable")
    if wireless_name in WIRELESS_COMMANDS:
        wireless_commands = WIRELESS_COMMANDS[wireless_name]
    del wireless_name
    if isinstance(wireless_commands, list):
        server.debug(
            '%s "%s"..' % ("Enabling" if enable else "Disabling", wireless_type)
        )
        for command in wireless_commands:
            try:
                run(command.split(" "), ignore_errors=False)
            except OSError as err:
                server.error(
                    'Attempting to run the command "%s" raised an exception!' % command,
                    err=err,
                )
        server.set("%s_enabled" % wireless_type, enable)
        del wireless_commands


# EOF

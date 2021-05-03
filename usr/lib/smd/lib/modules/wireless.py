#!/usr/bin/false
# Module: Wireless (System)
#
# Sets and changes the System Wireless Radio settings.
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

from lib.util import run, boolean
from lib.constants import (
    RADIO_EXEC,
    HOOK_RADIO,
    HOOK_STARTUP,
    HOOK_HIBERNATE,
    MESSAGE_TYPE_POST,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_CONFIG,
)

HOOKS_SERVER = {
    HOOK_RADIO: "config",
    HOOK_STARTUP: "startup",
    HOOK_HIBERNATE: "hibernate",
}


def startup(server):
    _radio_set(server, "wireless", server.get_config("wireless.boot", True, False))
    _radio_set(server, "bluetooth", server.get_config("bluetooth.boot", True, False))


def config(server, message):
    if message.radio is None:
        return
    if message.type == MESSAGE_TYPE_CONFIG:
        server.set_config(
            f"{message.radio}.boot", boolean(message.get("boot", True)), True
        )
    elif message.type == MESSAGE_TYPE_ACTION:
        _radio_set(server, message.radio, boolean(message.get("enabled", True)))


def hibernate(server, message):
    if message.state != MESSAGE_TYPE_POST:
        return
    _radio_set(server, "wireless", server.get_config("wireless.enabled", True, False))
    _radio_set(
        server, "bluetooth", server.get_config("bluetooth.enabled", False, False)
    )


def _radio_set(server, radio, enable):
    commands = RADIO_EXEC.get(f'{radio.lower()}_{"enable" if enable else "disable"}')
    if isinstance(commands, list):
        server.debug(f'{"Enabling" if enable else "Disabling"} "{radio}"..')
        for command in commands:
            try:
                run(command, ignore_errors=False)
            except OSError as err:
                server.error(
                    f'Attempting to run the command "{command}" raised an exception!',
                    err=err,
                )
        server.set_config(f"{radio}.enabled", enable, True)
    del commands

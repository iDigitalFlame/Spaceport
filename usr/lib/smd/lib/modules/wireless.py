#!/usr/bin/false
# Module: Wireless (System)
#
# Sets and changes the System Wireless Radio settings.
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

from lib.util import run, boolean
from lib.structs.message import Message
from lib.constants import (
    RADIO_EXEC,
    HOOK_RADIO,
    HOOK_STARTUP,
    HOOK_HIBERNATE,
    HOOK_NOTIFICATION,
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
    _radio_set(
        server, "wireless", server.get_config("wireless.boot", True, False), False
    )
    _radio_set(
        server, "bluetooth", server.get_config("bluetooth.boot", True, False), False
    )


def config(server, message):
    if message.radio is None:
        return
    if message.type == MESSAGE_TYPE_CONFIG:
        server.set_config(
            f"{message.radio}.boot", boolean(message.get("boot", True)), True
        )
    elif message.type == MESSAGE_TYPE_ACTION:
        _radio_set(server, message.radio, boolean(message.get("enabled", True)), True)


def hibernate(server, message):
    if message.state != MESSAGE_TYPE_POST:
        return
    _radio_set(
        server, "wireless", server.get_config("wireless.enabled", True, False), False
    )
    _radio_set(
        server, "bluetooth", server.get_config("bluetooth.enabled", False, False), False
    )


def _radio_set(server, radio, enable, notify):
    c = RADIO_EXEC.get(f'{radio.lower()}_{"enable" if enable else "disable"}')
    if not isinstance(c, list):
        return
    s = server.get_config(f"{radio}.enabled", not enable)
    if s == enable:
        del s
        return server.debug(
            f'Not re-{"enabling" if enable else "disabling"} already '
            f'{"enabled" if enable else "disabed"} radio {radio}.'
        )
    del s
    server.debug(f'{"Enabling" if enable else "Disabling"} "{radio}"..')
    for x in c:
        try:
            run(x)
        except OSError as err:
            server.error(f'Error running the command "{x}"!', err=err)
    del c
    server.set_config(f"{radio}.enabled", enable, True)
    if not notify:
        return
    server.send(
        None,
        Message(
            header=HOOK_NOTIFICATION,
            payload={
                "title": "Radio Status Change",
                "body": f"{radio.title()} was {'Enabled' if enable else 'Disabled'}",
                "icon": "configuration-section",
            },
        ),
    )

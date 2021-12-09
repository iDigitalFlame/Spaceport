#!/usr/bin/false
# Module: Forwarder (System)
#
# Forwards server specific calls to the clients.
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

from lib.constants import (
    HOOK_OK,
    HOOK_ERROR,
    HOOK_POWER,
    HOOK_RELOAD,
    HOOK_BACKGROUND,
    HOOK_NOTIFICATION,
)

HOOKS_SERVER = {
    HOOK_OK: "forward",
    HOOK_ERROR: "error",
    HOOK_POWER: "forward",
    HOOK_RELOAD: "forward",
    HOOK_BACKGROUND: "forward",
    HOOK_NOTIFICATION: "forward",
}


def forward(_, message):
    return message.set_multicast()


def error(server, message):
    if "error" not in message:
        return
    server.error(
        f'An error was detected on hook 0x{message.get("hook", HOOK_ERROR):02X}: '
        f'{message["error"]}\n{message.get("trace", "...")}'
    )

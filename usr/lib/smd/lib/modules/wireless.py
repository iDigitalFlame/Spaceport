#!/usr/bin/false
################################
### iDigitalFlame  2016-2024 ###
#                              #
#            -/`               #
#            -yy-   :/`        #
#         ./-shho`:so`         #
#    .:- /syhhhh//hhs` `-`     #
#   :ys-:shhhhhhshhhh.:o- `    #
#   /yhsoshhhhhhhhhhhyho`:/.   #
#   `:yhyshhhhhhhhhhhhhh+hd:   #
#     :yssyhhhhhyhhhhhhhhdd:   #
#    .:.oyshhhyyyhhhhhhddd:    #
#    :o+hhhhhyssyhhdddmmd-     #
#     .+yhhhhyssshdmmddo.      #
#       `///yyysshd++`         #
#                              #
########## SPACEPORT ###########
### Spaceport + SMD
#
# Copyright (C) 2016 - 2024 iDigitalFlame
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

# Module: System/Wireless (System)
#   Sets and changes the system Wireless Radio settings. Allows radio settings to
#   be controlled from userspace. Also starts services related to the radio if
#   enabled (like with Bluetooth).

from lib.util import boolean
from lib.util.exec import nulexec
from lib.constants.config import RADIO_EXEC, RADIO_TYPES
from lib.constants import (
    MSG_PRE,
    MSG_POST,
    MSG_ACTION,
    MSG_CONFIG,
    HOOK_RADIO,
    HOOK_STARTUP,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
)


HOOKS_SERVER = {
    HOOK_RADIO: "config",
    HOOK_STARTUP: "startup",
    HOOK_SHUTDOWN: "shutdown",
    HOOK_HIBERNATE: "hibernate",
}


def startup(server):
    _radio(server, "wireless", server.get("radio.wireless.boot", True), True)
    _radio(server, "bluetooth", server.get("radio.bluetooth.boot", True), True)


def shutdown(server):
    if not server.get("radio.wireless.boot", False):
        _radio(server, "wireless", False, True)
    if not server.get("radio.bluetooth.boot", False):
        _radio(server, "bluetooth", False, True)


def config(server, message):
    if message.radio not in RADIO_TYPES:
        return
    if message.type == MSG_CONFIG:
        server.set(f"radio.{message.radio}.boot", boolean(message.get("boot", True)))
        return server.save()
    if message.type != MSG_ACTION:
        return
    r = _radio(
        server,
        message.radio,
        boolean(message.get("enabled", True)),
        message.force,
        True,
        True,
    )
    if not r or message.force:
        return
    return message.multicast()


def hibernate(server, message):
    # NOTE(dij): Disable the wireless devices before Hibernating.
    if message.state == MSG_PRE:
        _radio(server, "wireless", False, True)
        _radio(server, "bluetooth", False, True)
    elif message.state == MSG_POST:
        _radio(server, "wireless", server.get("radio.wireless.state", True), True)
        _radio(server, "bluetooth", server.get("radio.bluetooth.state", True), True)


def _radio_set(server, name, enable, state, save):
    c = RADIO_EXEC.get(f"{name}_{state}")
    if not isinstance(c, list) or len(c) == 0:
        return server.warning(
            f'[m/wireless]: Cannot {state} radio "{name}", no commands found!'
        )
    server.debug(f'[m/wireless]: {state.title()[0:-1]}ing radio "{name}".')
    for x in c:
        try:
            nulexec(x, wait=True)
        except OSError as err:
            server.error(f'[m/wireless]: Cannot execute the radio command "{x}"!', err)
    del c
    server.set(f"radio.{name}.state", enable)
    if not save:
        return
    server.save()


def _radio(server, radio, enable, force, notify=False, save=False):
    v = "enable" if enable else "disable"
    if not force:
        if server.get(f"radio.{radio}.state", not enable) == enable:
            return server.debug(
                f'[m/wireless]: Not re-{v[0:-1]}ing already {v}d radio "{radio}".'
            )
    _radio_set(server, radio, enable, v, save)
    if notify:
        server.notify(
            "Radio Status Change",
            f"{radio.title()} was {v.title()}d",
            "configuration-section",
        )
    del v
    return True

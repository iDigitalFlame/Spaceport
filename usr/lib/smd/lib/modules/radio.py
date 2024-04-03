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

# Module: System/Radio (System)
#   Sets and changes the system Radio settings. Allows radio settings to be
#   controlled from userspace. Also starts services related to the radio if
#   enabled (like with Bluetooth).
#   Changing state of a Radio will also send a user trigger response to enable
#   user-based profile triggers (used in session.py) for when a Radio comes
#   online/offline.

from lib.util.exec import nulexec
from lib.util import boolean, a2z, nes
from lib.constants.config import RADIO_EXEC, RADIO_NAMES
from lib.constants import (
    MSG_POST,
    MSG_ACTION,
    MSG_CONFIG,
    HOOK_RADIO,
    HOOK_STARTUP,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
)


HOOKS_SERVER = {
    HOOK_RADIO: "Radio.hook",
    HOOK_STARTUP: "Radio.startup",
    HOOK_SHUTDOWN: "Radio.hook",
    HOOK_HIBERNATE: "Radio.hook",
}


class Radio(object):
    __slots__ = ("_states",)

    def __init__(self):
        self._states = dict()

    def startup(self, server):
        server.debug("[m/radio]: Running Radio startup..")
        for k, v in self._states.items():
            self._set(server, k, v, True, update=False)
        server.debug("[m/radio]: Radio startup completed!")

    def setup_server(self, server):
        for i in RADIO_NAMES:
            if not a2z(i):
                server.warning(f'[m/radio]: Skipping invalid Radio name "{i}"!')
                continue
            self._states[i] = server.get(f"radio.{i}.boot", True, set_non_exist=True)
        server.debug(f"[m/radio]: Radio states dump: {self._states}")

    def hook(self, server, message):
        if message.header() == HOOK_SHUTDOWN:
            for i in RADIO_NAMES:
                if not a2z(i) or server.get(f"radio.{i}.boot", True):
                    continue
                self._set(server, i, False, True)
            return
        elif message.header() == HOOK_HIBERNATE:
            a = message.type == MSG_POST
            for k, v in self._states.items():
                if not v:
                    continue
                self._set(server, k, a, True, update=False)
            del a
            return
        if not a2z(message.radio):
            return server.warning("[m/radio]: Ignoring invalid Radio name!")
        if message.radio not in self._states:
            return server.warning(
                f'[m/radio]: Ignoring unknown Radio name "{message.radio}"!'
            )
        if message.type == MSG_CONFIG:
            server.set(
                f"radio.{message.radio}.boot", boolean(message.get("boot", True))
            )
            return server.save()
        if message.type != MSG_ACTION:
            return
        r = self._set(
            server,
            message.radio,
            boolean(message.get("enabled", True)),
            message.force,
            True,
        )
        if not r or message.force:
            return
        return message.multicast()

    def _set(self, server, name, state, force, notify=False, update=True):
        v = "enable" if state else "disable"
        if not force and self._states[name] == state:
            return server.debug(f"[m/radio/{name}]: Not re-{v[0:-1]}ing.")
        e = RADIO_EXEC.get(f"{name}_{v}")
        if nes(e):
            e = [e]
        elif not isinstance(e, list) or len(e) == 0:
            return server.warning(f"[m/radio/{name}]: Cannot {v}, no commands found!")
        t = v.title()
        server.info(f"[m/radio/{name}]: {t[0:-1]}ing..")
        for x in e:
            try:
                nulexec(x, wait=True)
            except OSError as err:
                server.error(
                    f'[m/radio/{name}]: Cannot execute {v} command "{x}"!', err
                )
        del v, e
        if not update:
            return True
        server.debug(f'[m/radio/{name}]: Setting internal state to "{str(state)}".')
        self._states[name] = state
        if notify:
            server.notify(
                "Radio Status Change",
                f"{name.title()} was {t}d",
                "configuration-section",
            )
        del t
        return True

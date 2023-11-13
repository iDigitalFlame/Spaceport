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

# Module: User/Display
#   Maintains the Display state and will inform the user Session if the Display
#   configuration has changed.

from lib import Message
from lib.util import boolean
from lib.util.file import read
from lib.sway import displays, swaymsg
from lib.constants.config import DISPLAY_BUILTIN, DISPLAY_PATH_LID
from lib.constants import HOOK_DISPLAY, HOOK_MONITOR, HOOK_POWER, HOOK_RELOAD

HOOKS = {
    HOOK_POWER: "Display.display",
    HOOK_RELOAD: "Display.setup",
    HOOK_MONITOR: "Display.display",
}


class Display(object):
    __slots__ = ("_auto", "_last")

    def __init__(self):
        self._auto = False
        self._last = dict()

    def setup(self, server):
        self._auto = boolean(server.get("display.auto", True, True))
        self._check(server)

    def _read(self, server):
        server.debug("[m/display]: Checking Display state..")
        try:
            d = displays()
        except OSError as err:
            return server.error("[m/display]: Cannot retrieve Display list!", err)
        o, s, u, n = self._last.copy(), False, False, list()
        for i in d:
            server.debug(
                f'[m/display]: Found Display "{i.name}" in the "{"enabled" if i.active else "disabled"}" state.'
            )
            # NOTE(dij): Check to verify if a single Display is enabled.
            if not s and i.active:
                s = True
            # NOTE(dij): Check if our Display configuration has changed and we
            #            need to send out an update.
            if not u and (i.name not in o or o[i.name] != i.active):
                u = True
            # NOTE(dij): Found a new Display that's not enabled.
            if i.name not in o:  # or not i.active:
                n.append(i.name)
            self._last[i.name] = i.active
        del o
        if self._auto:
            return (u, s, n)
        del n
        return (u, s, None)

    def _check(self, server):
        u, s, n = self._read(server)
        if not s or len(self._last) <= 1:
            server.debug(
                f'[m/display]: Enabling built-in Display "{DISPLAY_BUILTIN}" as no displays are enabled!'
            )
            try:
                swaymsg(0, f"output {DISPLAY_BUILTIN} enable")
            except OSError as err:
                server.error(
                    f'[m/display]: Cannot enable the built-in Display "{DISPLAY_BUILTIN}"!',
                    err,
                )
        else:
            server.debug(
                "[m/display]: Minimum of one Display is connected and enabled."
            )
        if not self._auto:
            return u
        # NOTE(dij): Single read the LID path here. This is ok since it's a single
        #            read that's not affected by the other calls.
        v = read(DISPLAY_PATH_LID, True, False)
        c = v is not None and len(v) >= 12 and v[12] == 0x63
        if c and len(self._last) > 1:
            server.debug(
                f'[m/display]: Disabling built-in Display "{DISPLAY_BUILTIN}" as the Lid is closed!'
            )
            try:
                swaymsg(0, f"output {DISPLAY_BUILTIN} disable")
            except OSError as err:
                server.error(
                    f'[m/display]: Cannot disable the built-in Display "{DISPLAY_BUILTIN}"!',
                    err,
                )
            if DISPLAY_BUILTIN in n:
                # NOTE(dij): Detect if the internal Display was disabled and remove
                #            it from the auto-list if it's been re-added to prevent
                #            an "off-then-on" situation.
                n.remove(DISPLAY_BUILTIN)
        del c, v
        for i in n:
            server.debug(f'[m/display]: Enabling Display "{i}"..')
            try:
                swaymsg(0, f"output {i} enable")
            except OSError as err:
                server.error(f'[m/display]: Cannot enable the Display "{i}"!', err)
        del n
        return u

    def display(self, server):
        if not self._check(server):
            return
        server.debug("[m/display]: Detected a change in monitors!")
        server.forward(Message(HOOK_DISPLAY))

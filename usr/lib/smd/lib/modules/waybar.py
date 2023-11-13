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

# Module: User/Waybar
#   Manages the Waybar process, responds to lock/power events and restarts
#   it if needed.

from lib.util import nes
from signal import SIGCONT, SIGSTOP
from lib.util.exec import stop, nulexec
from lib.constants.defaults import DEFAULT_WAYBAR_NAME
from lib.constants import (
    MSG_PRE,
    HOOK_LOCK,
    HOOK_DAEMON,
    HOOK_RELOAD,
    HOOK_DISPLAY,
    HOOK_SHUTDOWN,
)

HOOKS = {
    HOOK_LOCK: "Waybar.hook",
    HOOK_DAEMON: "Waybar.thread",
    HOOK_RELOAD: "Waybar.hook",
    HOOK_DISPLAY: "Waybar.hook",
    HOOK_SHUTDOWN: "Waybar.hook",
}


class Waybar(object):
    __slots__ = ("_bar", "_proc", "_errors", "_reload")

    def __init__(self):
        self._bar = None
        self._proc = None
        self._errors = 5
        self._reload = False

    def setup(self, server):
        self._bar = server.get("waybar", DEFAULT_WAYBAR_NAME, True)
        if not nes(self._bar):
            server.warning(
                '[m/waybar]: Config value "waybar" is invalid (must be a non-empty string), '
                "using the default value!"
            )
            self._bar = DEFAULT_WAYBAR_NAME

    def _exec(self, server):
        if self._errors <= 0:
            return
        if self._proc is not None and self._proc.returncode != 0:
            self._errors -= 1
            if self._errors <= 0:
                return server.error(
                    '[m/waybar]: Max number of Waybar errors reached, use the "reload" command to restart Waybar!'
                )
            server.warning(
                f"[m/waybar]: Waybar returned an error, it will be restarted {self._errors} more "
                f"times before a reload is required!"
            )
        self._reload = False
        stop(self._proc)
        server.debug(f'[m/waybar]: Starting Waybar with bar "{self._bar}"..')
        try:
            self._proc = nulexec(
                ["/usr/bin/waybar", "--bar", self._bar, "--log-level", "off"]
            )
        except OSError as err:
            server.error("[m/waybar]: Cannot start Waybar!", err)
            self._errors -= 1

    def thread(self, server):
        if self._reload:
            stop(self._proc)
            self._proc = None
        if self._errors <= 0 or (self._proc is not None and self._proc.poll() is None):
            return
        self._exec(server)

    def hook(self, server, message):
        if message.header() == HOOK_SHUTDOWN:
            # NOTE(dij): We're stopping the process here to prevent it being
            #            leaked if the thread call processes the message late.
            self._errors, self._reload = 0, False
            stop(self._proc)
            self._proc = None
        elif message.header() == HOOK_RELOAD:
            self._errors, self._reload = 5, True
            self.setup(server)
        elif message.header() == HOOK_DISPLAY:
            self._reload = True
        elif message.header() == HOOK_LOCK and message.type is not None:
            self._freeze(server, message.type == MSG_PRE)

    def _freeze(self, server, freeze):
        if self._proc is None or self._proc.poll() is not None:
            return
        if freeze:
            try:
                self._proc.send_signal(SIGSTOP)
            except OSError as err:
                return server.error("[m/waybar]: Cannot freeze Waybar!", err)
            return server.debug("[m/waybar]: Freezing Waybar due to Lockscreen.")
        try:
            self._proc.send_signal(SIGCONT)
        except OSError as err:
            return server.error("[m/waybar]: Cannot un-freeze Waybar!", err)
        server.debug("[m/waybar]: Unfreezing Waybar due to Lockscreen removal.")

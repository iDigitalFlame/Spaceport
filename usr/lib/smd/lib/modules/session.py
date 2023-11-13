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

# Module: User/Session
#   Manages the User's startup and session processes. Handles "Trigger" actions
#   for user-defined events that can execute ba program(s) in response.

from os import kill
from lib.sway import windows
from lib.util import boolean
from lib.util.file import expand
from signal import SIGCONT, SIGSTOP
from lib.constants.config import RADIO_TYPES
from lib.util.exec import stop, nulexec, split
from lib.constants import (
    MSG_PRE,
    MSG_POST,
    HOOK_LOCK,
    HOOK_POWER,
    HOOK_RADIO,
    MSG_ACTION,
    HOOK_RELOAD,
    HOOK_SUSPEND,
    HOOK_DISPLAY,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
)
from lib.constants.defaults import (
    DEFAULT_SESSION_IGNORE,
    DEFAULT_SESSION_FREEZE,
    DEFAULT_SESSION_STARTUPS,
)

HOOKS = {
    HOOK_LOCK: "Session.lock",
    HOOK_POWER: "Session.trigger",
    HOOK_RADIO: "Session.trigger",
    HOOK_RELOAD: "Session.reload",
    HOOK_DISPLAY: "Session.trigger",
    HOOK_SUSPEND: "Session.trigger",
    HOOK_SHUTDOWN: "Session.reload",
    HOOK_HIBERNATE: "Session.trigger",
}


def _trigger(server, name):
    t = server.get(f"trigger.{name}", list(), True)
    if t is None or len(t) == 0:
        return
    c = split(t)
    del t
    if c is None:
        return server.warning(
            f'[m/session]: Trigger config value "trigger.{name}" is not a list or string!'
        )
    if len(c) == 0:
        return None
    return c


def _can_freeze(ignore, window):
    if window.app.startswith("i3lock") or window.app.startswith("swaylock"):
        return False
    if not isinstance(ignore, list) or len(ignore) == 0:
        return True
    for i in ignore:
        if i in window.app:
            return False
    return True


class Session(object):
    __slots__ = ("_ignore", "_last_ac", "_startup", "_profiles", "_can_freeze")

    def __init__(self):
        self._ignore = list()
        self._last_ac = None
        self._startup = list()
        self._profiles = dict()
        self._can_freeze = False

    def setup(self, server):
        self._can_freeze = boolean(
            server.get("session.freeze.enabled", DEFAULT_SESSION_FREEZE, True)
        )
        if self._can_freeze:
            e = server.get("session.freeze.ignore", DEFAULT_SESSION_IGNORE, True)
            if not isinstance(e, list) or len(e) == 0:
                server.warning(
                    '[m/waybar]: Config value "session.freeze.ignore" is invalid (must be a list), '
                    "using an empty value!"
                )
            else:
                for i in e:
                    self._ignore.append(expand(i).lower())
            del e
        self._profiles["display"] = _trigger(server, "display")
        self._profiles["power_ac"] = _trigger(server, "power_ac")
        self._profiles["power_battery"] = _trigger(server, "power_battery")
        self._profiles["lock_pre"] = _trigger(server, "lock_pre")
        self._profiles["lock_post"] = _trigger(server, "lock_post")
        self._profiles["suspend_pre"] = _trigger(server, "suspend_pre")
        self._profiles["suspend_post"] = _trigger(server, "suspend_post")
        self._profiles["hibernate_pre"] = _trigger(server, "hibernate_pre")
        self._profiles["hibernate_post"] = _trigger(server, "hibernate_post")
        self._profiles["wireless_enable"] = _trigger(server, "wireless.enable")
        self._profiles["wireless_disable"] = _trigger(server, "wireless.disable")
        self._profiles["bluetooth_enable"] = _trigger(server, "bluetooth.enable")
        self._profiles["bluetooth_disable"] = _trigger(server, "bluetooth.disable")
        s = server.get("session.startups", DEFAULT_SESSION_STARTUPS, True)
        if not isinstance(s, list) or len(s) == 0:
            return
        for x in s:
            server.debug(f'[m/session]: Running startup process "{x}"..')
            try:
                p = nulexec(split(x, True))
                self._startup.append(p)
                server.watch(p)
                del p
            except OSError as err:
                server.warning(
                    f'[m/session]: Cannot execute the startup process "{x}"!', err
                )
        del s

    def _freeze(self, server, pre):
        if not self._can_freeze:
            return server.debug("[m/session]: Not freezing windows as it's disabled.")
        try:
            w = windows()
        except OSError as err:
            return server.error("[m/session]: Cannot retrive the window list!", err)
        if len(w) == 0:
            return server.debug("[m/session]: No windows detected, not freezing.")
        for i in w:
            if not _can_freeze(self._ignore, i):
                if pre:
                    server.debug(
                        f'[m/session]: Ignorining Window (pid="{i.pid}", app="{i.app}").'
                    )
                continue
            if pre:
                try:
                    kill(i.pid, SIGSTOP)
                except OSError as err:
                    server.error(
                        f'[m/session]: Cannot freeze Window (pid="{i.pid}", app="{i.app}")"!',
                        err,
                    )
                continue
            try:
                kill(i.pid, SIGCONT)
            except OSError as err:
                server.error(
                    f'[m/session]: Cannot un-freeze Window (pid="{i.pid}", app="{i.app}")!',
                    err,
                )
        del w

    def lock(self, server, message):
        if message.type == MSG_PRE:
            self._freeze(server, True)
            self._trigger(server, "lock_pre")
        elif message.type == MSG_POST:
            self._freeze(server, False)
            self._trigger(server, "lock_post")

    def _trigger(self, server, name):
        t = self._profiles.get(name)
        if t is None or not isinstance(t, list) or len(t) == 0:
            return
        server.debug(f'[m/session]: Running trigger commands for "{name}"!')
        for i in t:
            try:
                server.watch(nulexec(i))
            except OSError as err:
                server.error(
                    f'[m/session]: Cannot start the trigger ({name}) command "{i}"!',
                    err,
                )
            else:
                server.debug(
                    f'[m/session]: Started the trigger ({name}) command "{i}"!'
                )
        del t

    def reload(self, server, message):
        self._last_ac = None
        self._ignore.clear()
        self._profiles.clear()
        for i in self._startup:
            stop(i)
        self._startup.clear()
        if message.header() == HOOK_SHUTDOWN:
            return
        server.debug(
            "[m/session]: Reloading configuration and re-running startup commands.."
        )
        self.setup(server)

    def trigger(self, server, message):
        if message.header() == HOOK_POWER:
            if message.type == MSG_PRE:
                # NOTE(dij): Prevent re-running power triggers when the AC
                #            device reconnects.
                if self._last_ac is not None and not self._last_ac:
                    return
                self._last_ac = False
                return self._trigger(server, "power_battery")
            if message.type == MSG_POST:
                if self._last_ac is not None and self._last_ac:
                    return
                self._last_ac = True
                return self._trigger(server, "power_ac")
        if message.header() == HOOK_DISPLAY:
            return self._trigger(server, "display")
        if message.header() == HOOK_SUSPEND:
            return self._trigger(
                server, "suspend_pre" if message.type == MSG_PRE else "suspend_post"
            )
        if message.header() == HOOK_HIBERNATE:
            return self._trigger(
                server, "hibernate_pre" if message.type == MSG_PRE else "hibernate_post"
            )
        if (
            message.header() == HOOK_RADIO
            and message.type == MSG_ACTION
            and message.radio in RADIO_TYPES
        ):
            if message.radio == "wireless":
                return self._trigger(
                    server,
                    "wireless_enable"
                    if message.get("enabled", True)
                    else "wireless_disable",
                )
            elif message.radio == "bluetooth":
                return self._trigger(
                    server,
                    "bluetooth_enable"
                    if message.get("enabled", True)
                    else "bluetooth_disable",
                )

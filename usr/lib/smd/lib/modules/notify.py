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

# Module: User/Notifier
#   Manages and sends notifications to the User.

import gi

gi.require_version("Notify", "0.7")

from lib.util.file import expand
from lib.util import boolean, nes
from gi.repository import GObject, Notify
from os.path import isdir, isfile, isabs, splitext
from lib.constants.config import NAME_CLIENT, NOTIFY_ICONS, NOTIFY_EXTENSIONS
from lib.constants import EMPTY, HOOK_RELOAD, HOOK_NOTIFICATION, HOOK_SHUTDOWN
from lib.constants.defaults import (
    DEFAULT_NOTIFY_DIRS,
    DEFAULT_NOTIFY_ICON,
    DEFAULT_NOTIFY_THEME,
    DEFAULT_NOTIFY_FULLPATH,
)

HOOKS = {
    HOOK_RELOAD: "Notifier.reload",
    HOOK_SHUTDOWN: "Notifier.shutdown",
    HOOK_NOTIFICATION: "Notifier.notify",
}


class Notifier(GObject.Object):
    __slots__ = ("_dirs", "_full", "_cache", "_default")

    def __init__(self):
        super(Notifier, self).__init__()
        Notify.init(NAME_CLIENT)
        self._dirs = list()
        self._full = False
        self._cache = dict()
        self._default = None

    def setup(self, server):
        self._full = boolean(
            server.get("notify.full_path", DEFAULT_NOTIFY_FULLPATH, True)
        )
        v = server.get("notify.default", DEFAULT_NOTIFY_ICON, True)
        if not nes(v):
            server.warning(
                '[m/notify]: Config value "notify.default" is invalid (must be a non-empty string), '
                "using the default value!"
            )
            v = DEFAULT_NOTIFY_ICON
        d = server.get("notify.dirs", DEFAULT_NOTIFY_DIRS, True)
        if not isinstance(d, list):
            server.warning(
                '[m/notify]: Config value "notify.dirs" is invalid (must be a list), '
                "using the default value!"
            )
            d = DEFAULT_NOTIFY_DIRS
        for i in d:
            x = expand(i)
            if not isdir(x):
                server.warning(
                    f'[m/notify]: Icon path "{i}" does not exist or is is not a directory!'
                )
            self._dirs.append(x)
            del x
        t = server.get("notify.theme", DEFAULT_NOTIFY_THEME, True)
        if not nes(t):
            server.warning(
                '[m/notify]: Config value "notify.theme" is invalid (must be a non-empty string), '
                "using the default value!"
            )
            t = DEFAULT_NOTIFY_THEME
        x = expand(t)
        if not isdir(x):
            server.warning(
                f'[m/notify]: Theme path "{t}" does not exist or is is not a directory!'
            )
        self._dirs.append(x)
        self._default = expand(f"{t}/{v}")
        if not isfile(self._default):
            server.warning(
                f'[m/notify]: Default icon path "{self._default}" does not exist or is is not a file!'
            )
        del v, t, d, x

    def reload(self, server):
        server.debug("[m/notify]: Clearing cache and reloading configuration..")
        self._dirs.clear()
        self._cache.clear()
        self.setup(server)
        try:
            Notify.uninit()
            Notify.init(NAME_CLIENT)
        except Exception as err:
            server.error("[m/notify]: Cannot reload notification subsystem!", err)

    def shutdown(self, server):
        server.debug("[m/notify]: Un-registering notification client.")
        self._dirs.clear()
        self._cache.clear()
        Notify.uninit()

    def _icon_search(self, icon):
        for i in self._dirs:
            v = f"{i}/{icon}"
            if isfile(v):
                return v
            f, _ = splitext(v)
            del v
            for x in NOTIFY_EXTENSIONS:
                n = f"{f}{x}"
                if isfile(n):
                    return n
                del n
            del f
        return None

    def _icon(self, server, icon):
        if self._full:
            return icon
        if icon is None:
            return self._default
        if icon in self._cache:
            return self._cache[icon]
        p = NOTIFY_ICONS.get(icon, icon)
        if isabs(p):
            if isfile(p):
                self._cache[icon] = p
                return p
            v = self._icon_search(icon)
        else:
            v = self._icon_search(p)
        del p
        if v is None:
            return self._default
        server.debug(f'[m/notify]: Adding icon name "{icon}" to cache as "{v}".')
        self._cache[icon] = v
        return v

    def notify(self, server, message):
        if not nes(message.title):
            return
        n = Notify.Notification.new(
            message.title,
            f'{message.get("body", EMPTY)}',
            self._icon(server, message.icon),
        )
        try:
            n.show()
        except Exception as err:
            server.error(
                f'[m/notify]: Cannot send notification "{message.title}"!', err
            )
        del n

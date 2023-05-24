#!/usr/bin/false
# Module: Notifications (User)
#
# Manages and tracks notifications for the User.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2023 iDigitalFlame
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

import gi

gi.require_version("Notify", "0.7")

from gi.repository import GObject, Notify
from os.path import isfile, isabs, expandvars, expanduser
from lib.constants import (
    EMPTY,
    NAME_CLIENT,
    HOOK_RELOAD,
    NOTIFY_ICONS,
    HOOK_NOTIFICATION,
    DEFAULT_NOTIFY_ICON,
    DEFAULT_NOTIFY_THEME,
    DEFAULT_NOTIFY_FULLPATH,
    NOTIFY_ICONS_EXTENSIONS,
)

HOOKS = {
    HOOK_RELOAD: "NotifyClient.reload",
    HOOK_NOTIFICATION: "NotifyClient.notify",
}


class NotifyClient(object):
    def __init__(self):
        self.notifer = Notifer()

    def reload(self):
        Notify.uninit(NAME_CLIENT)
        del self.notifer
        self.notifer = Notifer()

    def notify(self, server, message):
        if not isinstance(message.title, str) or len(message.title) == 0:
            return
        self.notifer.notify(
            server, message.title, message.get("body", EMPTY), message.get("icon", None)
        )


class Notifer(GObject.Object):
    def __init__(self):
        super(Notifer, self).__init__()
        Notify.init(NAME_CLIENT)
        self.cache = dict()

    def _find_icon(self, server, icon=None):
        if server.get_config("notify.full_path", DEFAULT_NOTIFY_FULLPATH, False):
            return icon
        if "default" not in self.cache:
            v = (
                f"{server.get_config('notify.theme', DEFAULT_NOTIFY_THEME, True)}/"
                f"{server.get_config('notify.default', DEFAULT_NOTIFY_ICON, True)}"
            )
            self.cache["default"] = expandvars(expanduser(v))
            del v
        if icon is None:
            return self.cache["default"]
        if icon in self.cache:
            return self.cache[icon]
        if icon in NOTIFY_ICONS:
            p = NOTIFY_ICONS[icon]
        else:
            p = icon
        if isabs(p) and isfile(p):
            self.cache[icon] = p
            return p
        e = server.get_config("notify.dirs", list(), False)
        if not isinstance(e, list):
            e = list()
        else:
            e = e.copy()
        e.append(server.get_config("notify.theme", DEFAULT_NOTIFY_THEME, False))
        for d in e:
            t = expandvars(expanduser(f"{d}/{p}"))
            if isfile(t):
                p = t
                break
            if "." not in t or t.rfind(".") >= len(t) - 3:
                f = False
                for e in NOTIFY_ICONS_EXTENSIONS:
                    x = f"{t}.{e}"
                    if isfile(x):
                        p = x
                        f = True
                        break
                    del x
                if f:
                    break
                del f
            del t
        del e
        if p is None or not isfile(p):
            p = self.cache["default"]
        server.debug(f'Catching icon "{icon}" as "{p}".')
        self.cache[icon] = p
        return p

    def notify(self, server, title, message, icon=None):
        n = Notify.Notification.new(title, message, self._find_icon(server, icon))
        try:
            n.show()
        except Exception as err:
            server.error(f'Error sending notification "{title}"!', err=err)
        del n

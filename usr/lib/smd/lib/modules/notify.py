#!/usr/bin/false
# Module: Notifications (User)
#
# Manages and tracks notifications for the User.
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

import gi

gi.require_version("Notify", "0.7")

from lib.util import eval_env
from os.path import isfile, isabs
from gi.repository import GObject, Notify
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

    def reload(self, _):
        del self.notifer
        self.notifer = Notifer()

    def notify(self, server, message):
        if message.title is None:
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
        if not server.get_config("notify.full_path", DEFAULT_NOTIFY_FULLPATH, False):
            return icon
        if "default" not in self.cache:
            val = (
                f"{server.get_config('notify.theme', DEFAULT_NOTIFY_THEME, True)}/"
                f"{server.get_config('notify.default', DEFAULT_NOTIFY_ICON, True)}"
            )
            self.cache["default"] = eval_env(val)
            del val
        if icon is None:
            return self.cache["default"]
        if icon in self.cache:
            return self.cache[icon]
        if icon in NOTIFY_ICONS:
            path = NOTIFY_ICONS[icon]
        else:
            path = icon
        if isabs(path) and isfile(path):
            self.cache[icon] = path
            return path
        dirs = list()
        dirs_list = server.get_config("notify.dirs", list(), False)
        if isinstance(dirs, list):
            dirs += dirs_list
        del dirs_list
        dirs.append(server.get_config("notify.theme", DEFAULT_NOTIFY_THEME, False))
        for d in dirs:
            temp = eval_env(f"{d}/{path}")
            if isfile(temp):
                path = temp
                break
            if "." not in temp:
                found = False
                for e in NOTIFY_ICONS_EXTENSIONS:
                    ext = f"{temp}.{e}"
                    if isfile(ext):
                        path = ext
                        found = True
                        break
                    del ext
                if found:
                    break
        del dirs
        if not isfile(path):
            path = self.cache["default"]
        self.cache[icon] = path
        return path

    def notify(self, server, title, message, icon=None):
        notification = Notify.Notification.new(
            title, message, self._find_icon(server, icon)
        )
        try:
            notification.show()
        except Exception as err:
            server.error(
                f'Attempting to send notification "{title}" raised an exception!',
                err=err,
            )
        del notification

#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# Module: Notifications (User)
#
# Manages and tracks notifications for the User.

import gi

gi.require_version("Notify", "0.7")

from os.path import isfile, join
from gi.repository import GObject, Notify
from lib.constants import (
    HOOK_NOTIFICATION,
    NAME_CLIENT,
    NOTIFY_ICON_BASE,
    NOTIFY_ICONS,
    NOTIFY_ICON_DEFAULT,
    NOTIFY_ICON_EXTENSIONS,
)

HOOKS = {HOOK_NOTIFICATION: "NotifyClient.hook"}
HOOKS_SERVER = None


class NotifyClient(object):
    def __init__(self):
        self.notify = Notifer()

    def hook(self, server, message):
        title = message.get("title")
        if title is not None:
            self.notify.notify(
                title, message.get("body", ""), message.get("icon", None)
            )
            del title


class Notifer(GObject.Object):
    def __init__(self):
        super(Notifer, self).__init__()
        Notify.init(NAME_CLIENT)

    def notify(self, title, message, icon=None):
        if icon is None:
            icon = join(NOTIFY_ICON_BASE, NOTIFY_ICON_DEFAULT)
        else:
            if icon in NOTIFY_ICONS:
                icon = NOTIFY_ICONS[icon]
            elif "/" not in icon:
                icon = join(NOTIFY_ICON_BASE, icon)
            if not isfile(icon):
                found = False
                if "." not in icon:
                    for extension in NOTIFY_ICON_EXTENSIONS:
                        if isfile("%s.%s" % (icon, extension)):
                            found = True

                            icon = "%s.%s" % (icon, extension)
                            break
                if not found:
                    icon = join(NOTIFY_ICON_BASE, NOTIFY_ICON_DEFAULT)
                del found
            else:
                icon = join(NOTIFY_ICON_BASE, NOTIFY_ICON_DEFAULT)
        notification = Notify.Notification.new(title, message, icon)
        notification.show()
        del notification

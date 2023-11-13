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

# defaults.py
#   Configurable Constants Values for: Defaults
#   Contains constants that are user configurable and reperesent the default
#   values for some operations.
#
#   This file is loaded from "/opt/spaceport/var/cache/smd/defaults.json" in JSON
#   format. The names present will replace any values contained in this file.

from lib.util.file import import_file
from lib.constants import CUSTOM_DEFAULTS

## Default Configuration Constants
# Overrides are loaded from disk from "CUSTOM_DEFAULTS".

# Waybar Defaults
DEFAULT_WAYBAR_NAME = "bar"

# Locker Defaults
DEFAULT_LOCKER_LID = True
DEFAULT_LOCKER_LOCK = 120
DEFAULT_LOCKER_BLANK = 60
DEFAULT_LOCKER_LOCKER = ["/usr/bin/swaylock", "-n"]
DEFAULT_LOCKER_SUSPEND = 120
DEFAULT_LOCKER_KEY_LOCK = True
DEFAULT_LOCKER_HIBERNATE = 300

# Notification Defaults
DEFAULT_NOTIFY_DIRS = list()
DEFAULT_NOTIFY_ICON = "dialog-information.png"
DEFAULT_NOTIFY_THEME = "/usr/share/icons/hicolor/scalable/status"
DEFAULT_NOTIFY_FULLPATH = False

# Background Defaults
DEFAULT_BACKGROUND_PATH = "${HOME}/Pictures/Backgrounds"
DEFAULT_BACKGROUND_SWITCH = 600
DEFAULT_BACKGROUND_LOCKSCREEN = "${HOME}/.cache/smd/lockscreen.png"

# Session Defaults
DEFAULT_SESSION_IGNORE = list()
DEFAULT_SESSION_FREEZE = True
DEFAULT_SESSION_MONITOR = False
DEFAULT_SESSION_STARTUPS = ["/usr/bin/nm-applet"]

import_file(CUSTOM_DEFAULTS)

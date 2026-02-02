################################
### iDigitalFlame  2016-2026 ###
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
# Copyright (C) 2016 - 2026 iDigitalFlame
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

# __init__.py
#   Constants Values for: Base
#
#   Contains constants that are not user configurable. This is the base of the
#   "lib.constants" package.

# Base Constants
EMPTY = str()
NEWLINE = "\n"
VERSION = "SMD-8.0_Tank_v2"
BOOLEANS = [
    "0",
    "1",
    "disable",
    "enable",
    "f",
    "false",
    "no",
    "off",
    "on",
    "t",
    "true",
    "yes",
]

# User Constants Configuration.
# Can be used to modify the values in the "constants.config" package.
CUSTOM_CONFIG = "/opt/spaceport/var/cache/smd/constants.json"
# Can be used to modify the values in the "constants.defaults" package.
CUSTOM_DEFAULTS = "/opt/spaceport/var/cache/smd/defaults.json"

# Hook Type Constants
## System Hooks
HOOK_OK = 0xC8
HOOK_LOG = 0xF0
HOOK_ERROR = 0xFF
HOOK_RELOAD = 0xF5
HOOK_DAEMON = 0x00
HOOK_STARTUP = 0x01
HOOK_SHUTDOWN = 0xFA
## Locker/Lock Screen Hooks
HOOK_LOCK = 0xA0
HOOK_LOCKER = 0xA6
## Hardware Event Hooks
HOOK_CPU = 0xA4
HOOK_USB = 0xAE
HOOK_POWER = 0xA1
HOOK_RADIO = 0xA5
HOOK_MONITOR = 0xA3
HOOK_DISPLAY = 0xA8
HOOK_BRIGHTNESS = 0xA7
## Power Notification Hooks
HOOK_SUSPEND = 0xC0
HOOK_HIBERNATE = 0xC1
## Hydra Hooks
HOOK_HYDRA = 0xE0
## Backup Hooks
HOOK_BACKUP = 0xBA
## Userland Hooks
HOOK_BACKGROUND = 0xBF
HOOK_NOTIFICATION = 0xB2

# Message Standard Type Constants
MSG_PRE = 0x00
MSG_POST = 0x01
MSG_USER = 0x06
MSG_ALERT = 0x07
MSG_STATUS = 0x02
MSG_ACTION = 0x03
MSG_CONFIG = 0x04
MSG_UPDATE = 0x05

# Logging Constants
LOG_LEVELS = {
    "0": 10,
    "1": 20,
    "2": 30,
    "3": 40,
    "4": 50,
    "debug": 10,
    "info": 20,
    "warning": 30,
    "error": 40,
    "critical": 50,
}
LOG_LEVELS_PREFIX = {
    90: " DUMP",
    50: " CRIT",
    40: "ERROR",
    30: " WARN",
    20: " INFO",
    10: "DEBUG",
}
LOG_LEVELS_REVERSE = {
    10: "debug",
    20: "info",
    30: "warning",
    40: "error",
    50: "critical",
}

# Locker Trigger Types
TRIGGER_KEY = 0x3
TRIGGER_LOCK = 0x0
TRIGGER_BLANK = 0x1
TRIGGER_TIMEOUT = 0x2

## Locker Backoff Times
LOCKER_TIME_BLANK = 7
LOCKER_TIME_BACKOFF = 5

## Locker Type Constants
## Translations are in the user "LOCKER_TYPE_NAMES" value.
LOCKER_TYPE_LID = "lid"
LOCKER_TYPE_KEY = "key"
LOCKER_TYPE_LOCK = "lock"
LOCKER_TYPE_BLANK = "blank"
LOCKER_TYPE_BACKUP = "backup"
LOCKER_TYPE_FREEZE = "freeze"
LOCKER_TYPE_SUSPEND = "suspend"
LOCKER_TYPE_HIBERNATE = "hibernate"

# Backup Constants
## Size string "array"
BACKUP_SIZES = "KMGTPEZ"
## Status Names
## The index is the BACKUP_STATE_* type.
BACKUP_STATE_NAMES = [
    "Idle",
    "Prep",
    "Keygen",
    "Compress",
    "Encrypt",
    "Compress",
    "Manifest",
    "Manifest",
    "Hashing",
    "Hashing",
    "Packing",
    "Upload",
    "Error",
    "Done",
]
## Status Messages
BACKUP_STATE_DONE = 0xD
BACKUP_STATE_ERROR = 0xC
BACKUP_STATE_KEYGEN = 0x2
BACKUP_STATE_PRE_CMD = 0x1
BACKUP_STATE_WAITING = 0x0
BACKUP_STATE_PACKING = 0xA
BACKUP_STATE_COMPRESS = 0x5
BACKUP_STATE_NO_KEYGEN = 0x3
BACKUP_STATE_UPLOADING = 0xB
BACKUP_STATE_HASHING_P1 = 0x8
BACKUP_STATE_HASHING_P2 = 0x9
BACKUP_STATE_MANIFEST_P1 = 0x6
BACKUP_STATE_MANIFEST_P2 = 0x7
BACKUP_STATE_ENCRYPT_COMPRESS = 0x4

# Hydra Constants
## Virtual Machine State
HYDRA_STATE_DONE = 0x4
HYDRA_STATE_SNAP = 0x6
HYDRA_STATE_FAILED = 0x5
HYDRA_STATE_STOPPED = 0x10
HYDRA_STATE_WAITING = 0x1
HYDRA_STATE_RUNNING = 0x2
HYDRA_STATE_SLEEPING = 0x3
HYDRA_STATE_SNAP_DEL = 0x8
HYDRA_STATE_SNAP_LOAD = 0x7

## System Commands
HYDRA_TAP = 0x24
HYDRA_STOP = 0x11
HYDRA_WAKE = 0x12
HYDRA_START = 0x13
HYDRA_SLEEP = 0x14
HYDRA_GA_IP = 0x22
HYDRA_STATUS = MSG_STATUS
HYDRA_RESTART = 0x25
HYDRA_GA_PING = 0x23
HYDRA_USB_ADD = 0x15
HYDRA_USB_QUERY = 0x32
HYDRA_USB_CLEAN = 0x21
HYDRA_HIBERNATE = 0x26
HYDRA_SNAP_LIST = 0x27
HYDRA_SNAP_TAKE = 0x28
HYDRA_USB_DELETE = 0x17
HYDRA_SEND_INPUT = 0x31
HYDRA_SNAP_DELETE = 0x29
HYDRA_USER_RESULT = 0x33
HYDRA_SNAP_RESTORE = 0x30
HYDRA_USB_RECONNECT = 0x34
HYDRA_USER_DIRECTORY = 0x18
HYDRA_USER_ADD_ALIAS = 0x19
HYDRA_USER_DELETE_ALIAS = 0x20

## Hydra Input Keymapping Constants
HYDRA_KEYS_MAP = {
    0x29: "0",
    0x21: "1",
    0x40: "2",
    0x23: "3",
    0x24: "4",
    0x25: "5",
    0x5E: "6",
    0x26: "7",
    0x2A: "8",
    0x28: "9",
    0x22: "apostrophe",
    0x7C: "backslash",
    0x7B: "bracket_left",
    0x7D: "bracket_right",
    0x3C: "comma",
    0x3E: "dot",
    0x2B: "equal",
    0x7E: "grave_accent",
    0x5F: "minus",
    0x3A: "semicolon",
    0x3F: "slash",
}
HYDRA_KEYS_CTRL = [
    "AGAIN",
    "ALT",
    "AUDIOMUTE",
    "AUDIONEXT",
    "AUDIOPLAY",
    "AUDIOPREV",
    "AUDIOSTOP",
    "BACKSPACE",
    "CALCULATOR",
    "CAPS_LOCK",
    "COMPOSE",
    "COMPUTER",
    "COPY",
    "CTRL",
    "CUT",
    "DOWN",
    "END",
    "ESC",
    "FIND",
    "HELP",
    "HOME",
    "INSERT",
    "LEFT",
    "LESS",
    "MAIL",
    "MEDIASELECT",
    "MENU",
    "META_L",
    "META_R",
    "NUM_LOCK",
    "PASTE",
    "PAUSE",
    "PGDN",
    "PGUP",
    "POWER",
    "PRINT",
    "PROPS",
    "RET",
    "RIGHT",
    "SCROLL_LOCK",
    "SHIFT",
    "SLEEP",
    "STOP",
    "TAB",
    "UNDO",
    "UP",
    "VOLUMEDOWN",
    "VOLUMEUP",
    "WAKE",
]
HYDRA_KEYS_NAMED = {
    0x27: "apostrophe",
    0x5C: "backslash",
    0x5B: "bracket_left",
    0x5D: "bracket_right",
    0x2C: "comma",
    0x2E: "dot",
    0x3D: "equal",
    0x60: "grave_accent",
    0x2D: "minus",
    0x3B: "semicolon",
    0x2F: "slash",
}
HYDRA_KEYS_SIMPLE = b"abcdefghijklmnopqrstuvwxyz12345678901234567890"
HYDRA_KEYS_CTRL_MAP = {
    "audio_mute": "AUDIOMUTE",
    "audio_play": "AUDIOPLAY",
    "audio_stop": "AUDIOSTOP",
    "calc": "CALCULATOR",
    "caps": "CAPS_LOCK",
    "capslock": "CAPS_LOCK",
    "media_select": "MEDIASELECT",
    "media": "MEDIASELECT",
    "super": "META_L",
    "win": "META_L",
    "meta": "META_L",
    "numlock": "NUM_LOCK",
    "page_down": "PGDN",
    "pagedown": "PGDN",
    "page_up": "PGUP",
    "pageup": "PGUP",
    "enter": "RET",
    "return": "RET",
    "scrolllock": "SCROLL_LOCK",
    "volume_down": "VOLUMEDOWN",
    "vol_down": "VOLUMEDOWN",
    "volume_up": "VOLUMEUP",
    "vol_up": "VOLUMEUP",
}

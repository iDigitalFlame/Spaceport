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

# __init__.py
#   Constants Values for: Base
#
#   Contains constants that are not user configurable. This is the base of the
#   "lib.constants" package.

## Base Constants
EMPTY = str()
NEWLINE = "\n"
VERSION = "SMD-7.6_Tank_v2"
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

## User Constants Configuration.
# Can be used to modify the values in the "constants.config" package.
CUSTOM_CONFIG = "/opt/spaceport/var/cache/smd/constants.json"
# Can be used to modify the values in the "constants.defaults" package.
CUSTOM_DEFAULTS = "/opt/spaceport/var/cache/smd/defaults.json"

## Hook Type Constants
# System Hooks
HOOK_OK = 0xC8
HOOK_LOG = 0xF0
HOOK_ERROR = 0xFF
HOOK_RELOAD = 0xF5
HOOK_DAEMON = 0x00
HOOK_STARTUP = 0x01
HOOK_SHUTDOWN = 0xFA
# Locker/Lock Screen Hooks
HOOK_LOCK = 0xA0
HOOK_LOCKER = 0xA6
# Hardware Event Hooks
HOOK_CPU = 0xA4
HOOK_POWER = 0xA1
HOOK_RADIO = 0xA5
HOOK_MONITOR = 0xA3
HOOK_DISPLAY = 0xA8
HOOK_BRIGHTNESS = 0xA7
# Power Notification Hooks
HOOK_SUSPEND = 0xC0
HOOK_HIBERNATE = 0xC1
# Hydra Hooks
HOOK_HYDRA = 0xE0
# Backup Hooks
HOOK_BACKUP = 0xBA
# Userland Hooks
HOOK_BACKGROUND = 0xBF
HOOK_NOTIFICATION = 0xB2

## Message Standard Type Constants
MSG_PRE = 0x00
MSG_POST = 0x01
MSG_USER = 0x06
MSG_STATUS = 0x02
MSG_ACTION = 0x03
MSG_CONFIG = 0x04
MSG_UPDATE = 0x05

## Hydra Constants
# Machine State
HYDRA_STATE_DONE = 0x4
HYDRA_STATE_FAILED = 0x5
HYDRA_STATE_STOPPED = 0x10
HYDRA_STATE_WAITING = 0x1
HYDRA_STATE_RUNNING = 0x2
HYDRA_STATE_SLEEPING = 0x3

# System
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
HYDRA_USB_QUERY = HYDRA_STATUS
HYDRA_USB_CLEAN = 0x21
HYDRA_HIBERNATE = 0x26
HYDRA_USB_DELETE = 0x17

# User
HYDRA_USER_DIRECTORY = 0x18
HYDRA_USER_ADD_ALIAS = 0x19
HYDRA_USER_DELETE_ALIAS = 0x20

## Logging Translation Constants
LOG_INDEX = {50: " CRIT ", 40: "ERROR", 30: " WARN", 20: " INFO", 10: "DEBUG"}

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
LOG_LEVELS_REVERSE = {
    10: "debug",
    20: "info",
    30: "warning",
    40: "error",
    50: "critical",
}

## Power/Locker Trigger Types
TRIGGER_KEY = 0x3
TRIGGER_LOCK = 0x0
TRIGGER_BLANK = 0x1
TRIGGER_TIMEOUT = 0x2

## Locker Time Options
LOCKER_TIME_BLANK = 7
LOCKER_TIME_BACKOFF = 5

## Locker Type Name Constants
# Translations are in the user "LOCKER_TYPE_NAMES" value.
LOCKER_TYPE_LID = "lid"
LOCKER_TYPE_KEY = "key"
LOCKER_TYPE_LOCK = "lock"
LOCKER_TYPE_BLANK = "blank"
LOCKER_TYPE_BACKUP = "backup"
LOCKER_TYPE_FREEZE = "freeze"
LOCKER_TYPE_SUSPEND = "suspend"
LOCKER_TYPE_HIBERNATE = "hibernate"

## Backup Constants
# Size string "array"
BACKUP_SIZES = "KMGTPEZ"
# Status Names
# The index is the BACKUP_STATE_* type.
BACKUP_STATE_NAMES = [
    "idle",
    "prep",
    "keygen",
    "compress",
    "encrypt",
    "compress",
    "hashing",
    "hashing",
    "packing",
    "upload",
    "error",
    "done",
]
# Status Messages
BACKUP_STATE_DONE = 0xB
BACKUP_STATE_ERROR = 0xA
BACKUP_STATE_KEYGEN = 0x2
BACKUP_STATE_PRE_CMD = 0x1
BACKUP_STATE_WAITING = 0x0
BACKUP_STATE_PACKING = 0x8
BACKUP_STATE_COMPRESS = 0x5
BACKUP_STATE_NO_KEYGEN = 0x3
BACKUP_STATE_UPLOADING = 0x9
BACKUP_STATE_HASHING_P1 = 0x6
BACKUP_STATE_HASHING_P2 = 0x7
BACKUP_STATE_ENCRYPT_COMPRESS = 0x4

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

# config.py
#   Configurable Constants Values for: Base
#
#   Contains constants that are user configurable.
#
#   This file is loaded from "/opt/spaceport/var/cache/smd/config.json" in JSON
#   format. The names present will replace any values contained in this file.

from socket import gethostname
from lib.util.file import import_file
from lib.constants import (
    HOOK_OK,
    HOOK_LOG,
    HOOK_LOCK,
    HOOK_POWER,
    HOOK_BACKUP,
    HOOK_RELOAD,
    HOOK_MONITOR,
    HOOK_SUSPEND,
    CUSTOM_CONFIG,
    HOOK_HIBERNATE,
    HOOK_BACKGROUND,
    LOCKER_TYPE_KEY,
    LOCKER_TYPE_LID,
    LOCKER_TYPE_LOCK,
    LOCKER_TYPE_BLANK,
    HOOK_NOTIFICATION,
    LOCKER_TYPE_SUSPEND,
    LOCKER_TYPE_HIBERNATE,
)

## Default Configuration Constants
# Overrides are loaded from disk from "CUSTOM_CONFIG".

# Naming Conventions
NAME = gethostname().lower()
NAME_CLIENT = "smd-client"
NAME_SERVER = "smd-daemon"
NAME_POWERCTL = "powerctl"

# Directory Path Constants
DIRECTORY_BASE = "/usr/lib/smd"
DIRECTORY_LIB = f"{DIRECTORY_BASE}/lib"
DIRECTORY_TEMP = "/var/run/smd"
DIRECTORY_CONFIG = "/var/cache/smd"
DIRECTORY_MODULES = f"{DIRECTORY_LIB}/modules"
DIRECTORY_LIBEXEC = f"{DIRECTORY_BASE}/libexec"
DIRECTORY_POWERCTL = f"{DIRECTORY_LIB}/powerctl"

# Socket Constants
SOCKET = f"{DIRECTORY_TEMP}/{NAME}.sock"
SOCKET_GROUP = "smd"
SOCKET_BACKLOG = 512

# Waiting/Timeout Constants
TIMEOUT_SEC_STOP = 15
TIMEOUT_SEC_HOOK = 15
TIMEOUT_SEC_MESSAGE = 5

# Configuration Path Constants
CONFIG_CLIENT = "${HOME}/.config/smd.json"
CONFIG_SERVER = f"{DIRECTORY_CONFIG}/config.json"
CONFIG_BACKUP = f"{DIRECTORY_CONFIG}/backup.json"

# Log Constants
LOG_TICKS = True
LOG_LEVEL = "warning"
LOG_PAYLOAD = False
LOG_FRAME_LIMIT = 15

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_FORMAT_JOURNAL = "[%(levelname)s]: %(message)s"

LOG_PATH_SERVER = f"{DIRECTORY_TEMP}/{NAME}-server.log"
LOG_PATH_CLIENT = "/var/run/user/{uid}/smd-client-{pid}.log"

HOOK_TRANSLATIONS = {
    "ok": HOOK_OK,
    "log": HOOK_LOG,
    "lock": HOOK_LOCK,
    "power": HOOK_POWER,
    "notify": HOOK_NOTIFICATION,
    "backup": HOOK_BACKUP,
    "reload": HOOK_RELOAD,
    "monitor": HOOK_MONITOR,
    "suspend": HOOK_SUSPEND,
    "hibernate": HOOK_HIBERNATE,
    "background": HOOK_BACKGROUND,
}

# Hydra Module Constants
HYDRA_USER = "qemu"
HYDRA_WAIT_TIME = 10
HYDRA_SOCK_BUF_SIZE = 4096
HYDRA_PATH_MOUNTS = "/proc/self/mounts"
HYDRA_VM_CONFIGS = ["vm.conf", "vm.json", "vmx"]

HYDRA_BRIDGE = "vmi0"
HYDRA_BRIDGE_NAME = f"vm.{NAME}"
HYDRA_BRIDGE_NETWORK = "172.16.172.0/26"

HYDRA_DIR = f"{DIRECTORY_TEMP}/hydra"
HYDRA_DIR_USB = "/sys/bus/usb/devices/*/idVendor"
HYDRA_DIR_DHCP = f"{DIRECTORY_CONFIG}/hydra"
HYDRA_DIR_DEVICES = "/dev/bus/usb"

HYDRA_EXEC_VM = "/usr/bin/qemu-system-x86_64"
HYDRA_EXEC_SMB = "/usr/bin/smbd"
HYDRA_EXEC_DNS = "/usr/bin/dnsmasq"
HYDRA_EXEC_VNC = "/usr/bin/vncviewer"
HYDRA_EXEC_SPICE = "/usr/bin/spicy"

HYDRA_FILE_SMB = f"{HYDRA_DIR}/smb.conf"
HYDRA_FILE_DNS = f"{HYDRA_DIR}/dns.conf"

HYDRA_RESERVE = "/proc/sys/vm/nr_hugepages"
HYDRA_RESERVE_SIZE = 2

# CPU Module Constants
CPU_PATH = "/sys/devices/system/cpu"
CPU_PATH_MIN = "cpufreq/cpuinfo_min_freq"
CPU_PATH_MAX = "cpufreq/cpuinfo_max_freq"
CPU_PATH_CURRENT = "cpufreq/scaling_cur_freq"

CPU_PATH_GOVERNOR = "cpufreq/scaling_governor"
CPU_PATH_GOVERNORS = "cpufreq/scaling_available_governors"

CPU_PATH_SCALING_MIN = "cpufreq/scaling_min_freq"
CPU_PATH_SCALING_MAX = "cpufreq/scaling_max_freq"

CPU_PATH_PERFORMANCE = "cpufreq/energy_performance_preference"
CPU_PATH_PERFORMANCES = "cpufreq/energy_performance_available_preferences"

CPU_PATH_TURBO = "/sys/devices/system/cpu/intel_pstate/no_turbo"
CPU_PATH_TURBO_MIN = "/sys/devices/system/cpu/intel_pstate/min_perf_pct"
CPU_PATH_TURBO_MAX = "/sys/devices/system/cpu/intel_pstate/max_perf_pct"
CPU_PATH_TURBO_CURRENT = "/sys/devices/system/cpu/intel_pstate/turbo_pct"

# Brightess Module Constants
BRIGHTNESS_PATH = "/sys/class/backlight/intel_backlight/brightness"
BRIGHTNESS_PATH_MAX = "/sys/class/backlight/intel_backlight/max_brightness"

# Notification Module Constants
NOTIFY_ICONS = {
    "error": "dialog-error.png",
    "warn": "dialog-warning.png",
    "warning": "dialog-warning.png",
    "info": "dialog-information.svg",
    "question": "dialog-question.png",
}
NOTIFY_EXTENSIONS = [".png", ".svg", ".jpg", ".gif", ".ico"]

# Radio Module Constants
RADIO_PATH_WIFI = "/sys/class/net"
RADIO_PATH_BLUE = "/sys/class/bluetooth/*/rfkill*/state"

RADIO_TYPES = [
    "bluetooth",
    "wireless",
]
RADIO_EXEC = {
    "bluetooth_disable": [
        "/usr/bin/systemctl stop bluetooth.service",
        "/usr/bin/rfkill block bluetooth",
    ],
    "bluetooth_enable": [
        "/usr/bin/rfkill unblock bluetooth",
        "/usr/bin/systemctl start bluetooth.service",
    ],
    "wireless_disable": ["/usr/bin/rfkill block wifi"],
    "wireless_enable": ["/usr/bin/rfkill unblock wifi"],
}

# Backup Module Constants
BACKUP_STATE = f"{DIRECTORY_CONFIG}/backup-state.json"
BACKUP_HOSTS = "/etc/smd/backup-hosts.ssh"
BACKUP_TIMEOUT = 7200
BACKUP_KEY_SIZE = 0xFF
BACKUP_STATE_DIR = f"{DIRECTORY_CONFIG}/backup"
BACKUP_WAIT_TIME = 86400
BACKUP_DEFAULT_DIR = "/opt/hydra/smd-backup"
BACKUP_DEFAULT_PORT = 22
BACKUP_BATTERY_PATH = "/sys/class/power_supply/AC/online"

BACKUP_EXCLUDE = [
    "/dev",
    "/sys",
    "/tmp",
    "/run",
    "/proc",
    "/var/run",
]

# Background Module Constants
BACKGROUND_PATH_CACHE = "${HOME}/.cache/smd"
BACKGROUND_PATH_EXTENSIONS = [".jpg", ".png", ".jpeg", ".bmp"]

LOCKER_TYPE_NAMES = {
    LOCKER_TYPE_KEY: "Yubikey",
    LOCKER_TYPE_LID: "Lid Close",
    LOCKER_TYPE_LOCK: "Lockscreen",
    LOCKER_TYPE_BLANK: "Screen Blank",
    LOCKER_TYPE_SUSPEND: "Suspend",
    LOCKER_TYPE_HIBERNATE: "Hibernate",
}

LOCKER_PATH_DIR = "${HOME}/.config/theme/current"
LOCKER_PATH_STATUS = f"{DIRECTORY_TEMP}/lockers"
LOCKER_PATH_BATTERY = "/sys/class/power_supply/AC/online"
LOCKER_PATH_WAKEALARM = "/sys/class/rtc/rtc0/wakealarm"

LOCKER_EXEC_LOCK = f"{DIRECTORY_LIBEXEC}/smd-locker"
LOCKER_EXEC_DND_ON = ["/usr/bin/swaync-client", "--skip-wait", "--dnd-on"]
LOCKER_EXEC_DND_OFF = ["/usr/bin/swaync-client", "--skip-wait", "--dnd-off"]
LOCKER_EXEC_SUSPEND = ["/usr/bin/systemctl", "suspend"]
LOCKER_EXEC_HIBERNATE = ["/usr/bin/systemctl", "hibernate"]

# Screen Constants
DISPLAY_BUILTIN = "eDP-1"

# Screen Utility Paths
DISPLAY_PATH_LID = "/proc/acpi/button/lid/LID0/state"
DISPLAY_PATH_ACTIVE = "/sys/class/graphics/fb0/device/drm/card*/card*/enabled"
DISPLAY_PATH_DEFAULT = (
    f"/sys/class/graphics/fb0/device/drm/card*/card*{DISPLAY_BUILTIN}/enabled"
)
DISPLAY_PATH_CONNECTED = "/sys/class/graphics/fb0/device/drm/card*/card*/status"

import_file(CUSTOM_CONFIG)

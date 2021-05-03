#!/usr/bin/false
# The Constants Python file is to hold and save basic defaults that may be used in the
# execution of the System Management Daemon.
#
# This file is saved/loaded to "/opt/spaceport/var/cache/smd/constants.json" as a JSON file.
# These paramaters are updated and saved to the file when it does not exist.
# The file paramaters are loaded from the file when it exists and will only fill in non-defaults.
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

from os.path import isfile
from socket import gethostname
from importlib import import_module
from lib.util import read_json, write_json


def __init__(config_file):
    instance = import_module(__name__)
    if not isfile(config_file):
        vars = dict()
        for name, value in instance.__dict__.items():
            if name is None or len(name) == 0 or name[0] == "_" or not name.isupper():
                continue
            vars[name.lower()] = value
        write_json(
            config_file, vars, indent=4, sort=True, ignore_errors=True, perms=644
        )
        del vars
        del instance
        return
    vars = read_json(config_file, ignore_errors=True)
    if isinstance(vars, dict):
        for name, value in vars.items():
            try:
                setattr(instance, name.upper(), value)
            except AttributeError:
                pass
    del vars
    del instance


EMPTY = str()
VERSION = "SMD-5.5Tank"
BOOLEANS = ["0", "1", "true", "false", "on", "off", "t", "f", "yes", "no"]

NAME_POWERCTL = "powerctl"
NAME_CLIENT = "smd-client"
NAME_SERVER = "smd-daemon"
NAME = gethostname().lower()

# Directory Path Constants
DIRECTORY_TEMP_CLIENT = "/tmp"
DIRECTORY_TEMP = "/var/run/smd"
DIRECTORY_BASE = "/usr/lib/smd"
DIRECTORY_CONFIG = "/var/cache/smd"
DIRECTORY_LIB = f"{DIRECTORY_BASE}/lib"
DIRECTORY_HYDRA = f"{DIRECTORY_TEMP}/hydra"
DIRECTORY_STATIC = f"{DIRECTORY_BASE}/static"
DIRECTORY_MODULES = f"{DIRECTORY_LIB}/modules"
DIRECTORY_LIBEXEC = f"{DIRECTORY_BASE}/libexec"
DIRECTORY_POWERCTL = f"{DIRECTORY_LIB}/powerctl"

# Socket Constants
SOCKET_BACKLOG = 512
SOCKET_READ_ERRNO = 1000
SOCKET_READ_INT_SIZE = 4
SOCKET = f"{DIRECTORY_TEMP}/{NAME}.sock"

# Configuration Path Constants
CONFIG_CLIENT = "${HOME}/.config/smd.json"
CONFIG_CPU = f"{DIRECTORY_CONFIG}/cpu.json"
CONFIG_BACKUP = f"{DIRECTORY_CONFIG}/backup.json"
CONFIG_SERVER = f"{DIRECTORY_CONFIG}/config.json"
CONFIG_CONSTANTS = "/opt/spaceport/var/cache/smd/constants.json"

# Log Constants
LOG_TICKS = True
LOG_PAYLOAD = False
LOG_LEVEL = "WARNING"
LOG_PATH_SERVER = f"{DIRECTORY_TEMP}/{NAME}-server.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_PATH_CLIENT = f"{DIRECTORY_TEMP_CLIENT}/smd-${{USER}}-{{pid}}.log"
LOG_NAMES = {50: "CRITICAL", 40: "ERROR", 30: "WARNING", 20: "INFO", 10: "DEBUG"}
LOG_LEVELS = {
    "0": "DEBUG",
    "1": "INFO",
    "2": "WARNING",
    "3": "ERROR",
    "4": "CRITICAL",
    "debug": "DEBUG",
    "info": "INFO",
    "warning": "WARNING",
    "error": "ERROR",
    "critical": "CRITICAL",
}

# Hook Type Constants
HOOK_OK = 0xC8
HOOK_CPU = 0xA4
HOOK_LOG = 0xF0
HOOK_LOCK = 0xA0
HOOK_ERROR = 0xFF
HOOK_HYDRA = 0xE0
HOOK_POWER = 0xA1
HOOK_RADIO = 0xA5
HOOK_BACKUP = 0xBA
HOOK_RELOAD = 0xF5
HOOK_DAEMON = 0x00
HOOK_ROTATE = 0xA2
HOOK_LOCKER = 0xA6
HOOK_SUSPEND = 0xC0
HOOK_MONITOR = 0xA3
HOOK_DISPLAY = 0xA8
HOOK_STARTUP = 0x01
HOOK_SHUTDOWN = 0xFA
HOOK_HIBERNATE = 0xC1
HOOK_BACKGROUND = 0xBF
HOOK_BRIGHTNESS = 0xA7
HOOK_NOTIFICATION = 0xB2
HOOK_THREAD_TIMEOUT = 15
HOOK_TRANSLATIONS = {
    "ok": HOOK_OK,
    "lock": HOOK_LOCK,
    "power": HOOK_POWER,
    "backup": HOOK_BACKUP,
    "reload": HOOK_RELOAD,
    "monitor": HOOK_MONITOR,
    "suspend": HOOK_SUSPEND,
    "notify": HOOK_NOTIFICATION,
    "hibernate": HOOK_HIBERNATE,
    "background": HOOK_BACKGROUND,
}

# Message Standard Type Constants
MESSAGE_TYPE_PRE = 0x00
MESSAGE_TYPE_POST = 0x01
MESSAGE_TYPE_STATUS = 0x02
MESSAGE_TYPE_ACTION = 0x03
MESSAGE_TYPE_CONFIG = 0x04

# Default Configuration Constants
# Polybar Defaults
DEFAULT_POLYBAR_NAME = "bar"
# Locker Defaults
DEFAULT_LOCKER_LID = True
DEFAULT_LOCKER_LOCK = 120
DEFAULT_LOCKER_BLANK = 60
DEFAULT_LOCKER_SUSPEND = 120
DEFAULT_LOCKER_HIBERNATE = 300
DEFAULT_LOCKER_KEY_LOCK = True
DEFAULT_LOCKER_LOCKER = ["/usr/bin/i3lock", "-n"]
# Notification Defaults
DEFAULT_NOTIFY_ICON = "dialog-information.png"
DEFAULT_NOTIFY_THEME = ["/usr/share/icons/hicolor/scalable/status"]
DEFAULT_NOTIFY_FULLPATH = False
# Background Defaults
DEFAULT_BACKGROUND_SWITCH = 600
DEFAULT_BACKGROUND_PATH = "${HOME}/Pictures/Backgrounds"
DEFAULT_BACKGROUND_LOCKSCREEN = "${HOME}/.cache/smd/lockscreen.png"
# Session Defaults
DEFAULT_SESSION_TAP = False
DEFAULT_SESSION_MONITOR = False
DEFAULT_SESSION_STARTUPS = ["/usr/bin/nm-applet"]
DEFAULT_SESSION_COMPOSER = ["/usr/bin/picom", "-c"]

# Hydra Module Constants
HYDRA_STOP = 0x11
HYDRA_WAKE = 0x12
HYDRA_UID = "kvm"
HYDRA_START = 0x13
HYDRA_SLEEP = 0x14
HYDRA_USB_ADD = 0x15
HYDRA_BRIDGE = "vmi0"
HYDRA_USB_QUERY = 0x16
HYDRA_USB_CLEAN = 0x21
HYDRA_RESERVE_SIZE = 2
HYDRA_USB_DELETE = 0x17
HYDRA_USER_DIRECTORY = 0x18
HYDRA_USER_ADD_ALIAS = 0x19
HYDRA_USER_DELETE_ALIAS = 0x20
HYDRA_EXEC_SMB = "/usr/bin/smbd"
HYDRA_BRIDGE_NAME = f"vm.{NAME}"
HYDRA_STATUS = MESSAGE_TYPE_STATUS
HYDRA_USB_DEVICES = "/dev/bus/usb"
HYDRA_EXEC_DNS = "/usr/bin/dnsmasq"
HYDRA_EXEC_NGINX = "/usr/bin/nginx"
HYDRA_USB_DIR = "/sys/bus/usb/devices"
HYDRA_DHCP_DIR = "/var/cache/smd/hydra"
HYDRA_BRIDGE_NETWORK = "172.16.172.0/26"
HYDRA_EXEC_TOKENS = "/usr/bin/websockify"
HYDRA_RESERVE = "/proc/sys/vm/nr_hugepages"
HYDRA_EXEC_VM = "/usr/bin/qemu-system-x86_64"
HYDRA_SMB_FILE = f"{DIRECTORY_HYDRA}/smb.conf"
HYDRA_DNS_FILE = f"{DIRECTORY_HYDRA}/dns.conf"
HYDRA_TOKENS = f"{DIRECTORY_HYDRA}/tokens.sock"
HYDRA_VM_CONFIGS = ["vm.conf", "vm.json", "vmx"]
HYDRA_USB_COMMANDS = ["list", "add", "remove", "del"]
HYDRA_COMMAND_START = bytes('{"execute": "qmp_capabilities"}\r\n', "UTF-8")
HYDRA_SMB_CONFIG = """[global]
workgroup = VM-{name}
server string = VM-{name}
server role = standalone server
hosts allow = {network} 127.0.0.1/32
log file = /dev/null
max log size = 0
bind interfaces only = yes
realm = VM.{name}.COM
passdb backend = tdbsam
interfaces = {ip}/32
wins support = no
wins proxy = no
dns proxy = no
usershare allow guests = no
usershare max shares = 0
[User]
comment = Home Directories
path = /home
guest ok = no
writable = yes
read only = no
printable = no
public = no
[UserRo]
comment = Home Directories Read Only
path = /home
guest ok = no
writable = no
read only = yes
printable = no
public = no
"""
HYDRA_DNS_CONFIG = """port=53
no-hosts
bind-dynamic
expand-hosts
user={user}
group={user}
interface={interface}
listen-address={ip}
resolv-file=/var/run/systemd/resolve/resolv.conf
domain={name}.com,{network}
local=/{name}.com/
address=/vm.{name}.com/{ip}
address=/vm/{ip}
address=/vmhost.{name}.com/{ip}
address=/vmhost/{ip}
address=/hypervisor.{name}.com/{ip}
address=/hypervisor/{ip}
dhcp-lease-max=64
dhcp-option=vendor:MSFT,2,1i
dhcp-option=option:router,{ip}
dhcp-leasefile={dir}/dhcp.leases
dhcp-option=option:ntp-server,{ip}
dhcp-option=option:dns-server,{ip}
dhcp-range={start},{end},{netmask},12h
dhcp-option=option:domain-search,{name}.com
"""

# CPU Module Constants
CPU_PATH = "/sys/devices/system/cpu"
CPU_PATH_MIN = "cpufreq/cpuinfo_min_freq"
CPU_PATH_MAX = "cpufreq/cpuinfo_max_freq"
CPU_PATH_CURRENT = "cpufreq/scaling_cur_freq"
CPU_PATH_GOVERNOR = "cpufreq/scaling_governor"
CPU_PATH_MIN_SCALING = "cpufreq/scaling_min_freq"
CPU_PATH_MAX_SCALING = "cpufreq/scaling_max_freq"
CPU_PATH_GOVERNORS = "cpufreq/scaling_available_governors"
CPU_PATH_PERFORMANCE = "cpufreq/energy_performance_preference"
CPU_PATH_TURBO = "/sys/devices/system/cpu/intel_pstate/no_turbo"
CPU_PATH_TURBO_MIN = "/sys/devices/system/cpu/intel_pstate/min_perf_pct"
CPU_PATH_TURBO_MAX = "/sys/devices/system/cpu/intel_pstate/max_perf_pct"
CPU_PATH_PERFORMANCES = "cpufreq/energy_performance_available_preferences"

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
NOTIFY_ICONS_EXTENSIONS = ["png", "svg", "jpg", "gif"]

# Rotation Module Constants
ROTATE_PATH_STATUS = f"{DIRECTORY_TEMP}/rotate"
ROTATE_PATH_GYROS = "/sys/bus/iio/devices/iio:device*"
ROTATE_PATH_BUTTON = "/dev/input/by-path/pci-0000:00:1f.0-platform-INT33D6:00-event"

ROTATE_LEFT = 0
ROTATE_RIGHT = 1
ROTATE_NORMAL = 2
ROTATE_INVERTED = 3
ROTATE_THRESHOLD = 7.0
ROTATE_ITHRESHOLD = -7.0
ROTATE_DEVICE_NAMES = ["touchscreen", "wacom", "digitizer"]
ROTATE_EXEC_DEVICES = ["/usr/bin/xinput", "--list", "--name-only"]
ROTATE_STATE_NAMES = {
    ROTATE_LEFT: "left",
    ROTATE_RIGHT: "right",
    ROTATE_NORMAL: "normal",
    ROTATE_INVERTED: "inverted",
}
ROTATE_CORD_STATES = {
    ROTATE_LEFT: ["0", "-1", "1", "1", "0", "0", "0", "0", "1"],
    ROTATE_RIGHT: ["0", "1", "0", "-1", "0", "1", "0", "0", "1"],
    ROTATE_NORMAL: ["1", "0", "0", "0", "1", "0", "0", "0", "1"],
    ROTATE_INVERTED: ["-1", "0", "1", "0", "-1", "1", "0", "0", "1"],
}

# Radio Module Constants
RADIO_PATH_WIFI = "/sys/class/net"
RADIO_PATH_BLUE = "/sys/class/bluetooth/*/rfkill*/state"
RADIO_EXEC = {
    "wireless_enable": ["/usr/bin/rfkill unblock wifi"],
    "wireless_disable": ["/usr/bin/rfkill block wifi"],
    "bluetooth_enable": [
        "/usr/bin/rfkill unblock bluetooth",
        "/usr/bin/systemctl start bluetooth.service",
    ],
    "bluetooth_disable": [
        "/usr/bin/systemctl stop bluetooth.service",
        "/usr/bin/rfkill block bluetooth",
    ],
}

# Backup Module Constants
BACKUP_TIMEOUT = 7200
BACKUP_KEY_SIZE = 0xFF
BACKUP_SIZES = "KMGTPEZ"
BACKUP_DEFAULT_PORT = 22
BACKUP_WAIT_TIME = 86400
BACKUP_STATUS_IDLE = 0x00
BACKUP_STATUS_ERROR = 0x0F
BACKUP_STATUS_PACKING = 0x04
BACKUP_STATUS_HASHING = 0x02
BACKUP_STATUS_UPLOADING = 0x05
BACKUP_STATUS_ENCRYPTING = 0x03
BACKUP_STATUS_COMPRESSING = 0x01
BACKUP_DEFAULT_DIR = "/home/smd"
BACKUP_HOSTS = "/etc/smd/backup-hosts.ssh"
BACKUP_STATE_DIR = f"{DIRECTORY_CONFIG}/backup"
BACKUP_STATE = f"{DIRECTORY_CONFIG}/backup-state.json"
BACKUP_BATTERY_PATH = "/sys/class/power_supply/AC/online"
BACKUP_STATUS_NAMES = [
    "idle",
    "compress",
    "hashing",
    "encrypt",
    "packing",
    "upload",
]
BACKUP_EXCLUDE_PATHS = [
    "/dev",
    "/sys",
    "/tmp",
    "/run",
    "/proc",
    "/var/run",
]
BACKUP_RESTORE_SCRIPT = """#!/bin/bash
if [ $# -lt 1 ]; then
    echo "$0 <private_key> [output_dir]"
    exit 1
fi

output="$(pwd)/output"
if [ $# -eq 2 ]; then
    output=$2
fi

keydata=$(openssl pkeyutl -decrypt -inkey "$1" -in "data.pem")
if [ $? -ne 0 ] || [ -z "$keydata" ]; then
    echo "Decryption of key failed!"
    exit 1
fi

echo "Decrypting, please wait..."
printf "$keydata" | openssl aes-256-cbc -a -d -pass stdin -pbkdf2 -in data.ebf -out data.tar.zx
if [ $? -ne 0 ] || [ ! -f "data.tar.zx" ]; then
    echo "Decryption of backup file failed!"
    exit 1
fi

hash_sum=$(sha256sum "data.tar.zx" | awk '{print $1}')
if [ $? -ne 0 ]; then
    echo "File hashing failed!"
    exit 1
fi

hash_orig="$(cat data.sum | awk '{print $1}')"
if [[ "$hash_sum" != "$hash_orig" ]]; then
    echo "Hash sum mismatch!"
    exit 1
fi

echo "Extracting and dumping into \"$output\"..."
mkdir "$output" 12> /dev/null

tar -xf data.tar.zx --zstd -C "$output"
if [ $? -ne 0 ]; then
    echo "Extraction failed!"
    exit 1
fi

echo "Extraction complete."
exit 0
"""

# Background Module Constants
BACKGROUND_PATH_CACHE = "${HOME}/.cache/smd"
BACKGROUND_EXEC_AUTO = f"{DIRECTORY_LIBEXEC}/smd-auto-display"
BACKGROUND_EXEC_SIZE = '/usr/bin/xrandr --query | grep " connected" | grep -o "[0-9][0-9]*x[0-9][0-9]*" | head -1'

# Locker Module Constants
LOCKER_TYPE_LID = "lid"
LOCKER_TYPE_KEY = "key"
LOCKER_TYPE_LOCK = "lock"
LOCKER_TYPE_BLANK = "blank"
LOCKER_TYPE_SUSPEND = "suspend"
LOCKER_TYPE_HIBERNATE = "hibernate"
LOCKER_TYPE_NAMES = {
    LOCKER_TYPE_KEY: "Yubikey",
    LOCKER_TYPE_LID: "Lid Close",
    LOCKER_TYPE_LOCK: "Lock Screen",
    LOCKER_TYPE_BLANK: "Screen Blank",
    LOCKER_TYPE_SUSPEND: "Suspend",
    LOCKER_TYPE_HIBERNATE: "Hibernate",
}

LOCKER_BLANK_TIME = 5
LOCKER_CHECK_TIME = 5
LOCKER_BACKOFF_TIME = 15

LOCKER_TRIGGER_LID = 0x1
LOCKER_TRIGGER_KEY = 0x3
LOCKER_TRIGGER_LOCK = 0x0
LOCKER_TRIGGER_TIMEOUT = 0x2

LOCKER_PATH_STATUS = f"{DIRECTORY_TEMP}/lockers"
LOCKER_PATH_LID = "/proc/acpi/button/lid/LID0/state"
LOCKER_PATH_WAKEALARM = "/sys/class/rtc/rtc0/wakealarm"

LOCKER_EXEC_LOCK = f"{DIRECTORY_LIBEXEC}/smd-locker"
LOCKER_EXEC_SUSPEND = ["/usr/bin/systemctl", "suspend"]
LOCKER_EXEC_HIBERNATE = ["/usr/bin/systemctl", "hibernate"]
LOCKER_EXEC_RESET = f"{DIRECTORY_LIBEXEC}/smd-reset-display"
LOCKER_EXEC_SCREEN_ON = ["/usr/bin/xset", "dpms", "force", "on"]
LOCKER_EXEC_SCREEN_OFF = ["/usr/bin/xset", "dpms", "force", "off"]

# Screen Utility Paths
SCREEN_PATH_ACTIVE = "/sys/class/graphics/fb0/device/drm/card*/card*/enabled"
SCREEN_PATH_CONNECTED = "/sys/class/graphics/fb0/device/drm/card*/card*/status"

__init__(CONFIG_CONSTANTS)

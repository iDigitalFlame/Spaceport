#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# The Constants Python file is to hold and save basic defaults that may be used in the
# executiton of the System Management Daemon.
# This file is saved/loaded to "/opt/spaceport/config/smd-constants.json" as a JSON file.
# These paramaters are updated and saved to the file when it does not exist.
# The file paramaters are loaded from the file when it exists and will only fill in non-defaults.
# Updated 10/2018

from os.path import join, isfile
from importlib import import_module
from lib.util import read_json, write_json


def _init(config_file):
    vars_instance = import_module(__name__)
    if not isfile(config_file):
        vars_dict = dict()
        for var_name, var_value in vars_instance.__dict__.items():
            if (
                var_name is not None
                and len(var_name) > 0
                and var_name[0] != "_"
                and var_name.isupper()
            ):
                vars_dict[var_name.lower()] = var_value
        write_json(config_file, vars_dict, indent=4, sort=True, ignore_errors=True)
        del vars_dict
    else:
        vars_dict = read_json(config_file, ignore_errors=True)
        if isinstance(vars_dict, dict):
            for var_name, var_value in vars_dict.items():
                try:
                    setattr(vars_instance, var_name.upper(), var_value)
                except AttributeError:
                    pass
        del vars_dict
    del vars_instance


EMPTY = str()
VERSION = "SMD-2.6r"
BOOLEANS = ["0", "1", "true", "false", "on", "off"]

NAME_BASE = "spaceport"
NAME_POWERCTL = "powerctl"
NAME_CLIENT = "SystemManagementClient"
NAME_SERVER = "SystemManagementDaemon"

DIRECTORY_TEMP = "/var/run"
DIRECTORY_TEMP_CLIENT = "/tmp"
DIRECTORY_BASE = join("/opt", NAME_BASE)
DIRECTORY_BIN = join(DIRECTORY_BASE, "bin")
DIRECTORY_LIB = join(DIRECTORY_BASE, "lib")
DIRECTORY_HYRDA = join(DIRECTORY_TEMP, "hydra")
DIRECTORY_CONFIG = join(DIRECTORY_BASE, "config")
DIRECTORY_MODULES = join(DIRECTORY_LIB, "modules")
DIRECTORY_LIBEXEC = join(DIRECTORY_BASE, "libexec")
DIRECTORY_POWERCTL = join(DIRECTORY_LIB, "powerctl")

SOCKET_BACKLOG = 512
SOCKET_MESSAGE_INTEGER_SIZE = 4
SOCKET = join("/var/run", "smd-%s.sock" % NAME_BASE)

CONFIG_CLIENT = "{home}/.config/smd-config.json"
CONFIG_SERVER = join(DIRECTORY_CONFIG, "smd-config.json")

HOOK_LOCK = "com.%s.lock" % NAME_BASE
HOOK_HYDRA = "com.%s.hydra" % NAME_BASE
HOOK_TABLET = "com.%s.mode" % NAME_BASE
HOOK_POWER = "com.%s.power" % NAME_BASE
HOOK_RELOAD = "com.%s.reload" % NAME_BASE
HOOK_DAEMON = "com.%s.daemon" % NAME_BASE
HOOK_ROTATE = "com.%s.rotate" % NAME_BASE
HOOK_UPDATE = "com.%s.update" % NAME_BASE
HOOK_MONITOR = "com.%s.monitor" % NAME_BASE
HOOK_HIBERNATE = "com.%s.sleep" % NAME_BASE
HOOK_STARTUP = "com.%s.startup" % NAME_BASE
HOOK_SHUTDOWN = "com.%s.shutdown" % NAME_BASE
HOOK_NOTIFICATION = "com.%s.notify" % NAME_BASE
HOOK_BACKGROUND = "com.%s.background" % NAME_BASE

LOG_PAYLOAD = False
LOG_LEVEL = "WARNING"
LOG_FILE_SERVER = join(DIRECTORY_TEMP, "smd-%s-server.log" % NAME_BASE)
LOG_FILE_CLIENT = join(DIRECTORY_TEMP_CLIENT, "smd-%s-client-{pid}.log" % NAME_BASE)
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

HYRDA_UID = "kvm"
HYDRA_BRIDGE = "vmi0"
HYDRA_EXEC_SMB = "/usr/bin/smbd"
HYDRA_USB_DEVICES = "/dev/bus/usb"
HYDRA_EXEC_DNS = "/usr/bin/dnsmasq"
HYDRA_EXEC_NGINX = "/usr/bin/nginx"
HYDRA_DHCP_DIR = "/var/cache/hydra"
HYDRA_USB_DIR = "/sys/bus/usb/devices"
HYDRA_BRIDGE_NAME = "vm.%s" % NAME_BASE
HYDRA_BRIDGE_NETWORK = "172.16.172.0/26"
HYDRA_EXEC_VM = "/usr/bin/qemu-system-x86_64"
HYDRA_VM_CONFIGS = ["vm.conf", "vm.json", "vmx"]
HYDRA_SMB_FILE = join(DIRECTORY_HYRDA, "smb.conf")
HYDRA_DNS_FILE = join(DIRECTORY_HYRDA, "dns.conf")
HYDRA_TOKENS = join(DIRECTORY_HYRDA, "tokens.sock")
HYDRA_BROWSER_COMMAND = ["/usr/bin/surf", "-pmKBSngD"]
HYDRA_EXEC_TOKENS = join(DIRECTORY_CONFIG, "hydra/websockify/run")
HYDRA_VNC_COMMAND = ["/usr/bin/vncviewer", "FullscreenSystemKeys=0"]
HYDRA_COMMAND_START = bytes('{"execute": "qmp_capabilities"}\r\n', "UTF-8")
HYDRA_POWERCTL_COMMANDS = ["usb", "start", "stop", "connect", "list", "name"]
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
 public = no"""
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
address=/vmhost.{name}.com/{ip}
address=/vmhost/{ip}
address=/hypervisor.{name}/{ip}
address=/hypervisor/{ip}
dhcp-lease-max=64
dhcp-option=vendor:MSFT,2,1i
dhcp-option=option:router,{ip}
dhcp-leasefile={dir}/dhcp.leases
dhcp-option=option:ntp-server,{ip}
dhcp-option=option:dns-server,{ip}
dhcp-range={start},{end},{netmask},12h
dhcp-option=option:domain-search,{name}.com"""

CPU_MIN_FREQ = "cpufreq/cpuinfo_min_freq"
CPU_MAX_FREQ = "cpufreq/cpuinfo_max_freq"
CPU_DIRECTORY = "/sys/devices/system/cpu"
CPU_CURRENT_FREQ = "cpufreq/scaling_cur_freq"
CPU_SCALING_MIN_FREQ = "cpufreq/scaling_min_freq"
CPU_SCALING_MAX_FREQ = "cpufreq/scaling_max_freq"
CPU_SCALING_GOVERNOR = "cpufreq/scaling_governor"
CPU_STATE = join(DIRECTORY_CONFIG, "smd-cpu.json")
CPU_GOVERNORS_AVAILABLE = "cpufreq/scaling_available_governors"
CPU_PERFORMANCE_STATE = "cpufreq/energy_performance_preference"
CPU_PSTATE_TURBO = "/sys/devices/system/cpu/intel_pstate/no_turbo"
CPU_PSTATE_TURBO_MIN = "/sys/devices/system/cpu/intel_pstate/min_perf_pct"
CPU_PSTATE_TURBO_MAX = "/sys/devices/system/cpu/intel_pstate/max_perf_pct"
CPU_PERFORMANCE_STATE_AVAILABLE = "cpufreq/energy_performance_available_preferences"

BRIGHTNESS_FILE = "/sys/class/backlight/intel_backlight/brightness"
BRIGHTNESS_FILE_MAX = "/sys/class/backlight/intel_backlight/max_brightness"

TABLET_STATE_CLOSED = 0
TABLET_STATE_LAPTOP = 1
TABLET_STATE_TABLET = 2
TABLET_LID_FILE = "/proc/acpi/button/lid/LID0/state"
TABLET_STATUS_GLOB = "/sys/class/graphics/fb0/device/drm/card*/card*/status"
TABLET_DISPLAY_GLOB = "/sys/class/graphics/fb0/device/drm/card*/card*/enabled"
TABLET_EVENT_FILE = "/dev/input/by-path/pci-0000:00:1f.0-platform-INT33D6:00-event"

NOTIFY_ICONS = {
    "error": "/usr/share/icons/Flat-Remix-Dark/status/scalable/dialog-error.png",
    "warn": "/usr/share/icons/Flat-Remix-Dark/status/scalable/dialog-warning.png",
    "warning": "/usr/share/icons/Flat-Remix-Dark/status/scalable/dialog-warning.png",
    "info": "/usr/share/icons/Flat-Remix-Dark/status/scalable/dialog-information.svg",
    "question": "/usr/share/icons/Flat-Remix-Dark/status/scalable/dialog-question.png",
}
NOTIFY_ICON_DEFAULT = "stock_dialog-info.png"
NOTIFY_ICON_EXTENSIONS = ["png", "svg", "jpg", "gif"]
NOTIFY_ICON_BASE = "/usr/share/icons/Flat-Remix-Dark/apps/scalable/"

ROTATION_CORD_STATES = {
    "left": ["0", "-1", "1", "1", "0", "0", "0", "0", "1"],
    "normal": ["1", "0", "0", "0", "1", "0", "0", "0", "1"],
    "right": ["0", "1", "0", "-1", "0", "1", "0", "0", "1"],
    "inverted": ["-1", "0", "1", "0", "-1", "1", "0", "0", "1"],
}
ROTATION_THREASHOLD = 7.0
ROTATION_THREASHOLD_NEG = -7.0
ROTATION_GYROS = "/sys/bus/iio/devices/iio:device*"
ROTATION_LOCK_STATUS = "/var/run/smd-rotate-lock.sock"
ROTATION_DEVICES = ["/usr/bin/xinput", "--list", "--name-only"]

WIRELESS_COMMANDS = {
    "wireless_enable": ["/usr/bin/rfkill unblock wifi"],
    "wireless_disable": ["/usr/bin/rfkill block wifi"],
    "bluetooth_enable": [
        "/usr/bin/rfkill unblock bluetooth",
        "/usr/bin/rfkill unblock bluetooth",
        "/usr/bin/systemctl start bluetooth.service",
    ],
    "bluetooth_disable": [
        "/usr/bin/systemctl stop bluetooth.service",
        "/usr/bin/rfkill block bluetooth",
        "/usr/bin/rfkill block bluetooth",
    ],
}
WIRELESS_WIFI_DEVICES = "/sys/class/net"
WIRELESS_BLUE_DEVICES = "/sys/class/bluetooth"

BACKGROUND_DIRECTORY_CACHE = ".cache/smd-client"
BACKGROUND_LOCKSCREEN = ".config/smd-lockscreen.png"
BACKGROUND_DIRECTORY_DEFAULT = "{home}/Pictures/Backgrounds"
BACKGROUND_SIZE = '/usr/bin/xrandr --query | grep " connected" | grep -o "[0-9][0-9]*x[0-9][0-9]*" | head -1'
BACKGROUND_STANDARD = [
    "/usr/bin/feh",
    "--no-fehbg",
    "--bg-fill",
    "--randomize",
    "/usr/share/archlinux/wallpaper/*",
]

LOCKER_LID = "lid"
LOCKER_BLANK = "blank"
LOCKER_BLANK_DEFAULT = 60
LOCKER_SLEEP_DEFAULT = 120
LOCKER_LOCK_BLANK_DEFAULT = 5
LOCKER_HIBERNATE = "hibernate"
LOCKER_LOCK_SCREEN = "lock-screen"
LOCKER_LOCK_DEFAULT = ["/usr/bin/i3lock", "-n"]
LOCKER_STATUS_FILE = "/var/run/smd-lockers.sock"
LOCKER_QUERY = {"type": "locker", "action": "get"}
LOCKER_EXEC_HIBERNATE = ["/usr/bin/systemctl", "hibernate"]
LOCKER_SCREEN_ON = ["/usr/bin/xset", "dpms", "force", "on"]
LOCKER_CONTROL_QUERY = {"type": "locker", "action": "query"}
LOCKER_SCREEN_OFF = ["/usr/bin/xset", "dpms", "force", "off"]
LOCKER_NAMES = {
    LOCKER_LID: "Lid",
    LOCKER_HIBERNATE: "Sleep",
    LOCKER_BLANK: "Display Blank",
    LOCKER_LOCK_SCREEN: "Lockscreen",
}

POLYBAR_DEFAULT = {"laptop": "laptop", "tablet": "tablet"}

SESSION_DEFAULT_LOCK = 120
SESSION_DEFAULT_BACKGROUND = 600
SESSION_NETWORK = ["/usr/bin/nm-applet"]
SESSION_COMPOSER = ["/usr/bin/compton", "-cd", ":1"]
SESSION_PROFILES = {
    "power-ac": list(),
    "power-battery": list(),
    "mode-tablet": list(),
    "mode-laptop": list(),
    "rotate": list(),
    "display": list(),
    "lock-pre": list(),
    "lock-post": list(),
    "sleep-post": list(),
    "sleep-pre": list(),
}

_init("/opt/spaceport/config/smd-constants.json")

# EOF

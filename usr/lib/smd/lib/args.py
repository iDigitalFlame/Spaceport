#!/usr/bin/false
################################
### iDigitalFlame  2016-2025 ###
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
# Copyright (C) 2016 - 2025 iDigitalFlame
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

# args.py
#   This is the static arguments and descriptions storage file. This stores some
#   of the static content that can be dynamically loaded by the powerctl loader.

from lib.constants import BOOLEANS

ARGS = {
    "cpu": [
        (
            ("-a", "--advanced"),
            {
                "dest": "advanced",
                "help": "display detailed CPU information",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-g", "--governor"),
            {
                "type": str,
                "dest": "governor",
                "help": "set the CPU governor",
                "action": "store",
                "metavar": "governor",
                "required": False,
            },
            "config",
        ),
        (
            ("-m", "--min"),
            {
                "type": str,
                "dest": "minimum",
                "help": "set the minimum CPU frequency",
                "action": "store",
                "metavar": "frequency",
                "required": False,
            },
            "config",
        ),
        (
            ("-x", "--max"),
            {
                "type": str,
                "dest": "maximum",
                "help": "set the maximum CPU frequency",
                "action": "store",
                "metavar": "frequency",
                "required": False,
            },
            "config",
        ),
        (
            ("-p", "--power"),
            {
                "type": str,
                "dest": "power_governor",
                "help": "set the CPU power governor",
                "action": "store",
                "metavar": "power_governor",
                "required": False,
            },
            "config",
        ),
        (
            ("-t", "--turbo"),
            {
                "type": str,
                "dest": "turbo",
                "help": "enable or disable CPU turbo mode",
                "action": "store",
                "metavar": "turbo",
                "choices": BOOLEANS,
                "required": False,
            },
            "config",
        ),
        (
            ("-tm", "--turbo-min"),
            {
                "type": str,
                "dest": "turbo_minimum",
                "help": "set the CPU turbo driver minimum percentage",
                "action": "store",
                "metavar": "percentage",
                "required": False,
            },
            "config",
        ),
        (
            ("-tx", "--turbo-max"),
            {
                "type": str,
                "action": "store",
                "dest": "turbo_maximum",
                "help": "set the CPU turbo driver maximum percentage",
                "metavar": "percentage",
                "required": False,
            },
            "config",
        ),
        (
            ("-s", "--step"),
            {
                "dest": "step",
                "help": "set the maximum CPU frequency after setting turbo (implies -t)",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-n", "--select"),
            {
                "type": str,
                "dest": "selector",
                "help": "filter to specific CPU(s) (name, number or comma separated)",
                "action": "store",
                "metavar": "selector",
                "required": False,
            },
        ),
        (
            ("-w", "--wait"),
            {
                "dest": "wait",
                "help": "display CPU details after setting",
                "action": "store_true",
                "required": False,
            },
        ),
    ],
    "log": [
        (
            ("-l", "--level"),
            {
                "type": str,
                "dest": "level",
                "help": "set the log level to use (temporary, 0 [debug] - 4 [critical])",
                "action": "store",
                "metavar": "level",
                "required": True,
            },
        ),
    ],
    "blue": [
        (
            ("-d", "--disable"),
            {
                "dest": "disable",
                "help": "disable Bluetooth",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-e", "--enable"),
            {
                "dest": "enable",
                "help": "enable Bluetooth",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-t", "--toggle"),
            {
                "dest": "toggle",
                "help": "toggle Bluetooth",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-b", "--boot"),
            {
                "type": str,
                "dest": "boot",
                "help": "set the Bluetooth boot state",
                "required": False,
                "action": "store",
                "metavar": "boot",
                "choices": BOOLEANS,
            },
            "config",
        ),
        (
            ("-f", "--force"),
            {
                "dest": "force",
                "help": "force enable/disable Bluetooth regardless of current state",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-s", "--status"),
            {
                "dest": "status",
                "help": "show the current Bluetooth boot and enabled state",
                "action": "store_true",
                "required": False,
            },
            "status",
        ),
        (
            "command",
            {
                "help": "bluetooth commands",
                "nargs": "?",
                "action": "store",
                "default": None,
                "choices": BOOLEANS + ["set", "boot"],
            },
            "command",
        ),
        (
            "args",
            {
                "nargs": "*",
                "help": "optional arguments",
                "action": "store",
                "default": None,
            },
        ),
    ],
    "wifi": [
        (
            ("-d", "--disable"),
            {
                "dest": "disable",
                "help": "disable Wireless",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-e", "--enable"),
            {
                "dest": "enable",
                "help": "enable Wireless",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-t", "--toggle"),
            {
                "dest": "toggle",
                "help": "toggle Wireless",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-b", "--boot"),
            {
                "type": str,
                "dest": "boot",
                "help": "set the Wireless boot state",
                "action": "store",
                "metavar": "boot",
                "choices": BOOLEANS,
                "required": False,
            },
            "config",
        ),
        (
            ("-f", "--force"),
            {
                "dest": "force",
                "help": "force enable/disable Wireless regardless of current state",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-s", "--status"),
            {
                "dest": "status",
                "help": "show the current Wireless boot and enabled state",
                "action": "store_true",
                "required": False,
            },
            "status",
        ),
        (
            "command",
            {
                "help": "wireless commands",
                "nargs": "?",
                "action": "store",
                "default": None,
                "choices": BOOLEANS + ["set", "boot"],
            },
            "command",
        ),
        (
            "args",
            {
                "help": "Optional arguments",
                "nargs": "*",
                "action": "store",
                "default": None,
            },
        ),
    ],
    "lock": [
        (
            ("-f", "--force"),
            {
                "dest": "force",
                "help": "force Lockscreen and override lockers",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-t", "--suspend"),
            {
                "type": str,
                "dest": "suspend",
                "help": "set the Suspend timeout (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
        ),
        (
            ("-kt", "--suspend-force"),
            {
                "type": str,
                "dest": "suspend_force",
                "help": "force set the Suspend timeout (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
        ),
        (
            ("-z", "--hibernate"),
            {
                "type": str,
                "dest": "hibernate",
                "action": "store",
                "metavar": "seconds",
                "help": "set the Hibernate timeout (seconds / true [until reboot] / false [disable])",
                "required": False,
            },
        ),
        (
            ("-kz", "--hibernate-force"),
            {
                "type": str,
                "dest": "hibernate_force",
                "help": "force set the Hibernate timeout (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
        ),
        (
            "timeout",
            {
                "help": "set the Suspend timeout (seconds / true [until reboot] / false [disable])",
                "nargs": "?",
                "action": "store",
                "default": None,
            },
        ),
    ],
    "hydra": [
        (
            ("-l", "--list"),
            {
                "dest": "list",
                "help": "list running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_list",
        ),
        (
            ("-i", "--id"),
            {
                "type": int,
                "dest": "vmid",
                "help": "VMID of VM to select",
                "action": "store",
                "metavar": "vmid",
                "required": False,
            },
        ),
        (
            ("-n", "--name"),
            {
                "type": str,
                "dest": "name",
                "help": "name or path of VM to select",
                "action": "store",
                "metavar": "name",
                "required": False,
            },
        ),
        (
            ("-d", "--dir"),
            {
                "dest": "directory",
                "type": str,
                "help": "set the user VM search directory",
                "action": "store",
                "metavar": "dir",
                "required": False,
            },
            "user_directory",
        ),
        (
            ("-a", "--alias-add"),
            {
                "dest": "alias_add",
                "type": str,
                "help": "add an alias to the selected VM",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "user_alias",
        ),
        (
            ("-ar", "--alias-del"),
            {
                "dest": "alias_delete",
                "type": str,
                "help": "remove an alias from the selected VM",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "user_alias",
        ),
        (
            ("-T", "--tap"),
            {
                "dest": "tap",
                "help": "tap the VM power button",
                "action": "store_true",
                "required": False,
            },
            "vm_tap",
        ),
        (
            ("-sl", "--snaps"),
            {
                "dest": "snaps",
                "help": "list the Snapshots for the selected VM",
                "action": "store_true",
                "required": False,
            },
            "vm_snap_list",
        ),
        (
            ("-st", "--snap-take"),
            {
                "dest": "snap",
                "type": str,
                "help": "take a Snapshot of the selected VM",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "vm_snap",
        ),
        (
            ("-sr", "--snap-restore"),
            {
                "dest": "snap_restore",
                "type": str,
                "help": "restore a Snapshot of the selected VM",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "vm_snap_restore",
        ),
        (
            ("-sd", "--snap-del"),
            {
                "dest": "snap_delete",
                "type": str,
                "help": "delete a Snapshot of the selected VM",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "vm_snap_delete",
        ),
        (
            ("-x", "--stop"),
            {
                "dest": "stop",
                "help": "softly stop the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_stop",
        ),
        (
            ("-xa", "--stop-all"),
            {
                "dest": "all_stop",
                "help": "stop all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            ("-f", "--stop-force"),
            {
                "dest": "stop_force",
                "help": "force poweroff (halt) the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_stop",
        ),
        (
            ("-fa", "--stop-force-all"),
            {
                "dest": "all_force",
                "help": "force poweroff (halt) all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            ("-t", "--timeout"),
            {
                "type": int,
                "dest": "timeout",
                "help": 'optional shutdown timeout, ignored using "-f"',
                "action": "store",
                "metavar": "timeout",
                "default": 90,
                "required": False,
            },
        ),
        (
            ("-s", "--start"),
            {
                "dest": "start",
                "help": "start the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_start",
        ),
        (
            "--debug",
            {
                "dest": "debug",
                "help": "temporarily enable the debug flag when starting the VM",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "--temp",
            {
                "dest": "temp",
                "help": "use temporary disks when starting the VM (no changes saved)",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-r", "--restart"),
            {
                "dest": "restart",
                "help": "restart the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_restart",
        ),
        (
            ("-ra", "--restart-all"),
            {
                "dest": "all_restart",
                "help": "restart all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            ("-R", "--reset"),
            {
                "dest": "reset",
                "help": "force reset the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_restart",
        ),
        (
            ("-Ra", "--reset-all"),
            {
                "dest": "all_reset",
                "help": "force reset all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            ("-q", "--hibernate"),
            {
                "dest": "hibernate",
                "help": "hibernate (suspend to disk) the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_hibernate",
        ),
        (
            ("-qa", "--hibernate-all"),
            {
                "dest": "all_hibernate",
                "help": "hibernate (suspend to disk) all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            ("-ul", "--usbs"),
            {
                "dest": "usb_list",
                "help": "list USB devices connected to the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb_list",
        ),
        (
            ("-u", "--usb-add"),
            {
                "dest": "usb_add",
                "help": "connect a USB device to the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb",
        ),
        (
            ("-ur", "--usb-del"),
            {
                "dest": "usb_delete",
                "help": "disconnect a USB device from the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb",
        ),
        (
            ("-un", "--usb-name"),
            {
                "type": str,
                "dest": "usb_name",
                "help": "name of USB device to select",
                "action": "store",
                "metavar": "name",
                "required": False,
            },
        ),
        (
            ("-ui", "--usb-id"),
            {
                "type": int,
                "dest": "usb_id",
                "help": "USB device ID to select",
                "action": "store",
                "metavar": "id",
                "required": False,
            },
        ),
        (
            ("-uv", "--vendor"),
            {
                "type": str,
                "dest": "usb_vendor",
                "help": "USB device vendor ID to select",
                "action": "store",
                "metavar": "vendor",
                "required": False,
            },
        ),
        (
            ("-up", "--product"),
            {
                "type": str,
                "dest": "usb_product",
                "help": "USB device product ID to select",
                "action": "store",
                "metavar": "product",
                "required": False,
            },
        ),
        (
            ("-uc", "--usb-clean"),
            {
                "dest": "usb_clean",
                "help": "remove all USB devices connected to the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb_clean",
        ),
        (
            ("-uu", "--usb-reconnect"),
            {
                "dest": "usb_reconnect",
                "help": "reconnect all USB devices connected to the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb_reconnect",
        ),
        (
            "--usb2",
            {
                "dest": "usb_slow",
                "help": "use the USB2.0 bus instead of USB3.0 (default is 3.0)",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-k", "--input"),
            {
                "type": str,
                "dest": "input",
                "help": "keyboard input to send to the VM",
                "action": "store",
                "metavar": "keys",
                "required": False,
            },
            "vm_input",
        ),
        (
            "--caps",
            {
                "dest": "use_caps",
                "help": "use the caps_lock key instead of shift for uppercase characters",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            ("-c", "--connect"),
            {
                "dest": "connect",
                "help": "connect to the selected VM",
                "action": "store_true",
                "required": False,
            },
            "vm_connect",
        ),
        (
            ("-cv", "--vnc"),
            {
                "dest": "connect_vnc",
                "help": "connect to the selected VM (using VNC)",
                "action": "store_true",
                "required": False,
            },
            "vm_connect",
        ),
        (
            "--no-fork",
            {
                "dest": "no_fork",
                "help": "do not fork when connecting to a VM",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-w", "--wake"),
            {
                "dest": "wake",
                "help": "resume the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_sleep",
        ),
        (
            ("-wa", "--wake-all"),
            {
                "dest": "all_wake",
                "help": "resume all suspended VMs",
                "required": False,
                "action": "store_true",
            },
            "vm_all",
        ),
        (
            ("-z", "--suspend"),
            {
                "dest": "sleep",
                "help": "suspend the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_sleep",
        ),
        (
            ("-za", "--suspend-all"),
            {
                "dest": "all_sleep",
                "help": "suspend all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            ("-es", "--schema"),
            {
                "dest": "schema",
                "help": "output the VM config file schema",
                "action": "store_true",
                "required": False,
            },
            "example",
        ),
        (
            ("-e", "--example"),
            {
                "dest": "example",
                "help": "output a VM config file example",
                "action": "store_true",
                "required": False,
            },
            "example",
        ),
        (
            ("-p", "--ping"),
            {
                "dest": "ga_ping",
                "help": "check the status of the QEMU Guest Agent",
                "action": "store_true",
                "required": False,
            },
            "vm_ping",
        ),
        (
            ("-I", "--ifconfig"),
            {
                "dest": "ga_ip",
                "help": "retrive the VM IP addresses using the QEMU Guest Agent",
                "action": "store_true",
                "required": False,
            },
            "vm_ip",
        ),
        (
            "--dmenu",
            {
                "dest": "dmenu",
                "help": "list output in a dmenu compatible format",
                "action": "store_true",
                "required": False,
            },
            "vm_list",
        ),
        (
            "command",
            {
                "help": "command to execute",
                "nargs": "?",
                "action": "store",
                "default": None,
            },
            "tokenize",
        ),
        (
            "args",
            {
                "nargs": "*",
                "default": None,
                "action": "store",
                "help": "optional arguments",
            },
        ),
    ],
    "locker": [
        (
            ("-b", "--blank"),
            {
                "type": str,
                "dest": "blank",
                "help": "set the Blank inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-kb", "--blank-force"),
            {
                "type": str,
                "dest": "blank_force",
                "help": "force set the Blank inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-l", "--lockscreen"),
            {
                "type": str,
                "dest": "lockscreen",
                "help": "set the Lockscreen inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-kl", "--lockscreen-force"),
            {
                "type": str,
                "dest": "lockscreen_force",
                "help": "force set the Lockscreen inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-s", "--suspend"),
            {
                "type": str,
                "dest": "suspend",
                "help": "set the Suspend inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-ks", "--suspend-force"),
            {
                "type": str,
                "dest": "suspend_force",
                "help": "force set the Suspend inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-z", "--hibernate"),
            {
                "type": str,
                "dest": "hibernate",
                "help": "set the Hibernate inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-kz", "--hibernate-force"),
            {
                "type": str,
                "dest": "hibernate_force",
                "help": "force set the Hibernate inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-d", "--lid"),
            {
                "type": str,
                "dest": "lid",
                "help": "set the Lid inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-kd", "--lid-force"),
            {
                "type": str,
                "dest": "lid_force",
                "help": "force set the Lid inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-y", "--key"),
            {
                "type": str,
                "dest": "key",
                "help": "set the Key inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-ky", "--key-force"),
            {
                "type": str,
                "dest": "key_force",
                "help": "force set the Key inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-f", "--freeze"),
            {
                "type": str,
                "dest": "freeze",
                "help": "set the App Freeze inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-kf", "--freeze-force"),
            {
                "type": str,
                "dest": "freeze_force",
                "help": "force set the App Freeze inhibitor time (seconds / true [until reboot] / false [disable])",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            ("-C", "--clean"),
            {
                "dest": "clear",
                "help": "clear all current inhibitors",
                "action": "store_true",
                "required": False,
            },
            "clear",
        ),
    ],
    "backup": [
        (
            ("-l", "--list"),
            {
                "dest": "list",
                "help": "list backup plans",
                "action": "store_true",
                "required": False,
            },
            "default",
        ),
        (
            ("-a", "--advanced"),
            {
                "dest": "advanced",
                "help": "display detailed backup plan information",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-s", "--start"),
            {
                "dest": "start",
                "help": "start a backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-F", "--full"),
            {
                "dest": "full",
                "help": "force a full backup instead of the current state",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-x", "--stop"),
            {
                "dest": "stop",
                "help": "stop a backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-p", "--pause"),
            {
                "dest": "pause",
                "help": "pause a running backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-r", "--resume"),
            {
                "dest": "resume",
                "help": "resume a paused backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-f", "--force"),
            {
                "dest": "force",
                "help": "force a backup to start, even on battery",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-R", "--retry-failed"),
            {
                "dest": "retry",
                "help": "retry all failed backups",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-C", "--clear"),
            {
                "dest": "clear",
                "help": "clear backup database cache",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            ("-L", "--entries"),
            {
                "dest": "entries",
                "help": "show the files inside the specified backup tar",
                "action": "store_true",
                "required": False,
            },
            "entries",
        ),
        (
            ("-E", "--extract"),
            {
                "dest": "extract",
                "help": "extract the files from the specified backup tar",
                "action": "store_true",
                "required": False,
            },
            "extract",
        ),
        (
            ("-k", "--key"),
            {
                "type": str,
                "dest": "key",
                "help": "path to the backup private key for extracting and entries",
                "action": "store",
                "metavar": "key",
                "required": False,
            },
        ),
        (
            ("-d", "--dir"),
            {
                "type": str,
                "dest": "dir",
                "help": "select the backup target path or output dir when extracting",
                "action": "store",
                "metavar": "dir",
                "required": False,
            },
            "config",
        ),
        (
            "path",
            {
                "help": "backup target path",
                "nargs": "?",
                "action": "store",
                "default": None,
            },
            "config",
        ),
        (
            "files",
            {
                "nargs": "*",
                "default": None,
                "action": "store",
                "help": "files to extract from backup (accepts wildcards)",
            },
        ),
    ],
    "reload": [
        (
            ("-a", "--all"),
            {
                "dest": "all",
                "help": "reload all system and user services",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-f", "--force"),
            {
                "dest": "force",
                "help": "do not prompt for conrifmation",
                "action": "store_true",
                "required": False,
            },
        ),
    ],
    "brightness": [
        (
            ("-i", "--increase"),
            {
                "dest": "increase",
                "help": "increase the current Brightness level by 5%",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-d", "--decrease"),
            {
                "dest": "decrease",
                "help": "decrease the current Brightness level by 5%",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            ("-s", "--set"),
            {
                "type": str,
                "dest": "brightness",
                "help": "set the current Brightness level",
                "action": "store",
                "metavar": "level",
                "required": False,
            },
        ),
        (
            "level",
            {
                "nargs": "?",
                "help": "set the current Brightness level",
                "action": "store",
                "default": None,
            },
        ),
    ],
}
DESCRIPTIONS = {
    "cpu": "Processor Management Module",
    "log": "Logging Management Module",
    "blue": "Bluetooth Management Module",
    "wifi": "Wireless Management Module",
    "lock": "Lockscreen Management Module",
    "hydra": "Hydra Hypervisor Management Module",
    "locker": "Locker Management Module",
    "backup": "Backup Management Module",
    "reload": "Configuration Reload Management Module",
    "brightness": "Display Brightness Management Module",
}

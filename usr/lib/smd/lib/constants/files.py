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

# files.py
#   Constants Values for: Files
#
#   Contains constants that are not user configurable and represent file data that
#   SMD may generate during runtime.

HYDRA_CONFIG_DNS = """port=53
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
HYDRA_CONFIG_SMB = """[global]
workgroup = VM-{name}
server string = VM-{name}
server role = standalone server
hosts allow = {network} 127.0.0.1/32
log file = /dev/null
log level = 0
logging =
max log size = 0
bind interfaces only = yes
realm = VM.{name}.COM
passdb backend = tdbsam
interfaces = {ip}/32
wins support = no
wins proxy = no
dns proxy = no
eventlog list =
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
follow symlinks = yes
[UserRo]
comment = Home Directories Read Only
path = /home
guest ok = no
writable = no
read only = yes
printable = no
public = no
follow symlinks = no
"""

BACKUP_RESTORE_SCRIPT = """#!/bin/bash
set -u

if [ $# -lt 1 ]; then
    echo "$0 <private_key> [output_dir]"
    exit 1
fi
if ! [ -e "$1" ]; then
    printf 'Private key "%s" does not exist!\\n' "$1"
    exit 1
fi

output="$(pwd)/output"
if [ $# -eq 2 ]; then
    output="$2"
else
    output="$(pwd)/output"
fi
if ! mkdir -p "$output" 2> /dev/null; then
    printf 'Cannot use or make output directory "%s"!\\n' "$output"
    exit 1
fi

hash=$(sha256sum "data.pak" | awk '{print $1}')
if [ $? -ne 0 ]; then
    echo "File hashing failed!"
    exit 1
fi
if [[ "$hash" != "$(cat data.sum | awk '{print $1}')" ]]; then
    echo "Hash sum mismatch!"
    exit 1
fi

key=$(openssl pkeyutl -decrypt -inkey "$1" -in "data.pem" -out -)
if [ $? -ne 0 ] || [ -z "$key" ]; then
    printf 'Decryption using key "%s" failed!\\n' "$1"
    exit 1
fi

printf 'Decrypting and extracing into "%s", please wait..\\n' "$output"
env key="$key" openssl aes-256-ctr -d -pass env:key -pbkdf2 -in data.pak -out - | tar -xf - --zstd -C "$output"

r=$?
unset key

if [ $r -ne 0 ]; then
    echo "Decryption and extraction of backup file failed!"
    exit 1
fi

echo "Extraction complete."
exit 0
"""
BACKUP_RESTORE_SCRIPT_NO_KEY = """#!/bin/bash
set -u

output="$(pwd)/output"
if [ $# -eq 1 ]; then
    output="$1"
else
    output="$(pwd)/output"
fi
if ! mkdir -p "$output" 2> /dev/null; then
    printf 'Cannot use or make output directory "%s"!\\n' "$output"
    exit 1
fi

hash=$(sha256sum "data.pak" | awk '{print $1}')
if [ $? -ne 0 ]; then
    echo "File hashing failed!"
    exit 1
fi
if [[ "$hash" != "$(cat data.sum | awk '{print $1}')" ]]; then
    echo "Hash sum mismatch!"
    exit 1
fi

printf 'Extracing into "%s", please wait..\\n' "$output"
if ! tar -xf "data.pak" --zstd -C "$output"; then
    echo "Extraction of backup file failed!"
    exit 1
fi

echo "Extraction complete."
exit 0
"""

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
bind-dynamic
expand-hosts
no-hosts
group={user}
interface={interface}
listen-address={ip}
resolv-file=/var/run/systemd/resolve/resolv.conf
user={user}
domain={name}.com,{network}
local=/{name}.com/
address=/vm.{name}.com/{ip}
address=/vm/{ip}
address=/vmhost.{name}.com/{ip}
address=/vmhost/{ip}
address=/hypervisor.{name}.com/{ip}
address=/hypervisor/{ip}
dhcp-lease-max=64
dhcp-leasefile={dir}/dhcp.leases
dhcp-option=vendor:MSFT,2,1i
dhcp-option=option:router,{ip}
dhcp-option=option:ntp-server,{ip}
dhcp-option=option:dns-server,{ip}
dhcp-option=option:domain-search,{name}.com
dhcp-range={start},{end},{netmask},12h
"""
HYDRA_CONFIG_SMB = """[global]
allow dns updates = disabled
allow insecure wide links = no
async smb echo handler = no
bind interfaces only = yes
browse list = no
change notify = yes
config backend = file
create krb5 conf = no
debug class = no
debug encryption = no
debug pid = no
debug uid = no
disable netbios = yes
dns proxy = no
enable asu support = no
enable core files = no
enable spoolss = no
eventlog list =
guest account = nobody
host msdfs = no
hostname lookups = no
interfaces = {ip}/32
kernel change notify = yes
large readwrite = yes
lm announce = no
load printers = no
log file = /dev/null
logging =
log level = 0
max log size = 0
max smbd processes = 256
multicast dns register = no
name resolve order = host
ntlm auth = ntlmv2-only
nt pipe support = no
nt status support = yes
obey pam restrictions = no
pam password change = no
passdb backend = tdbsam
passdb expand explicit = no
passwd chat debug = no
read raw = yes
realm = vm.{name}.com
registry shares = no
require strong key = yes
reset on zero vc = no
security = user
server role = standalone server
server services = nbt rpc s3fs smb
server signing = auto
server smb transports = tcp, nbt
server string = VM-{name_upper}
smb3 directory leases = auto
smb ports = 445 139
time server = no
unix charset = UTF8
unix extensions = yes
use mmap = yes
usershare allow guests = no
usershare max shares = 0
utmp = no
wins proxy = no
wins support = no
workgroup = VM-{name_upper}
write raw = yes

[User]
access based share enum = no
acl allow execute always = no
acl group control = no
acl group control = no
acl map full control = yes
administrative share = no
afs share = no
available = yes
browseable = yes
case sensitive = yes
comment = Home Directories
create mask = 0740
csc policy = disable
delete readonly = no
delete veto files = no
directory mask = 0750
dont descend = /bin, /boot, /dev, /etc, /lib, /lib64, /mnt, /opt, /proc, /root, /run, /sbin, /srv, /sys, /tmp, /usr, /var
dos filemode = no
dos filetime resolution = no
dos filetimes = yes
durable handles = yes
ea support = no
fake directory create times = no
fake oplocks = no
follow symlinks = yes
force create mode = 0000
force directory mode = 0000
force unknown acl user = no
fstype = NTFS
guest ok = no
hide dot files = yes
hide files =
hide special files = no
hide unreadable = no
hide unwriteable files = no
honor change notify privilege = no
hosts allow = {network} 127.0.0.1/32
inherit acls = no
inherit owner = no
inherit permissions = no
invalid users = root
kernel oplocks = no
kernel share modes = no
level2 oplocks = yes
locking = yes
mangled names = yes
map acl inherit = no
map archive = no
map hidden = no
map readonly = yes
map system = no
max connections = 0
max print jobs = 0
nt acl support = yes
oplocks = yes
path = /home
posix locking = no
preserve case = yes
printable = no
read only = no
root preexec close = no
server smb encrypt = disabled
store dos attributes = no
strict allocate = no
strict locking = no
strict sync = no
sync always = no
use client driver = no
use sendfile = yes
veto files =
veto oplock files =
wide links = no
writable = yes

[UserRo]
copy = User
comment = Home Directories Read Only
read only = yes
writable = no
"""  # noqa: E501

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

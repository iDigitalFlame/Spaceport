#!/usr/bin/dash
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
## Faillock Configuration
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

if ! [ "$USER" = "root" ]; then
    echo "Error: root is required!"
    exit 1
fi

FILE_HASH="4c5e3222b401ab5dd72bd9efbdc174eb"

# Only replace this file if it does not exist or match our hash.
if ! [ -f "/etc/security/faillock.conf" ] || ! [ "$(md5sum "/etc/security/faillock.conf" | awk '{print $1}')" = "$FILE_HASH" ]; then
    echo 'Updating "/etc/security/faillock.conf"..'
    cat<<EOF>"/etc/security/faillock.conf"
dir           = /var/run/faillock
deny          = 7
unlock_time   = 300
fail_interval = 600

audit
silent
no_log_info
local_users_only
EOF
fi

chown root:root "/etc/security/faillock.conf"
chmod 0444      "/etc/security/faillock.conf"
